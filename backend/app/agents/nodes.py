import json
import logging
from datetime import datetime
from langchain_core.messages import AIMessage, ToolMessage
from app.services.prompts import query_identification_prompt, agent_prompt, agent_node_human_prompt
from langchain.prompts import ChatPromptTemplate
from app.agents.tools import PatientDataSearchInput

logger = logging.getLogger(__name__)

def query_identification_node(self):
    async def node(state):
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
    return node

def custom_tool_node(self):
    async def node(state):
        if not self.tools:
            raise ValueError("No tools available for the agent.")
        tool_messages = []
        if state.query_type == "user_specific":
            patient_id_tool = next((tool for tool in self.tools if "PatientIdSearchTool" in tool.name or "patient_id" in tool.name.lower()), None)
            if patient_id_tool:
                try:
                    tool_input = {
                        "query": state.query or self.query,
                    }
                    patient_id_result = await patient_id_tool.ainvoke(tool_input)
                    updated_patient_ids = state.patient_id or []
                    try:
                        if isinstance(patient_id_result, list):
                            for pid in patient_id_result:
                                pid_str = str(pid).strip()
                                if pid_str and pid_str not in updated_patient_ids:
                                    updated_patient_ids.append(pid_str)
                                    logger.info(f"✅ Added patient ID: {pid_str}")
                            logger.info(f"📌 Final updated_patient_ids: {updated_patient_ids}")
                        else:
                            logger.warning(f"⚠️ patient_id_result is not a list. Got: {type(patient_id_result)}")
                    except Exception as e:
                        logger.error(f"🔥 Error updating patient IDs: {e}")
                    state = state.update_state(patient_id=updated_patient_ids)
                    patient_id_message = ToolMessage(
                        content=str(patient_id_result),
                        tool_call_id=f"{patient_id_tool.name}_{datetime.now().timestamp()}",
                        name=patient_id_tool.name
                    )
                    tool_messages.append(patient_id_message)
                    logger.info("PatientIdSearchTool executed successfully")
                except Exception as e:
                    logger.error(f"Error executing PatientIdSearchTool: {e}")
                    error_message = AIMessage(content=f"Error executing {patient_id_tool.name}: {str(e)}")
                    tool_messages.append(error_message)
            patient_data_tool = next((tool for tool in self.tools if "PatientDataSearchTool" in tool.name or "patient_data" in tool.name.lower()), None)
            logger.info("Looking for PatientDataSearchTool after PatientIdSearchTool")
            if patient_data_tool:
                try:
                    tool_input = {
                        "query": state.query or self.query,
                        "patient_id": state.patient_id or []
                    }
                    logger.info("Custom state", json.dumps(state.model_dump(), indent=2))
                    validated_input = PatientDataSearchInput(**tool_input)
                    logger.info(f"Executing PatientDataSearchTool with input: {validated_input}")
                    patient_data_result = await patient_data_tool.ainvoke(tool_input)
                    patient_data_message = ToolMessage(
                        content=str(patient_data_result),
                        tool_call_id=f"{patient_data_tool.name}_{datetime.now().timestamp()}",
                        name=patient_data_tool.name
                    )
                    tool_messages.append(patient_data_message)
                    logger.info("PatientDataSearchTool executed successfully")
                except Exception as e:
                    logger.error(f"Error executing PatientDataSearchTool: {e}")
                    error_message = AIMessage(content=f"Error executing {patient_data_tool.name}: {str(e)}")
                    tool_messages.append(error_message)
            if not tool_messages:
                logger.warning("No appropriate tools found for user_specific query")
                logger.info(f"Available tools: {[tool.name for tool in self.tools]}")
                return state.update_state(
                    messages=[AIMessage(content=f"No PatientIdSearchTool or PatientDataSearchTool found. Available tools: {', '.join([tool.name for tool in self.tools])}")],
                    next_action="continue"
                )
        else:
            logger.info("Generic query detected, looking for PatientDataSearchTool...")
            patient_data_tool = next((tool for tool in self.tools if "PatientDataSearchTool" in tool.name or "patient_data" in tool.name.lower()), None)
            logger.info(f"Looking for PatientDataSearchTool for generic query")
            if patient_data_tool is None:
                logger.warning("No PatientDataSearchTool found for generic query")
                logger.info(f"Available tools: {[tool.name for tool in self.tools]}")
                return state.update_state(
                    messages=[AIMessage(content=f"No PatientDataSearchTool found for generic query. Available tools: {', '.join([tool.name for tool in self.tools])}")],
                    next_action="continue"
                )
            try:
                tool_input = {
                    "query": state.query or self.query,
                }
                validated_input = PatientDataSearchInput(**tool_input)
                patient_data_result = await patient_data_tool.ainvoke(tool_input)
                patient_data_message = ToolMessage(
                    content=str(patient_data_result),
                    tool_call_id=f"{patient_data_tool.name}_{datetime.now().timestamp()}",
                    name=patient_data_tool.name
                )
                tool_messages.append(patient_data_message)
                logger.info(f"PatientDataSearchTool executed successfully for generic query")
            except Exception as e:
                logger.error(f"Error executing PatientDataSearchTool for generic query: {e}")
                error_message = AIMessage(content=f"Error executing {patient_data_tool.name}: {str(e)}")
                tool_messages.append(error_message)
        return state.update_state(
            messages=tool_messages,
            next_action="continue"
        )
    return node

def agent_node(self):
    async def node(state):
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", agent_prompt),
            ("human", agent_node_human_prompt)
        ])
        messages = (state.messages or [])[-10:]
        response = await self.llm.ainvoke(
            prompt_template.format_messages(UserQuery=state.query, query=messages)
        )
        return state.update_state(
            messages=[AIMessage(content=response.content)]
        )
    return node

def store_chat_node(self):
    async def node(state):
        try:
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
        return updated_state
    return node

def should_continue(self):
    def fn(state):
        logger.info("Checking if the last message requires tool calls or chat storage...")
        next_action = state.next_action
        if next_action == "reject":
            return "store_chat"
        else:
            logger.info("Continuing to tools node for further processing.")
            return "tools"
    return fn 