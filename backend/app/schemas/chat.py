from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ChatMessage(BaseModel):
    """Chat message schema"""
    role: str
    content: str

class Citation(BaseModel):
    """Citation schema for references in RAG responses"""
    title: str
    source: str
    content: str
    id: str

class ChatRequest(BaseModel):
    """Chat request schema"""
    query: str = Field(..., description="The messages in the conversation")
    system_message: Optional[str] = Field(None, description="Optional system message to control the assistant's behavior")
    user_id: Optional[str] = Field(None, description="user ID for continuing an existing conversation")
    session_id: Optional[str] = Field(None, description="Session ID for tracking the session")
    roles: List[str] = Field(default_factory=list, description="Roles of the user making the request")

class ChatResponse(BaseModel):
    """Chat response schema"""
    message: ChatMessage
    user_id: str
    session_id: str
    created_at: Optional[str] = None
    citations: Optional[List[Citation]] = None