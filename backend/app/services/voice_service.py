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

class VoiceService:
    def __init__(self):
        self.settings = get_settings()
        self.active_sessions: Dict[str, Dict] = {}
        
    async def process_transcription(
        self, 
        text: str, 
        session_id: str, 
        user_id: Optional[str] = None,
        is_final: bool = True
    ) -> Dict[str, Any]:
        """Process voice transcription through LangGraph agent"""
        try:
            if not is_final:
                # For interim results, just acknowledge
                return {
                    "text": f"Processing: {text[:50]}..." if len(text) > 50 else f"Processing: {text}",
                    "metadata": {"interim": True}
                }
            
            # Get agent executor
            executor = await get_agent_executor()
            
            # Prepare input for the agent
            agent_input = {
                "query": text,
                "thread_id": user_id or session_id,
                "session_id": session_id
            }
            
            # Get response from agent (non-streaming for this endpoint)
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
        user_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream voice response through LangGraph agent"""
        try:
            # Get agent executor
            executor = await get_agent_executor()
            
            # Prepare input for the agent
            agent_input = {
                "query": text,
                "thread_id": user_id or session_id,
                "session_id": session_id
            }
            
            # Stream response from agent
            full_response = ""
            async for chunk in executor.astream(agent_input):
                chunk_data = {
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "type": chunk.get("type", "unknown"),
                    "node": chunk.get("node", "unknown")
                }
                
                if chunk.get("type") == "stream" and chunk.get("output"):
                    # Streaming text chunk
                    full_response += chunk["output"]
                    chunk_data.update({
                        "text": chunk["output"],
                        "is_partial": True,
                        "full_text": full_response
                    })
                    yield chunk_data
                    
                elif chunk.get("type") == "complete_response" and chunk.get("output"):
                    # Complete response from query identification
                    chunk_data.update({
                        "text": chunk["output"],
                        "is_partial": False,
                        "full_text": chunk["output"]
                    })
                    yield chunk_data
                    
                elif chunk.get("type") == "tool_result" and chunk.get("output"):
                    # Tool execution result
                    chunk_data.update({
                        "tool_result": chunk["output"],
                        "is_partial": False
                    })
                    yield chunk_data
                    
                elif chunk.get("type") == "complete":
                    # Final completion
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
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate complete voice response for WebSocket"""
        try:
            # Get agent executor
            executor = await get_agent_executor()
            
            # Prepare input for the agent
            agent_input = {
                "query": text,
                "thread_id": user_id or session_id,
                "session_id": session_id
            }
            
            # Collect streaming response
            response_text = ""
            tool_results = []
            
            async for chunk in executor.astream(agent_input):
                if chunk.get("type") == "stream" and chunk.get("output"):
                    response_text += chunk["output"]
                elif chunk.get("type") == "complete_response" and chunk.get("output"):
                    # If we get a complete response (like from query identification), use it
                    response_text = chunk["output"]
                elif chunk.get("type") == "tool_result" and chunk.get("output"):
                    tool_results.append(chunk["output"])
                elif chunk.get("type") == "complete":
                    break
            
            # Ensure we have some response
            if not response_text:
                response_text = "I've processed your request successfully."
            
            return {
                "text": response_text,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "tool_results": tool_results,
                    "user_id": user_id
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
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle voice interruption during AI response"""
        try:
            # Cancel any ongoing processing for this session
            if session_id in self.active_sessions:
                session_data = self.active_sessions[session_id]
                if "task" in session_data:
                    session_data["task"].cancel()
            
            # Process the interruption as a new request
            response = await self.generate_voice_response(new_text, session_id, user_id)
            
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
        """Get conversation history for a session"""
        try:
            # This would typically query your database
            # For now, return empty list or implement based on your chat history storage
            return []
        except Exception as e:
            logger.error(f"Error getting session history: {str(e)}")
            return []
    
    async def clear_session(self, session_id: str) -> bool:
        """Clear session data"""
        try:
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            # Clear from database as well if needed
            return True
        except Exception as e:
            logger.error(f"Error clearing session: {str(e)}")
            return False
    
    def start_session_task(self, session_id: str, task):
        """Track active session tasks for interruption handling"""
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {}
        self.active_sessions[session_id]["task"] = task
    
    def end_session_task(self, session_id: str):
        """End session task tracking"""
        if session_id in self.active_sessions and "task" in self.active_sessions[session_id]:
            del self.active_sessions[session_id]["task"]