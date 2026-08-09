from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from src.backend.core.database import get_db
from src.backend.core.config import settings
from src.backend.models.users import SteamUserModel
from src.backend.schemas.auth import TokenResponse, UserResponse
from src.backend.services.auth import (
    SteamAuthService,
    JWTManager,
    steam_id64_to_32,
)
from src.backend.core.logging import get_logger

logger = get_logger("dota.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication Context"])
security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> SteamUserModel:
    """Dependency extracting and validating current authenticated user from JWT Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = JWTManager.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature expired or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload content.",
        )

    user = db.query(SteamUserModel).filter_by(id=int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found.",
        )

    return user

@router.get(
    "/steam/login",
    summary="Get Steam OpenID 2.0 Redirect URL"
)
def steam_login(
    return_to: str = Query(
        default="http://localhost:3050/auth/callback",
        description="Client callback URL where Steam redirects after login"
    )
):
    """Generates Steam OpenID 2.0 login URL for client redirection."""
    login_url = SteamAuthService.get_steam_login_url(return_to)
    return {"login_url": login_url}

@router.get(
    "/steam/callback",
    response_model=TokenResponse,
    summary="Steam OpenID Callback & JWT Session Token Generation"
)
def steam_callback(
    request: Request,
    mock_steam_id64: Optional[str] = Query(default=None, description="Optional mock Steam ID64 for development/testing"),
    db: Session = Depends(get_db)
):
    """
    Validates Steam OpenID callback parameters, creates or updates the SteamUserModel,
    and returns a signed JWT access token.
    """
    params = dict(request.query_params)
    steam_id64 = None

    # Development / Testing mock override (Disabled in production)
    if mock_steam_id64:
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Mock authentication is disabled in production environment."
            )
        logger.info(f"Using mock_steam_id64 for development login: {mock_steam_id64}")
        steam_id64 = mock_steam_id64
    else:
        steam_id64 = SteamAuthService.verify_steam_callback(params)

    if not steam_id64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Steam OpenID authentication failed or invalid callback parameters."
        )

    user = SteamAuthService.authenticate_or_create_user(db, steam_id64)

    token_data = {
        "sub": str(user.id),
        "steam_id64": user.steam_id64,
        "steam_id32": user.steam_id32,
        "role": user.role,
        "display_name": user.display_name,
    }

    access_token = JWTManager.create_access_token(token_data)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        steam_id64=user.steam_id64,
        display_name=user.display_name,
    )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Authenticated User Profile"
)
def get_me(current_user: SteamUserModel = Depends(get_current_user)):
    """Returns profile metadata for the currently authenticated Steam user."""
    return current_user
