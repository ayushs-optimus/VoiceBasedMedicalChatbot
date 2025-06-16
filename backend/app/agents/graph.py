from typing import AsyncGenerator, List, Any, Optional, Dict
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode

from app.config import get_settings
from app.services.cosmos_db_handler import CosmosDBHandler
from app.services.cosmos_db_saver import CosmosDBSaver, JsonPlusSerializerCompat
from app.agents.tools import get_agent_tools
from app.services.prompts import tool_call_prompt
import asyncio
load_dotenv()
logger = logging.getLogger(__name__)


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

        self.tools: List[BaseTool] = get_agent_tools()
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create tool node for executing tools
        self.tool_node = ToolNode(self.tools)

        self.agent_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. Use the available tools when needed to help the user."),
            ("system", tool_call_prompt),
            ("placeholder", "{messages}")
        ])


        # The compiled graph is set in async init
        self.graph = None


    async def init(self):
        """Async initialization to set up LangGraph."""
        self.graph = await self._create_agent_graph()
        logger.info("AgentExecutor async graph setup complete.")

    async def _create_agent_graph(self) -> Any:
        """Create a simple agent graph with MessagesState only."""
        graph = StateGraph(MessagesState)

        # Add nodes
        graph.add_node("agent", self._agent_node)
        graph.add_node("tools", self.tool_node)
        graph.add_node("store_chat", self._store_chat_node)

        # Set entry point
        graph.set_entry_point("agent")

        # Add conditional edges
        graph.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                "store_chat": "store_chat"
            }
        )

        # Tools always go back to agent
        graph.add_edge("tools", "agent")
        
        # Store chat is the final step
        graph.add_edge("store_chat", END)

        return graph

    async def _agent_node(self, state: MessagesState) -> Dict[str, Any]:
        """Main agent node that processes messages and decides on actions."""
        print("Agent node processing messages...")
        
        messages = state["messages"]
        
        # Format messages for the prompt
        response = await self.llm_with_tools.ainvoke(
            self.agent_prompt.format_messages(messages=messages)
        )
        
        # Return the response as a new message
        return {"messages": [response]}

    def _should_continue(self, state: MessagesState) -> str:
        """Determine next action based on the last message."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, execute tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        else:
            # No tool calls, store chat and end
            return "store_chat"

    async def _store_chat_node(self, state: MessagesState) -> Dict[str, Any]:
        """Final node to persist chat history."""
        try:
            # Find ChatHistoryTool
            chat_tool = next((tool for tool in self.tools if tool.name == "chat_history_tool"), None)
            if chat_tool is None:
                logger.warning("ChatHistoryTool not found.")
                return {"messages": []}

            messages = state["messages"]
            
            # Store the conversation
            await chat_tool.ainvoke({
                "messages": messages
            })
            
            logger.info("Chat history stored successfully.")

        except Exception as e:
            logger.exception(f"Failed to store chat history: {e}")

        # Return empty messages to indicate completion
        return {"messages": []}

    async def astream(self, input_state: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream the agent execution step by step."""
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call await executor.init() before astream().")
        
        start_time = datetime.now()
        last_output = None

        async with CosmosDBHandler.from_conn_info(
            database_name=self.settings.AZURE_COSMOS_DB_DATABASE,
            container_name=self.settings.AZURE_COSMOS_DB_CHECKPOINTER_CONTAINER
        ) as handler:
            checkpointer = CosmosDBSaver(handler, serde=JsonPlusSerializerCompat())
            compiled_graph = self.graph.compile(checkpointer=checkpointer)

            query = input_state.get("query", [])
            if isinstance(query, str):
                initial_messages = [HumanMessage(content=query)]
            elif isinstance(query, list):
                initial_messages = query
            else:
                initial_messages = [HumanMessage(content=str(query))]

            state = {
                "messages": initial_messages
            }

            config = {
                "configurable": {
                    "thread_id": input_state.get("thread_id", "default_thread"),
                    "session_id": input_state.get("session_id", "default_session")
                }
            }
            async for event in compiled_graph.astream_events(state, config=config, version="v2"):
                ev = event.get("event")
                data = event.get("data", {})
                # print(f"Event received: {ev}, Data: {data}")

                # Only handle relevant events
                if ev not in {"on_chat_model_stream", "on_node_end"}:
                    continue

                messages = []
                if ev == "on_chat_model_stream":
                    chunk = data.get("chunk", {})
                    if isinstance(chunk, dict):
                        messages = chunk.get("messages", [])
                    elif hasattr(chunk, "content"):  # likely AIMessageChunk or similar
                        messages = [AIMessage(content=chunk.content)]
                    else:
                        messages = []


                output = None
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        output = msg.content
                        break

                if not output or output == last_output:
                    continue

                last_output = output

                # Extract tool output if present
                tool_history = [
                    {"tool": getattr(msg, "name", "unknown"), "result": msg.content}
                    for msg in messages if isinstance(msg, ToolMessage)
                ]

                execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                # print(f"Yielding output: {output}")
                yield {
                    "output": output,
                    "tool_history": tool_history,
                    "execution_time_ms": execution_time_ms,
                    "messages": messages,
                }


# Usage
_executor: Optional[AgentExecutor] = None

async def get_agent_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
        await _executor.init()
    return _executor