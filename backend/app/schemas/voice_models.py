from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class VoiceTranscriptionRequest(BaseModel):
    text: str = Field(..., description="Transcribed text from voice input")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    is_final: bool = Field(True, description="Whether this is the final transcription")
    confidence: Optional[float] = Field(None, description="Transcription confidence score")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    user_roles: Optional[List[str]] = Field(default_factory=list, description="Roles of the user for context")

class VoiceStreamRequest(BaseModel):
    text: str = Field(..., description="Transcribed text for streaming response")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    stream_audio: bool = Field(False, description="Whether to include audio in stream")
    user_roles: Optional[List[str]] = Field(default_factory=list, description="Roles of the user for context")

class VoiceResponse(BaseModel):
    session_id: str
    response_text: str
    audio_url: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TranscriptionMessage(BaseModel):
    text: str
    timestamp: str
    is_final: bool
    confidence: Optional[float] = None
    session_id: str

class VoiceWebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type: transcription, ai_response, error, ping, pong")
    data: Dict[str, Any] = Field(..., description="Message payload")
    session_id: Optional[str] = None
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    user_roles: Optional[List[str]] = Field(default_factory=list, description="Roles of the user for context")

class VoiceConversationContext(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    user_roles: Optional[List[str]] = Field(default_factory=list, description="Roles of the user for context")
