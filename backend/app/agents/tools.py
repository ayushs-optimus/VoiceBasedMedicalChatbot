import os
import logging
import requests
import json
from typing import List, Optional, Type, Any, Callable
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage,BaseMessage
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field
from applicationinsights import TelemetryClient
from pydantic import SecretStr
from app.config import get_settings
from app.services.ai_search_reteriver import get_patient_data
from app.services.telemetry import get_telemetry_client
from app.services.cosmos_db_handler import CosmosClientSingleton
from azure.cosmos import PartitionKey
from app.services.utils import generate_filter_query, get_message_type_and_content
from app.services.prompts import filter_query_prompt
logger = logging.getLogger(__name__)
telemetry_client = get_telemetry_client()

setting = get_settings()

### === Tool Input Schemas === ###


class ChatHistoryInput(BaseModel):
    messages: list = Field(description="List of chat message history")

class PatientIdSearchInput(BaseModel):
    query: str = Field(description="Free-text medical query used to search patients by description embedding")
    llm: Any 

    
class PatientDataSearchInput(BaseModel):
    query: str = Field(description="Free-text medical query used to search patients by description embedding")
    llm: Any
    patient_id : Optional[List[str]] = Field(default_factory=list, description="List of patient IDs to filter the search results")
    user_roles: Optional[List[str]] = Field(default_factory=list, description="Roles of the user making the request")
    
### === Tool Implementations === ###


class ChatHistoryTool(BaseTool):
    name: str = "chat_history_tool"
    description: str = "Tool to store chat history using Azure Cosmos DB"
    args_schema: Type[BaseModel] = ChatHistoryInput
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    query: Optional[str] = None
    database_name: str = setting.AZURE_COSMOS_DB_DATABASE
    container_name: str = setting.AZURE_COSMOS_DB_CHAT_HISTORY_CONTAINER

    async def store_chat_history(self, messages) -> str:
        try:
            print("chat history tool called", messages)
            async_client = CosmosClientSingleton.get_instance()
            database = await async_client.create_database_if_not_exists(self.database_name)
            container = await database.create_container_if_not_exists(id=self.container_name,partition_key= PartitionKey(path="/id"))
            

            query = "SELECT * FROM c WHERE c.id = @id AND c.user_id = @user_id"
            query_params = [
                {"name": "@user_id", "value": self.user_id},
                {"name": "@id", "value": f"{self.user_id}-{self.session_id}"}
            ]

            result = [item async for item in container.query_items(query=query, parameters=query_params)]
            documentFetched = result[0] if result else None
            data = list(documentFetched.get("data")) if documentFetched else []

            messageList = []
            for msg in messages:
                msg_type, msg_content = get_message_type_and_content(msg)
                if msg_content:
                    messageList.append({
                        "message": msg_content,
                        "type": msg_type
                    })


            data.append({
                "messages": messageList
            })
            await container.upsert_item({
                "id": f"{self.user_id}-{self.session_id}",
                "user_id": self.user_id,
                "session_id": self.session_id,
                "data": data
            })

            return "Chat history stored successfully."

        except Exception as ex:
            logger.exception(f"Error while storing chat history: {ex}")
            return "Error storing chat history."

    async def _arun(self, messages,
                    run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return await self.store_chat_history(messages)

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("ChatHistoryTool only supports async usage")

class PatientIdSearchTool(BaseTool):
    name: str = "PatientIdSearchTool"
    description: str = "This tool is called to search for a patient_id based on a user specified query. It uses Azure AI Search to find the most relevant patient_id based on the description embedding. call only when there's user query"
    args_schema: Type[BaseModel] = PatientIdSearchInput  

    async def search_patient_id(self, query: str) -> List[str]:
        try:
            print(f"Query: {query}")
            headers = {
                'Content-Type': 'application/json',
                'api-key': setting.AZURE_SEARCH_KEY
            }
            params = {
                'api-version': setting.AZURE_SEARCH_API_VERSION
            }

            search_payload = {
                "search": query,
                "top": 1,  # ✅ Get only top 5 results
                "count": True,
                "vectorQueries": [
                    {
                        "kind": "text",
                        "text": query,
                        "fields": "description_vector"
                    }
                ],
                "queryType": "semantic",
                "semanticConfiguration": "default-semantic-config",
                "captions": "extractive",
                "answers": "extractive|count-3",
                "queryLanguage": "en-us"
            }

            url = f"{setting.AZURE_SEARCH_ENDPOINT}/indexes/{setting.AZURE_SEARCH_INDEX_1}/docs/search"
            resp = requests.post(url, data=json.dumps(search_payload), headers=headers, params=params)
            resp.raise_for_status()  # Ensure exception is raised for HTTP errors

            search_results = resp.json()
            results = search_results.get("value", [])
            # print(f"Search results: {json.dumps(results, indent=2)}")
            # ✅ Filter by score threshold
            re_ranker_score = 1.5
            filtered_results = [
                r for r in results if r.get("@search.rerankerScore", 0) >= re_ranker_score
            ]

            # ✅ Clean output for printing
            cleaned_results = [
                {k: v for k, v in r.items() if k != "description_vector"}
                for r in filtered_results
            ]
            # print(f"Search results: {json.dumps(cleaned_results, indent=2)}")

            # ✅ Extract unique patient IDs
            patient_ids = list({r["patient_id"] for r in filtered_results if "patient_id" in r})

            return patient_ids if patient_ids else ["Patient not found."]
        
        except Exception as ex:
            logger.exception(f"Error during patient search: {ex}")
            return ["Error searching for patient."]
    
    async def _arun(
        self, query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> List[str]:
        patient_id = await self.search_patient_id(query)
        return patient_id

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("This tool only supports async usage.")
    
class PatientDataSearchTool(BaseTool):
    name: str = "PatientDataSearchTool"
    description: str = "This tool is called to fetch patient data based on the patient_id or other criteria. it will always be called after generating filter query from GenerateFilterQueryTool."
    args_schema: Type[BaseModel] = PatientDataSearchInput  
    llm: Optional[Any] = None
    user_roles: Optional[List[str]] = Field(default_factory=list, description="Roles of the user making the request")
    async def _arun(
        self,
        query: str,patient_id: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        try:
            filter_query = await generate_filter_query(
                query=query,
                patient_id=patient_id,
                roles=self.user_roles,
                llm=self.llm
            )
            patient_data = await get_patient_data(query=query,filter_query=filter_query)
            print(f"Patient data: {patient_data}")
            return patient_data
        except Exception as e:
            logger.exception(f"Error in patient data search tool: {e}")
            telemetry_client.track_exception()
            return f"Error fetching patient data: {str(e)}"

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("PatientDataSearchTool only supports async usage")
### === Tool Registry === ###


def  get_agent_tools(llm,user_id,session_id,query,user_roles) -> List[BaseTool]:
    patient_tool = PatientDataSearchTool()
    patient_tool.llm = llm  # Inject LLM manually
    patient_tool.user_roles = user_roles  # Inject user roles
    chat_history_tool = ChatHistoryTool()
    chat_history_tool.user_id = user_id
    chat_history_tool.session_id = session_id
    chat_history_tool.query = query

    return [
        chat_history_tool,
        PatientIdSearchTool(),
        patient_tool  # Now has LLM access
    ]

