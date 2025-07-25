import asyncio
import logging
import json
from typing import Dict, List, Optional, AsyncGenerator, Any
from datetime import datetime
import uuid

from app.agents.graph import get_agent_executor
from app.services.cosmos_db_handler import CosmosDBHandler
from app.config import get_settings

logger = logging.getLogger(__name__)

# ... [imports remain unchanged]

class VoiceService:
    def __init__(self):
        self.settings = get_settings()
        self.active_sessions: Dict[str, Dict] = {}

    async def process_transcription(
        self, 
        text: str, 
        session_id: str, 
        user_id: Optional[str] = None,
        is_final: bool = True,
        user_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            if not is_final:
                return {
                    "text": f"Processing: {text[:50]}..." if len(text) > 50 else f"Processing: {text}",
                    "metadata": {"interim": True}
                }

            executor = await get_agent_executor()
            agent_input = {
                "query": text,
                "thread_id": user_id or session_id,
                "session_id": session_id,
                "user_roles": user_roles or []
            }

            response_text = ""
            async for chunk in executor.astream(agent_input):
                if chunk.get("type") == "stream" and chunk.get("output"):
                    response_text += chunk["output"]
                elif chunk.get("type") == "complete_response" and chunk.get("output"):
                    response_text = chunk["output"]
                elif chunk.get("type") == "complete":
                    break

            if not response_text:
                response_text = "I received your message but couldn't generate a response. Please try again."

            return {
                "text": response_text,
                "metadata": {
                    "session_id": session_id,
                    "processed_at": datetime.now().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error processing transcription: {str(e)}")
            return {
                "text": "I'm sorry, I encountered an error processing your request. Please try again.",
                "metadata": {"error": str(e)}
            }

    async def stream_voice_response(
        self, 
        text: str, 
        session_id: str, 
        user_id: Optional[str] = None,
        user_roles: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            executor = await get_agent_executor()
            agent_input = {
                "query": text,
                "thread_id": user_id or session_id,
                "session_id": session_id,
                "user_roles": user_roles or []
            }

            full_response = ""
            async for chunk in executor.astream(agent_input):
                chunk_data = {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "type": chunk.get("type", "unknown"),
                    "node": chunk.get("node", "unknown")
                }

                if chunk.get("type") == "stream" and chunk.get("output"):
                    full_response += chunk["output"]
                    chunk_data.update({
                        "text": chunk["output"],
                        "is_partial": True,
                        "full_text": full_response
                    })
                    yield chunk_data

                elif chunk.get("type") == "complete_response" and chunk.get("output"):
                    chunk_data.update({
                        "text": chunk["output"],
                        "is_partial": False,
                        "full_text": chunk["output"]
                    })
                    yield chunk_data

                elif chunk.get("type") == "tool_result" and chunk.get("output"):
                    chunk_data.update({
                        "tool_result": chunk["output"],
                        "is_partial": False
                    })
                    yield chunk_data

                elif chunk.get("type") == "complete":
                    chunk_data.update({
                        "status": "complete",
                        "final_text": full_response or "Response completed.",
                        "is_partial": False
                    })
                    yield chunk_data
                    break

        except Exception as e:
            logger.error(f"Error streaming voice response: {str(e)}")
            yield {
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "type": "error"
            }

    async def generate_voice_response(
        self, 
        text: str, 
        session_id: str, 
        user_id: Optional[str] = None,
        user_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            executor = await get_agent_executor()
            agent_input = {
                "query": text,
                "thread_id": user_id or session_id,
                "session_id": session_id,
                "user_roles": user_roles or []
            }

            response_text = ""
            tool_results = []

            async for chunk in executor.astream(agent_input):
                if chunk.get("type") == "stream" and chunk.get("output"):
                    response_text += chunk["output"]
                elif chunk.get("type") == "complete_response" and chunk.get("output"):
                    response_text = chunk["output"]
                elif chunk.get("type") == "tool_result" and chunk.get("output"):
                    tool_results.append(chunk["output"])
                elif chunk.get("type") == "complete":
                    break

            if not response_text:
                response_text = "I've processed your request successfully."

            return {
                "text": response_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "tool_results": tool_results,
                    "user_id": user_id,
                    "user_roles": user_roles or []
                }
            }

        except Exception as e:
            logger.error(f"Error generating voice response: {str(e)}")
            return {
                "text": "I'm sorry, I encountered an error. Please try again.",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {"error": str(e)}
            }

    async def handle_voice_interruption(
        self, 
        session_id: str, 
        new_text: str,
        user_id: Optional[str] = None,
        user_roles: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        try:
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                if "task" in session_data:
                    session_data["task"].cancel()

            response = await self.generate_voice_response(new_text, session_id, user_id, user_roles)

            return {
                "text": response["text"],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "interrupted": True,
                "metadata": response.get("metadata", {})
            }

        except Exception as e:
            logger.error(f"Error handling voice interruption: {str(e)}")
            return {
                "text": "I was interrupted but I'm ready to continue. What would you like to know?",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "interrupted": True,
                "metadata": {"error": str(e)}
            }

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        try:
            return []
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            return []

    async def clear_session(self, session_id: str) -> bool:
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            return True
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return False

    def start_session_task(self, session_id: str, task):
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {}
        self.active_sessions[session_id]["task"] = task

    def end_session_task(self, session_id: str):
        if session_id in self.active_sessions and "task" in self.active_sessions[session_id]:
            del self.active_sessions[session_id]["task"]
