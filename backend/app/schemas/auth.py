from typing import List
from pydantic import BaseModel

class User(BaseModel):
    """User schema with Azure AD information"""
    username: str
    email: str
    roles: List[str]
    object_id: str