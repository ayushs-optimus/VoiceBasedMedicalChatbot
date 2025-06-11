from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import logging

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


@router.post("/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(has_role(["user", "admin"]))
):
    """
    Generate a chat completion using RAG or LangGraph agent.

    Args:
        request (ChatRequest): Input chat request with messages and options.
        background_tasks (BackgroundTasks): FastAPI background task manager.
        current_user (User): Authenticated user with role validation.

    Returns:
        ChatResponse: Assistant's response and metadata.
    """
    try:
        
        agent_executor = await get_agent_executor()
        result = await agent_executor.ainvoke({
            "query": request.query,
            "system_message": request.system_message,
            "user_role": current_user.roles,
            "thread_id": request.user_id or "Unkown",
            "session_id": request.session_id or "Unknown",
        })
        print("result ", result)

        response_message = ChatMessage(
            role="assistant",
            content=result.get("output", "No response generated.")
        )

        created_at = result.get("created_at")
        citations = result.get("citations", [])
        
        # Background logging
        background_tasks.add_task(
            log_chat_completion,
            user_id=current_user.username,
            request=request,
            response=response_message
        )

        return ChatResponse(
            message=response_message,
            user_id=request.user_id or "Unknown",
            session_id=request.session_id or "Unknown",
            created_at=created_at,
            citations=citations
        )

    except Exception as e:
        logger.exception(f"Error in chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating chat completion."
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
