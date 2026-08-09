import urllib.parse
import re
import jwt
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from src.backend.core.config import settings
from src.backend.core.logging import get_logger
from src.backend.models.users import SteamUserModel
from src.backend.models.base import utc_now

logger = get_logger("dota.service.auth")

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_BASE_ID64 = 76561197889877071

def steam_id64_to_32(steam_id64: str) -> int:
    """Converts a 64-bit Steam ID to a 32-bit account ID."""
    try:
        return int(steam_id64) - STEAM_BASE_ID64
    except Exception:
        return 0

class JWTManager:
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Encodes payload data into an HS256 JWT access token."""
        to_encode = data.copy()
        now = utc_now()
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": int(expire.timestamp()),
            "iat": int(now.timestamp())
        })
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[dict]:
        """Decodes and validates an HS256 JWT access token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token signature expired.")
            return None
        except jwt.PyJWTError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None

class SteamAuthService:
    @staticmethod
    def get_steam_login_url(return_to: str) -> str:
        """Constructs Steam OpenID 2.0 redirect URL."""
        parsed_return = urllib.parse.urlparse(return_to)
        realm = f"{parsed_return.scheme}://{parsed_return.netloc}" if parsed_return.netloc else return_to

        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": return_to,
            "openid.realm": realm,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        return f"{STEAM_OPENID_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    def verify_steam_callback(cls, params: Dict[str, str]) -> Optional[str]:
        """
        Verifies OpenID parameters returned by Steam callback.
        Returns the verified steam_id64 string or None.
        """
        validation_params = dict(params)
        validation_params["openid.mode"] = "check_authentication"

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(STEAM_OPENID_URL, data=validation_params)
                if resp.status_code == 200 and "is_valid:true" in resp.text:
                    claimed_id = params.get("openid.claimed_id", "")
                    match = re.search(r"https?://steamcommunity\.com/openid/id/(\d+)", claimed_id)
                    if match:
                        return match.group(1)
        except Exception as e:
            logger.error(f"Error validating Steam OpenID response: {e}")

        return None

    @classmethod
    def authenticate_or_create_user(
        cls,
        db: Session,
        steam_id64: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> SteamUserModel:
        """Creates or updates a SteamUserModel entity in the database."""
        now = utc_now()
        steam_id32 = steam_id64_to_32(steam_id64)

        user = db.query(SteamUserModel).filter_by(steam_id64=steam_id64).first()
        if not user:
            user = SteamUserModel(
                steam_id64=steam_id64,
                steam_id32=steam_id32,
                display_name=display_name or f"SteamUser_{steam_id32}",
                avatar_url=avatar_url,
                role="user",
                is_active=True,
                last_login_at=now
            )
            db.add(user)
        else:
            if display_name:
                user.display_name = display_name
            if avatar_url:
                user.avatar_url = avatar_url
            user.last_login_at = now

        db.commit()
        db.refresh(user)
        return user
