from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    steam_id64: str
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    steam_id64: str
    steam_id32: int
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    last_login_at: datetime

    class Config:
        from_attributes = True

class ApiKeyCreate(BaseModel):
    name: str

class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key: Optional[str] = None  # Only returned once upon creation
    is_active: bool
    created_at: datetime
