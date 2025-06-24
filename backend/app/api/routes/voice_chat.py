from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.schemas.voice_models import (
    VoiceTranscriptionRequest,
    VoiceStreamRequest,
    VoiceResponse,
    TranscriptionMessage
)
from app.services.voice_service import VoiceService
from app.services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice-chat"])

# Initialize services
voice_service = VoiceService()
websocket_manager = WebSocketManager()


@router.post("/transcribe", response_model=VoiceResponse)
async def process_transcription(request: VoiceTranscriptionRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        response = await voice_service.process_transcription(
            text=request.text,
            session_id=session_id,
            user_id=request.user_id,
            is_final=request.is_final,
            user_roles=request.user_roles if hasattr(request, 'user_roles') else []
        )

        return VoiceResponse(
            session_id=session_id,
            response_text=response["text"],
            audio_url=response.get("audio_url"),
            timestamp=datetime.now(),
            metadata=response.get("metadata", {})
        )

    except Exception as e:
        logger.error(f"Error processing transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_voice_response(request: VoiceStreamRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())

        async def generate_voice_stream():
            try:
                async for chunk in voice_service.stream_voice_response(
                    text=request.text,
                    session_id=session_id,
                    user_id=request.user_id,
                    user_roles=request.user_roles if hasattr(request, 'user_roles') else []
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                logger.error(f"Error in voice streaming: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            generate_voice_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )

    except Exception as e:
        logger.error(f"Error setting up voice stream: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket Endpoint
@router.websocket("/ws/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket_manager.connect(websocket, session_id)
    logger.info(f"Voice WebSocket connected for session: {session_id}")

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received data: {data}")

            try:
                message_data = json.loads(data)
                print(f"Parsed message data: {message_data}")
                print("session_id:", session_id)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                await websocket_manager.send_error(websocket, "Invalid JSON format")
                continue

            msg_type = message_data.get("type")
            logger.info(f"Received voice message: {msg_type}")

            if msg_type == "transcription":
                await handle_voice_transcription(websocket, message_data, session_id)
            elif msg_type == "ping":
                await websocket_manager.send_message(
                    websocket, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                await websocket_manager.send_error(websocket, f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, session_id)
        logger.info(f"Voice WebSocket disconnected for session: {session_id}")

    except Exception as e:
        logger.exception(f"Error in voice WebSocket for session {session_id}: {e}")
        await websocket_manager.send_error(websocket, str(e))

# ⬇️ Updated with roles
async def handle_voice_transcription(websocket: WebSocket, message_data: dict, session_id: str):
    try:
        transcription_data = message_data["data"]
        user_roles = transcription_data.get("user_roles", [])
        user_id = transcription_data.get("user_id")

        if transcription_data.get("isFinal", False):
            user_text = transcription_data["text"]
            logger.info(f"Processing final voice transcription: {user_text}")

            ai_response = await voice_service.generate_voice_response(
                text=user_text,
                session_id=session_id,
                user_id=user_id,
                user_roles=user_roles
            )

            await websocket_manager.send_message(
                websocket,
                {
                    "type": "ai_response",
                    "data": {
                        "text": ai_response["text"],
                        "audio_url": ai_response.get("audio_url"),
                        "timestamp": datetime.now().isoformat(),
                        "session_id": session_id
                    }
                }
            )
            logger.info(f"Sent voice AI response for session: {session_id}")
        else:
            logger.debug(f"Interim voice transcription: {transcription_data['text']}")

    except Exception as e:
        logger.error(f"Error handling voice transcription: {str(e)}")
        await websocket_manager.send_error(websocket, f"Error processing voice: {str(e)}")

@router.get("/sessions/{session_id}/history")
async def get_voice_session_history(session_id: str):
    """Get voice conversation history for a session"""
    try:
        history = await voice_service.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        logger.error(f"Error getting voice session history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def clear_voice_session(session_id: str):
    """Clear voice conversation history for a session"""
    try:
        await voice_service.clear_session(session_id)
        return {"message": f"Voice session {session_id} cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing voice session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))