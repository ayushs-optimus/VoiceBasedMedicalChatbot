import operator
from typing import Annotated, AsyncGenerator, List, Any, Literal, Optional, Dict
import logging
from datetime import datetime
import os

from pydantic import BaseModel
from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode
from app.agents.tools import PatientDataSearchInput 
from app.config import get_settings
from app.services.cosmos_db_handler import CosmosDBHandler
from app.services.cosmos_db_saver import CosmosDBSaver, JsonPlusSerializerCompat
from app.agents.tools import get_agent_tools
from app.services.prompts import query_identification_prompt
import json
load_dotenv()
logger = logging.getLogger(__name__)


class CustomMessagesState(BaseModel):
    messages: Optional[List[BaseMessage]] = []
    query_type: Optional[Literal["user_specific", "generic"]] = None
    filter_query: Optional[str] = None
    patient_id: Optional[List[str]] = None
    query: Optional[str] = None
    next_action: Optional[str] = None

    def add_message(self, message: BaseMessage):
        """Helper method to add a single message to the messages list"""
        if self.messages is None:
            self.messages = []
        self.messages.append(message)
    
    def add_messages(self, messages: List[BaseMessage]):
        """Helper method to add multiple messages to the messages list"""
        if self.messages is None:
            self.messages = []
        self.messages.extend(messages)
    
    def update_state(self, **kwargs) -> 'CustomMessagesState':
        """Helper method to create a new state with updated fields while preserving existing messages"""
        current_messages = self.messages or []
        new_messages = kwargs.pop('messages', [])
        
        # Combine existing messages with new ones
        all_messages = current_messages + (new_messages if isinstance(new_messages, list) else [new_messages] if new_messages else [])
        
        return CustomMessagesState(
            messages=all_messages,
            query_type=kwargs.get('query_type', self.query_type),
            filter_query=kwargs.get('filter_query', self.filter_query),
            patient_id=kwargs.get('patient_id', self.patient_id),
            query=kwargs.get('query', self.query),
            next_action=kwargs.get('next_action', self.next_action)
        )


class AgentExecutor:
    def __init__(self):
        self.settings = get_settings()

        self.llm = AzureChatOpenAI(
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            openai_api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("Azure_OPENAI_ENDPOINT"),
            temperature=0.7
        )
        self.user_id = None
        self.session_id = None
        self.query = None

        self.tools: List[BaseTool] = get_agent_tools(self.llm, self.user_id, self.session_id, self.query)
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create tool node for executing tools
        self.tool_node = ToolNode(self.tools)

        self.agent_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Use the available tools when needed to help the user."),
            ("placeholder", "{messages}")
        ])

        # The compiled graph is set in async init
        self.graph = None
        
    async def init(self):
        """Async initialization to set up LangGraph."""
        self.graph = await self._create_agent_graph()
        self.user_id = None
        self.session_id = None
        self.query = None
        logger.info("AgentExecutor async graph setup complete.")

    async def _query_identification_node(self, state: CustomMessagesState) -> CustomMessagesState:
        """Node to classify the query and extract patient ID using the LLM."""
        query = state.query
        if not query:
            return state.update_state(
                messages=[AIMessage(content="No query provided.")],
                query_type=None,
                patient_id=None,
                next_action="reject"
            )

        user_embed_query = query_identification_prompt + f"\n\nUser Query: {query}"
        try:
            llm_response = await self.llm.ainvoke(user_embed_query)
            parsed = json.loads(llm_response.content.strip())

            is_patient_related = parsed.get("is_patient_related", False)
            query_type = parsed.get("query_type")
            
            # Safely parse and clean the patient_id list
            raw_patient_id = parsed.get("patient_id", [])
            if not isinstance(raw_patient_id, list):
                raw_patient_id = []
            patient_id = [pid for pid in raw_patient_id if isinstance(pid, str) and pid.strip()]

            next_action = parsed.get("next_action", "reject")
            response = parsed.get("response", "No response provided.")

            return state.update_state(
                messages=[AIMessage(content=response)],
                query_type=query_type,
                patient_id=patient_id,
                next_action=next_action
            )

        except Exception as e:
            # Fallback logic on LLM failure
            import re
            patient_ids = re.findall(r"\b\d{3,}\b", query)
            query_type = "user_specific" if patient_ids else "generic"
            next_action = "route_to_tool_node" if patient_ids else "reject"

            return state.update_state(
                messages=[
                    AIMessage(content="Failed to parse LLM response. Fallback logic used."),
                    AIMessage(content=f"Query classified as `{query_type}`."),
                    AIMessage(content=f"Detected patient IDs: `{', '.join(patient_ids) if patient_ids else 'None'}`")
                ],
                query_type=query_type,
                patient_id=patient_ids,
                next_action=next_action
            )

    async def _custom_tool_node(self, state: CustomMessagesState) -> CustomMessagesState:
        """Custom tool node that routes to specific tools based on query_type."""
        
        if not self.tools:
            raise ValueError("No tools available for the agent.")
        
        tool_messages = []
        
        if state.query_type == "user_specific":
            # First, look for and execute PatientIdSearchTool
            patient_id_tool = next((tool for tool in self.tools if "PatientIdSearchTool" in tool.name or "patient_id" in tool.name.lower()), None)
            # print(f"Looking for PatientIdSearchTool for user_specific query")
            
            if patient_id_tool:
                try:
                    # Prepare tool input for PatientIdSearchTool
                    tool_input = {
                        "query": state.query or self.query,
                    }
                    # Execute PatientIdSearchTool
                    # print(f"Executing PatientIdSearchTool with input: {tool_input}")
                    patient_id_result = await patient_id_tool.ainvoke(tool_input)
                    # print(f"PatientIdSearchTool result: {patient_id_result}")
                    
                    # Extract patient IDs from the result and update state
                    updated_patient_ids = state.patient_id or []
                    try:
                        if isinstance(patient_id_result, list):
                            for pid in patient_id_result:
                                pid_str = str(pid).strip()
                                if pid_str and pid_str not in updated_patient_ids:
                                    updated_patient_ids.append(pid_str)
                                    print(f"✅ Added patient ID: {pid_str}")
                            print(f"📌 Final updated_patient_ids: {updated_patient_ids}")
                        else:
                            print(f"⚠️ patient_id_result is not a list. Got: {type(patient_id_result)}")

                    except Exception as e:
                        print(f"🔥 Error updating patient IDs: {e}")

                    # Update the state with new patient IDs
                    state = state.update_state(patient_id=updated_patient_ids)
                    
                    patient_id_message = ToolMessage(
                        content=str(patient_id_result),
                        tool_call_id=f"{patient_id_tool.name}_{datetime.now().timestamp()}",
                        name=patient_id_tool.name
                    )
                    tool_messages.append(patient_id_message)
                    print(f"PatientIdSearchTool executed successfully")
                    
                except Exception as e:
                    print(f"Error executing PatientIdSearchTool: {e}")
                    error_message = AIMessage(content=f"Error executing {patient_id_tool.name}: {str(e)}")
                    tool_messages.append(error_message)
            
            # Then, look for and execute PatientDataSearchTool
            patient_data_tool = next((tool for tool in self.tools if "PatientDataSearchTool" in tool.name or "patient_data" in tool.name.lower()), None)
            print(f"Looking for PatientDataSearchTool after PatientIdSearchTool")
            
            if patient_data_tool:
                try:
                    tool_input = {
                        "query": state.query or self.query,
                        "patient_id": state.patient_id or []
                    }
                    print("Custom state", json.dumps(state.model_dump(), indent=2))

                    # ✅ Convert dict to Pydantic object
                    validated_input = PatientDataSearchInput(**tool_input)
                    print(f"Executing PatientDataSearchTool with input: {validated_input}")
                    # ✅ Execute tool
                    patient_data_result = await patient_data_tool.ainvoke(tool_input)

                    # ✅ Wrap result in ToolMessage
                    patient_data_message = ToolMessage(
                        content=str(patient_data_result),
                        tool_call_id=f"{patient_data_tool.name}_{datetime.now().timestamp()}",
                        name=patient_data_tool.name
                    )
                    tool_messages.append(patient_data_message)
                    print(f"PatientDataSearchTool executed successfully")
                except Exception as e:
                    print(f"Error executing PatientDataSearchTool: {e}")
                    error_message = AIMessage(content=f"Error executing {patient_data_tool.name}: {str(e)}")
                    tool_messages.append(error_message)
# Check if any tools were found and executed
            if not tool_messages:
                print(f"No appropriate tools found for user_specific query")
                print(f"Available tools: {[tool.name for tool in self.tools]}")
                return state.update_state(
                    messages=[AIMessage(content=f"No PatientIdSearchTool or PatientDataSearchTool found. Available tools: {', '.join([tool.name for tool in self.tools])}")],
                    next_action="continue"
                )
                
        else:
            print("Generic query detected, looking for PatientDataSearchTool...")
            # For generic queries, only use PatientDataSearchTool
            patient_data_tool = next((tool for tool in self.tools if "PatientDataSearchTool" in tool.name or "patient_data" in tool.name.lower()), None)
            print(f"Looking for PatientDataSearchTool for generic query")
            
            if patient_data_tool is None:
                print(f"No PatientDataSearchTool found for generic query")
                print(f"Available tools: {[tool.name for tool in self.tools]}")
                return state.update_state(
                    messages=[AIMessage(content=f"No PatientDataSearchTool found for generic query. Available tools: {', '.join([tool.name for tool in self.tools])}")],
                    next_action="continue"
                )
            
            try:
                # Prepare tool input for PatientDataSearchTool
                tool_input = {
                    "query": state.query or self.query,
                }
                
                # Execute PatientDataSearchTool
                validated_input = PatientDataSearchInput(**tool_input)

                    # ✅ Execute tool
                patient_data_result = await patient_data_tool.ainvoke(tool_input)
                
                # Create ToolMessage for PatientDataSearchTool result
                patient_data_message = ToolMessage(
                    content=str(patient_data_result),
                    tool_call_id=f"{patient_data_tool.name}_{datetime.now().timestamp()}",
                    name=patient_data_tool.name
                )
                tool_messages.append(patient_data_message)
                print(f"PatientDataSearchTool executed successfully for generic query")
                
            except Exception as e:
                print(f"Error executing PatientDataSearchTool for generic query: {e}")
                error_message = AIMessage(content=f"Error executing {patient_data_tool.name}: {str(e)}")
                tool_messages.append(error_message)
        
        return state.update_state(
            messages=tool_messages,
            next_action="continue"
        )

    async def _create_agent_graph(self) -> Any:
        """Create a LangGraph with the extended CustomMessagesState."""
        graph = StateGraph(CustomMessagesState)

        # Add nodes
        graph.add_node("query_identification", self._query_identification_node)
        graph.add_node("tools", self._custom_tool_node)
        graph.add_node("store_chat", self._store_chat_node)
        graph.add_node("agent", self._agent_node)

        # Set entry point to query identification first
        graph.set_entry_point("query_identification")

        # After query identification, always go to the agent
        graph.add_conditional_edges(
            "query_identification",
            self._should_continue,
            {
                "tools": "tools",
                "store_chat": "agent"
            }
        )

        graph.add_edge("tools", "agent")
        graph.add_edge("agent", "store_chat")
        # Final node
        graph.add_edge("store_chat", END)

        return graph

    async def _agent_node(self, state: CustomMessagesState) -> CustomMessagesState:
        # print("Agent node processing messages...", state)
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful ai assistant, please do no use your internal knowledge, "
            "responsible for generating response based on the input"),
            ("human", """
            UserQuery:{UserQuery}
    Query: {query}
    """)
        ])

        messages = (state.messages or [])[-10:]  # Get only the last 10 messages
        # print(f"Last 10 messages in agent node: {messages}")

        response = await self.llm.ainvoke(
            prompt_template.format_messages(UserQuery=state.query, query=messages)
        )

        # Return updated state with new message
        return state.update_state(
            messages=[AIMessage(content=response.content)]
        )

    def _should_continue(self, state: CustomMessagesState) -> str:
        print("Checking if the last message requires tool calls or chat storage...")
        # print(f"Current state: {state}")
        next_action = state.next_action
        # print(f"Next action: {next_action}")
        if next_action == "reject":
            return "store_chat"
        else:
            print("Continuing to tools node for further processing.")
            # print("custom state", json.dumps(state.model_dump(), indent=2))
            return "tools"
        
    async def _store_chat_node(self, state: CustomMessagesState) -> CustomMessagesState:
        try:
            # print("Storing chat history...", json.dumps(state.model_dump(), indent=2))
            chat_tool = next((tool for tool in self.tools if tool.name == "chat_history_tool"), None)
            if chat_tool is None:
                logger.warning("ChatHistoryTool not found.")
                return state

            messages = state.messages or []
            await chat_tool.ainvoke({
                "messages": messages,
                "user_id": self.user_id,
                "session_id": self.session_id
            })
            updated_state = state.update_state(
                messages=messages,
                query="",
                query_type=None,
                patient_id=None,
                next_action=""
            )
            logger.info("Chat history stored successfully.")
        except Exception as e:
            logger.exception(f"Failed to store chat history: {e}")

        # Return the current state without modification
        return updated_state
    
    async def get_compiled_graph(self):
        try:
            async with CosmosDBHandler.from_conn_info(
                database_name=self.settings.AZURE_COSMOS_DB_DATABASE,
                container_name=self.settings.AZURE_COSMOS_DB_CHECKPOINTER_CONTAINER
            ) as handler:
                checkpointer = CosmosDBSaver(handler, serde=JsonPlusSerializerCompat())
                return self.graph.compile(checkpointer=checkpointer)
        except Exception as e:
            logging.error(f"Failed to initialize CosmosDB checkpointing: {e}")
            return self.graph.compile()  # fallback: compile without checkpointing

    async def astream(self, input_state: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the agent execution step by step."""
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call await executor.init() before astream().")
        
        self.user_id = input_state.get("thread_id", "Unknown")
        self.session_id = input_state.get("session_id", "Unknown")
        self.query = input_state.get("query", "No query provided")

        self.tools: List[BaseTool] = get_agent_tools(self.llm, self.user_id, self.session_id, self.query)
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_node = ToolNode(self.tools)

        start_time = datetime.now()
        last_output = None
        current_node = None

        # 🌐 Compile graph (CosmosDB checkpointing handled separately)
        compiled_graph = await self.get_compiled_graph()

        config = {
            "configurable": {
                "thread_id": self.user_id,
                "session_id": self.session_id
            }
        }

        # Load existing conversation history from checkpointer
        try:
            existing_state = await compiled_graph.aget_state(config)
            existing_messages = existing_state.values.get("messages", []) if existing_state.values else []
            # print(f"Loaded {len(existing_messages)} existing messages from checkpoint")
        except Exception as e:
            # print(f"Could not load existing state: {e}")
            existing_messages = []

        # Add the new query to existing messages
        query = input_state.get("query", [])
        if isinstance(query, str):
            new_message = HumanMessage(content=query)
        elif isinstance(query, list) and len(query) > 0:
            new_message = query[0] if isinstance(query[0], BaseMessage) else HumanMessage(content=str(query[0]))
        else:
            new_message = HumanMessage(content=str(query))

        # Combine existing messages with new message
        all_messages = existing_messages + [new_message]

        state = {
            "messages": all_messages,
            "query": self.query
        }

        async for event in compiled_graph.astream_events(state, config=config, version="v2"):
            ev = event.get("event")
            data = event.get("data", {})
            meta_data = event.get("metadata", {})
            current_node = meta_data.get("langgraph_node", "Unknown")

            if ev == "on_chat_model_stream" and current_node == "agent":
                chunk = data.get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                    yield {
                        "output": chunk.content,
                        "execution_time_ms": execution_time_ms,
                        "node": "agent",
                        "type": "stream"
                    }

            elif ev == "on_node_end":
                node_name = event.get("name", "")
                output_data = data.get("output", {})

                if node_name == "query_identification":
                    if "messages" in output_data and output_data["messages"]:
                        for msg in output_data["messages"]:
                            if isinstance(msg, AIMessage) and msg.content and not msg.content.strip().startswith("{"):
                                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                                yield {
                                    "output": msg.content,
                                    "execution_time_ms": execution_time_ms,
                                    "node": node_name,
                                    "type": "complete_response"
                                }

                elif node_name == "agent":
                    execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                    yield {
                        "output": "",
                        "execution_time_ms": execution_time_ms,
                        "node": node_name,
                        "type": "agent_complete"
                    }

                elif node_name == "tools":
                    if "messages" in output_data and output_data["messages"]:
                        for msg in output_data["messages"]:
                            if isinstance(msg, ToolMessage) and msg.content:
                                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                                yield {
                                    "output": f"Tool executed: {msg.content}",
                                    "execution_time_ms": execution_time_ms,
                                    "node": node_name,
                                    "type": "tool_result"
                                }

                elif node_name == "store_chat":
                    execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                    yield {
                        "output": "",
                        "execution_time_ms": execution_time_ms,
                        "type": "complete",
                        "status": "success"
                    }


# Usage
_executor: Optional[AgentExecutor] = None

async def get_agent_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
        await _executor.init()
    return _executor