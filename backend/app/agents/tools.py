import os
import logging
import requests
import json
from typing import List, Optional, Type, Any, Callable
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.pydantic_v1 import BaseModel, Field
from applicationinsights import TelemetryClient
from pydantic import SecretStr
from app.config import get_settings
from app.core.search import get_search_client
from app.services.ai_search_reteriver import get_patient_data
from app.services.telemetry import get_telemetry_client
from app.services.cosmos_db_handler import CosmosClientSingleton
from azure.cosmos import PartitionKey
from app.services.utils import get_message_type_and_content
logger = logging.getLogger(__name__)
telemetry_client = get_telemetry_client()

setting = get_settings()

### === Tool Input Schemas === ###

class SearchToolInput(BaseModel):
    query: str = Field(description="The search query")
    filter: Optional[str] = Field(None, description="Optional filter for search")
    top: int = Field(5, description="Number of results to return")

class CalculatorInput(BaseModel):
    expression: str = Field(description="The mathematical expression to evaluate")

class ChatHistoryInput(BaseModel):
    messages: list = Field(description="List of chat message history")

class GenerateFilterQueryInput(BaseModel):
    query: str
    roles: List[str]
    llm: Any 

class PatientSearchInput(BaseModel):
    query: str = Field(description="Free-text medical query used to search patients by description embedding")

### === Tool Implementations === ###

class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = "Tool to search documents using Azure AI Search"
    args_schema: Type[BaseModel] = SearchToolInput

    async def _arun(self, query: str, filter: Optional[str] = None, top: int = 5,
                    run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            telemetry_client.track_event("AgentToolUsed", {"tool": "search", "query": query})
            search_client = get_search_client()
            results = await search_client.search(query=query, filter=filter, top=top)

            if not results:
                return "No results found for the query."

            formatted_results = []
            for i, result in enumerate(results):
                title = result.get("title", f"Document {i+1}")
                content = result.get("content", "")
                content = content[:200] + "..." if len(content) > 200 else content
                source = result.get("source", "Unknown")
                formatted_results.append(f"[{i+1}] {title} (Source: {source})\n{content}\n")

            return "Search Results:\n\n" + "\n".join(formatted_results)

        except Exception as e:
            logger.exception(f"Error in search tool: {e}")
            telemetry_client.track_exception()
            return f"Error performing search: {str(e)}"

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("SearchTool does not support synchronous execution")


class CalculatorTool(BaseTool):
    name: str = "calculator_tool"
    description: str = "Tool to evaluate mathematical expressions"
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, expression: str,
             run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            telemetry_client.track_event("AgentToolUsed", {"tool": "calculator", "expression": expression})
            result = eval(expression)
            return f"The result of {expression} is {result}"
        except Exception as e:
            logger.exception(f"Error in calculator tool: {e}")
            telemetry_client.track_exception()
            return f"Error evaluating expression: {str(e)}"

    async def _arun(self, *args, **kwargs) -> str:
        raise NotImplementedError("CalculatorTool does not support asynchronous execution")


class ChatHistoryTool(BaseTool):
    name: str = "chat_history_tool"
    description: str = "Tool to store chat history using Azure Cosmos DB"
    args_schema: Type[BaseModel] = ChatHistoryInput

    database_name: str = setting.AZURE_COSMOS_DB_DATABASE
    container_name: str = setting.AZURE_COSMOS_DB_CHAT_HISTORY_CONTAINER

    async def store_chat_history(self, messages) -> str:
        try:
            async_client = CosmosClientSingleton.get_instance()
            database = await async_client.create_database_if_not_exists(self.database_name)

            container = await database.create_container_if_not_exists(id=self.container_name,partition_key= PartitionKey(path="/id"))
            user_id = "sfsdf"
            session_id = "sdfkjds"

            query = "SELECT * FROM c WHERE c.id = @id AND c.user_id = @user_id"
            query_params = [
                {"name": "@user_id", "value": user_id},
                {"name": "@id", "value": f"{user_id}-{session_id}"}
            ]

            result = [item async for item in container.query_items(query=query, parameters=query_params)]
            documentFetched = result[0] if result else None
            data = list(documentFetched.get("data")) if documentFetched else []

            messageList = [{
                "message": "sdfkljdsl",
                "type": "Human"
            }]

            msg_type, msg_content = get_message_type_and_content(messages[-1])
            if msg_type == "AI" and msg_content:
                messageList.append({
                    "message": msg_content,
                    "type": "AI"
                })

            data.append({
                "messages": messageList,
                "feedback": -1,
                "promptId": 239
            })

            await container.upsert_item({
                "id": f"{user_id}-{session_id}",
                "user_id": user_id,
                "session_id": session_id,
                "re_ranker_value": float(os.environ.get("AZURE_SEARCH_RE_RANKER_VALUE")),
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

class GenerateFilterQueryTool(BaseTool):
    name: str = "generate_filter_query_tool"
    description: str = "it will always be called Converts a user query into an Azure Search filter string using LLM and allowed roles based on patient id or any other information"
    args_schema: Type[BaseModel] = GenerateFilterQueryInput

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("Use async execution")

    async def _arun(self, query: str, roles: List[str], llm: Any) -> str:
        roles_str = ', '.join([f"'{r}'" for r in roles])
        
        prompt = f"""
You are an expert in Azure Cognitive Search.

Your job is to convert a natural language query into an OData-compliant filter expression.

Allowed filterable fields:
- patient_id (string)
- department_name (string)
- department_value (string)
- access (Collection of strings)

Valid roles for access checks are: [{roles_str}]

Only output a valid filter expression string.
Use this format for roles:
    access/any(a: a eq 'role1' or a eq 'role2')

Now convert the user query into a filter:

User query:
\"\"\"{query}\"\"\"

Filter query:
"""
        try:
            response = await llm.ainvoke(prompt)
            print("printing response" ,response)
            return response.strip()
        except Exception as e:
            return f"Error generating filter: {str(e)}"
        
class PatientIdSearchTool(BaseTool):
    name: str = "patient_search_tool"
    description: str = "This tool is called to search for a patient_id based on a user specified query. It uses Azure AI Search to find the most relevant patient_id based on the description embedding. call only when there's user query"
    args_schema: Type[BaseModel] = PatientSearchInput  

    async def search_patient_id(self, query: str) -> str:
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
                "queryType": "semantic",
                "semanticConfiguration": "default-semantic-config", 
                "search": query,
                "select": "*",
                "top": 2,
                "count": True,
                "captions": "extractive", 
                "answers": "extractive"
            }

            url = f"{setting.AZURE_SEARCH_ENDPOINT}/indexes/{setting.AZURE_SEARCH_INDEX_1}/docs/search"
            resp = requests.post(url, data=json.dumps(search_payload), headers=headers, params=params)
            search_results = resp.json()
            results = search_results.get("value", [])
            print(f"Search results: {results}")
            if not results:
                return "No results found."

            for i, r in enumerate(results):
                print(f"[{i}] patient_id={r.get('patient_id')} reranker_score={r.get('@search.reranker_score')}")

            if len(results) >= 2:
                score1 = results[0].get('@search.reranker_score', 0)
                score2 = results[1].get('@search.reranker_score', 0)
                
                return json.dumps({
                    "status": "no_results",
                    "message": "No relevant patient found for the query."
                }, indent=2)
                
            return results[0].get("patient_id", "Patient ID not found in top result.")
            if abs(score1 - score2) < 0.1:  # tune threshold based on testing
                return json.dumps({
                    "status": "ambiguous",
                    "candidates": [
                        {
                            "patient_id": results[0].get("patient_id"),
                            "description": results[0].get("description"),
                            "reranker_score": score1
                        },
                        {
                            "patient_id": results[1].get("patient_id"),
                            "description": results[1].get("description"),
                            "reranker_score": score2
                        }
                    ],
                    "message": "Multiple patients have similar relevance. Please clarify."
                }, indent=2)
            if(score1 <1 and score2 < 1):
                return json.dumps({
                    "status": "low_relevance",
                    "message": "The search results have low relevance scores. Please refine your query."
                }, indent=2)
            if len(results) ==0:
                return json.dumps({
                    "status": "no_results",
                    "message": "No relevant patient found for the query."
                }, indent=2)
        except Exception as ex:
            logger.exception(f"Error during patient search: {ex}")
            return "Error searching for patient."
        
    async def _arun(
        self, query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        patient_id = await self.search_patient_id(query)
        return patient_id

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("This tool only supports async usage.")
    
class PatientDataSearchTool(BaseTool):
    name: str = "patient_data_search_tool"
    description: str = "This tool is called to fetch patient data based on the patient_id or other criteria. it will always be called"
    args_schema: Type[BaseModel] = PatientSearchInput  

    async def _arun(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            patient_data = await get_patient_data(query)
            return patient_data
        except Exception as e:
            logger.exception(f"Error in patient data search tool: {e}")
            telemetry_client.track_exception()
            return f"Error fetching patient data: {str(e)}"
        
    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("PatientDataSearchTool only supports async usage")
### === Tool Registry === ###

def get_agent_tools() -> List[BaseTool]:
    return [
        SearchTool(),
        CalculatorTool(),
        ChatHistoryTool(),
        PatientIdSearchTool(),
        GenerateFilterQueryTool(),
        PatientDataSearchTool()
    ]
