import operator
from typing import Annotated, TypedDict, List, Any, Optional, Dict
import logging
from datetime import datetime
import json
import os
from dotenv import load_dotenv

from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import BaseTool
from langgraph.graph import StateGraph, END

from app.config import get_settings
from app.services.cosmos_db_handler import CosmosDBHandler
from app.services.cosmos_db_saver import CosmosDBSaver, JsonPlusSerializerCompat
from app.agents.tools import get_agent_tools

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

        self.agent_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant. {system_message}"),
            ("human", "{question}")
        ])

        # Place-holder, the compiled graph is set in async init
        self.graph = None

    async def init(self):
        """Async initialization to set up LangGraph."""
        self.graph = await self._create_agent_graph()
        logger.info("AgentExecutor async graph setup complete.")

    async def _create_agent_graph(self) -> Any:
        class AgentState(TypedDict):
            messages: Annotated[List[Any], operator.add]
            system_message: str
            user_id: str
            tool_call: Optional[Dict[str, Any]]
            tool_result: Optional[Any]
            tool_history: Annotated[List[Dict[str, Any]], operator.add]
            output: Optional[str]
            action_type: Optional[str]

        graph = StateGraph(AgentState)

        graph.add_node("brain_node", self._agent_node)
        graph.add_node("call_tool", self._call_tool_node)
        graph.add_node("formatter_node", self._formatter_node)
        graph.add_conditional_edges("formatter_node", self._should_continue, {
            "continue": "brain_node",
            "end": END
        })

        graph.add_edge("brain_node", "call_tool")
        graph.add_edge("call_tool", "formatter_node")
        graph.set_entry_point("brain_node")

        async with CosmosDBHandler.from_conn_info(
            database_name=self.settings.AZURE_COSMOS_DB_DATABASE,
            container_name=self.settings.AZURE_COSMOS_DB_CONTAINER
        ) as handler:
            checkpointer = CosmosDBSaver(handler, serde=JsonPlusSerializerCompat())
            
            return graph.compile(checkpointer=checkpointer)

    async def _agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_user_message = next(
            (msg.content for msg in reversed(messages) if isinstance(msg, HumanMessage)),
            None
        )

        if not last_user_message:
            return {**state, "output": "No question found.", "action_type": "answer"}

        prompt = self.agent_prompt.format_messages(
            system_message=state.get("system_message", "You're a helpful assistant."),
            conversation=messages,
            question=last_user_message
        )

        response = await self.llm_with_tools.ainvoke(prompt)

        if response.tool_calls:
            tool_call = response.tool_calls[0]
            return {
                **state,
                "agent_response": response.content,
                "tool_call": {"name": tool_call.name, "input": tool_call.args},
                "action_type": "tool"
            }
        else:
            return {
                **state,
                "output": response.content,
                "action_type": "answer"
            }

    async def _call_tool_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if state.get("action_type") != "tool":
            return state

        tool_call = state.get("tool_call")
        tool_name = tool_call["name"]
        tool_input = tool_call["input"]

        chosen_tool = next((tool for tool in self.tools if tool.name == tool_name), None)
        if not chosen_tool:
            return {
                **state,
                "output": f"Tool '{tool_name}' not found.",
                "action_type": "answer"
            }

        try:
            result = await chosen_tool.ainvoke(tool_input)
            return {
                **state,
                "tool_result": result,
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"Tool '{tool_name}' executed. Result: {result}")
                ],
                "tool_history": state.get("tool_history", []) + [{
                    "tool": tool_name, "input": tool_input, "result": result
                }]
            }
        except Exception as e:
            return {
                **state,
                "tool_result": str(e),
                "messages": state.get("messages", []) + [
                    AIMessage(content=f"Tool '{tool_name}' failed: {str(e)}")
                ],
                "tool_history": state.get("tool_history", []) + [{
                    "tool": tool_name, "input": tool_input, "error": str(e)
                }]
            }

    async def _formatter_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state  # Simply forward state to the conditional edge

    def _should_continue(self, state: Dict[str, Any]) -> str:
        if state.get("action_type") == "tool" and "tool_result" in state:
            return "continue"
        return "end"

    async def ainvoke(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        if not self.graph:
            raise RuntimeError("Graph not initialized. Call await executor.init() before ainvoke().")

        start_time = datetime.now()

       
        state = {
            "messages": input_state.get("messages", []),
            "system_message": input_state.get("system_message", ""),
            "user_id": input_state.get("user_id", "unknown"),
            "tool_history": [],
            "output": None,
            "tool_call": None,
            "tool_result": None,
            "action_type": None
        }

        config = {
            "configurable": {
                "thread_id": input_state.get("thread_id", "default_thread"),
                "session_id": input_state.get("session_id", "default_session")
            }
        }

        final_state = await self.graph.ainvoke(state,config=config)
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        output = final_state.get("output")
        if not output and final_state.get("messages"):
            last = final_state["messages"][-1]
            output = last.content if isinstance(last, AIMessage) else "Unable to process."

        return {
            "output": output,
            "tool_history": final_state.get("tool_history", []),
            "execution_time_ms": execution_time_ms,
            "messages": final_state.get("messages", [])
        }


# Usage
_executor: Optional[AgentExecutor] = None

async def get_agent_executor() -> AgentExecutor:
    global _executor
    if _executor is None:
        _executor = AgentExecutor()
        await _executor.init()
    return _executor
