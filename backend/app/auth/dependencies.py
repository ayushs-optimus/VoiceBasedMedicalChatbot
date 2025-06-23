from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import User
from app.auth.auth import get_auth_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")  # Adjust if needed

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user"""
    # print(f"Validating token: {token}")
    auth_client = get_auth_client()
    user_info = await auth_client.validate_access_token(token)

    return User.model_construct(
        username=user_info["name"],
        email=user_info["upn"],
        roles=["admin","doctor"],
        object_id=user_info["oid"]
    )

def has_role(required_roles: List[str]):
    """Returns a dependency that ensures the user has one of the required roles"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        # print(f"Checking roles: {required_roles}")
        user_roles = set(current_user.roles)
        if not user_roles.intersection(required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker  
