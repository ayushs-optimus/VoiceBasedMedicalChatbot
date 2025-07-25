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
from app.services.prompts import query_identification_prompt, agent_prompt, agent_node_human_prompt
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
        self.user_roles = None

        self.tools: List[BaseTool] = get_agent_tools(self.llm, self.user_id, self.session_id, self.query,self.user_roles)
        # self.llm_with_tools = self.llm.bind_tools(self.tools)  # Removed as unused

        # Create tool node for executing tools
        self.tool_node = ToolNode(self.tools)

        self.agent_prompt = ChatPromptTemplate.from_messages([
            ("system", agent_prompt),
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

    async def _create_agent_graph(self) -> Any:
        """Create a LangGraph with the extended CustomMessagesState."""
        graph = StateGraph(CustomMessagesState)

        # Add nodes
        graph.add_node("query_identification", query_identification_node(self))
        graph.add_node("tools", custom_tool_node(self))
        graph.add_node("store_chat", store_chat_node(self))
        graph.add_node("agent", agent_node(self))

        # Set entry point to query identification first
        graph.set_entry_point("query_identification")

        # After query identification, always go to the agent
        graph.add_conditional_edges(
            "query_identification",
            should_continue(self),
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
        self.user_roles = input_state.get("user_roles", [])
        self.tools: List[BaseTool] = get_agent_tools(self.llm, self.user_id, self.session_id, self.query,self.user_roles)
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