from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import logging
from fastapi.responses import StreamingResponse
import json
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from app.schemas.auth import User
from app.auth.dependencies import get_current_user, has_role
from app.core.rag_engine import get_rag_engine
from app.agents.graph import get_agent_executor

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/completions")
async def chat_completions_streaming(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(has_role(["user", "admin"]))
):
    """
    Stream chat completions using a LangGraph agent.
    """

    try:
        agent_executor = await get_agent_executor()

        async def event_generator():
            async for result in agent_executor.astream({
                "query": request.query,
                "system_message": request.system_message,
                "user_role": current_user.roles,
                "thread_id": request.user_id or "Unknown",
                "session_id": request.session_id or "Unknown",
            }):
                # Extract core message from result
                output = result.get("output", "No response yet.")
                response_message = {
                    "role": "assistant",
                    "content": output,
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "tool_history": result.get("tool_history", []),
                }

                # Yield as SSE data (text/event-stream)
                yield f"data: {json.dumps(response_message)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.exception(f"Error in streaming chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error streaming chat completion."
        )


def log_chat_completion(user_id: str, request: ChatRequest, response: ChatMessage):
    """
    Background task to log chat interactions.

    Args:
        user_id (str): ID of the user.
        request (ChatRequest): Original chat request.
        response (ChatMessage): Assistant's response.
    """
    try:
        logger.info(f"Chat completion logged for user {user_id}: {response.content}")
    except Exception as e:
        logger.error(f"Failed to log chat completion: {e}")
