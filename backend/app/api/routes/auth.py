from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import Token, User
from app.auth.auth import (
    authenticate_user, 
    create_access_token, 
    fake_users_db
)
from app.auth.dependencies import get_current_user, has_role
from app.config import get_settings
from app.services.telemetry import get_telemetry_client

router = APIRouter(
    tags=["authentication"],
    responses={401: {"description": "Unauthorized from authentication"}},
)

telemetry_client = get_telemetry_client()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        telemetry_client.track_event(
            "FailedLogin",
            {"username": form_data.username}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=get_settings().ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires
    )
    
    telemetry_client.track_event(
        "SuccessfulLogin",
        {"username": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user
    """
    return current_user

@router.get("/admin/users", response_model=list[User])
async def list_users(current_user: User = Depends(has_role(["admin"]))):
    """
    List all users (admin only)
    """
    return [
        User(
            username=username,
            email=data["email"],
            disabled=data["disabled"],
            roles=data["roles"]
        )
        for username, data in fake_users_db.items()
    ]