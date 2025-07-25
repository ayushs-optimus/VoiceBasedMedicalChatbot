from fastapi import WebSocket
from typing import Dict, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    WebSocket manager for voice chat functionality
    """
    
    def __init__(self):
        # Store connections by session_id for voice chat
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a WebSocket for voice chat"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.connection_metadata[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "message_count": 0,
            "type": "voice"
        }
        logger.info(f"Voice WebSocket connected for session: {session_id}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Disconnect a voice WebSocket"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.connection_metadata:
            del self.connection_metadata[session_id]
        logger.info(f"Voice WebSocket disconnected for session: {session_id}")

    async def send_message(self, websocket: WebSocket, message: Dict):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
            
            # Update message count if we can find the session
            for session_id, ws in self.active_connections.items():
                if ws == websocket:
                    if session_id in self.connection_metadata:
                        self.connection_metadata[session_id]["message_count"] += 1
                    break
                    
        except Exception as e:
            logger.error(f"Error sending voice WebSocket message: {str(e)}")
            # Find and disconnect the problematic connection
            for session_id, ws in list(self.active_connections.items()):
                if ws == websocket:
                    self.disconnect(websocket, session_id)
                    break

    async def send_to_session(self, session_id: str, message: Dict):
        """Send message to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await self.send_message(websocket, message)
        else:
            logger.warning(f"No voice WebSocket connection found for session: {session_id}")

    async def send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to WebSocket"""
        error_msg = {
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.send_message(websocket, error_msg)

    async def broadcast_to_all_voice_sessions(self, message: Dict):
        """Broadcast message to all voice WebSocket connections"""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            try:
                await self.send_message(websocket, message)
            except Exception as e:
                logger.error(f"Error broadcasting to voice session {session_id}: {str(e)}")
                disconnected_sessions.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected_sessions:
            if session_id in self.active_connections:
                websocket = self.active_connections[session_id]
                self.disconnect(websocket, session_id)

    def get_active_voice_sessions(self) -> List[str]:
        """Get list of active voice session IDs"""
        return list(self.active_connections.keys())

    def get_connection_info(self, session_id: str) -> Dict:
        """Get connection metadata for a session"""
        return self.connection_metadata.get(session_id, {})

    def is_session_connected(self, session_id: str) -> bool:
        """Check if a session has an active voice WebSocket connection"""
        return session_id in self.active_connections