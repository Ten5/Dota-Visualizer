from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.backend.core.database import get_db
from src.backend.models.users import SteamUserModel
from src.backend.schemas.auth import ApiKeyCreate, ApiKeyResponse
from src.backend.api.v1.auth import get_current_user
from src.backend.services.security import ApiKeyService
from src.backend.core.logging import get_logger

logger = get_logger("dota.api.keys")

router = APIRouter(prefix="/keys", tags=["Developer Security & API Keys"])

@router.post(
    "",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Developer API Key"
)
def create_api_key(
    key_create: ApiKeyCreate,
    current_user: SteamUserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a new developer API key for the authenticated user.
    The raw API key ('dota_live_...') is returned ONCE in this response.
    """
    logger.info(f"Creating API Key '{key_create.name}' for user {current_user.id}")
    return ApiKeyService.generate_api_key(db, name=key_create.name, user_id=current_user.id)

@router.get(
    "",
    response_model=List[ApiKeyResponse],
    summary="List Authenticated User API Keys"
)
def list_api_keys(
    current_user: SteamUserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists active API keys created by the authenticated user."""
    return ApiKeyService.list_user_api_keys(db, user_id=current_user.id)

@router.delete(
    "/{key_id}",
    summary="Revoke Developer API Key"
)
def revoke_api_key(
    key_id: int,
    current_user: SteamUserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes and deactivates an existing API key."""
    success = ApiKeyService.revoke_api_key(db, user_id=current_user.id, key_id=key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key ID {key_id} not found or does not belong to user."
        )
    return {"status": "success", "message": f"API Key ID {key_id} has been revoked."}
