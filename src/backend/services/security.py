import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session

from src.backend.models.users import ApiKeyModel, SteamUserModel
from src.backend.schemas.auth import ApiKeyCreate, ApiKeyResponse
from src.backend.core.logging import get_logger

logger = get_logger("dota.service.security")

class ApiKeyService:
    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Computes SHA-256 hash of an API key string."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def generate_api_key(
        cls,
        db: Session,
        name: str,
        user_id: Optional[int] = None
    ) -> ApiKeyResponse:
        """
        Generates a secure API key string ('dota_live_...'), stores its SHA-256 hash in DB,
        and returns ApiKeyResponse with raw key returned once to the caller.
        """
        raw_key = f"dota_live_{secrets.token_hex(16)}"
        key_hash = cls.hash_key(raw_key)

        api_key_obj = ApiKeyModel(
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            is_active=True,
            expires_at=None
        )

        db.add(api_key_obj)
        db.commit()
        db.refresh(api_key_obj)

        logger.info(f"Generated API Key '{name}' (ID: {api_key_obj.id}) for user_id: {user_id}")

        return ApiKeyResponse(
            id=api_key_obj.id,
            name=api_key_obj.name,
            key=raw_key,
            is_active=api_key_obj.is_active,
            created_at=api_key_obj.created_at
        )

    @classmethod
    def validate_api_key(cls, db: Session, raw_key: str) -> Optional[ApiKeyModel]:
        """
        Validates raw_key string against stored key_hash values.
        Verifies that key is active and not expired.
        """
        if not raw_key:
            return None

        key_hash = cls.hash_key(raw_key)
        api_key_obj = db.query(ApiKeyModel).filter_by(key_hash=key_hash, is_active=True).first()

        if not api_key_obj:
            return None

        if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
            logger.warning(f"API Key ID {api_key_obj.id} has expired.")
            return None

        return api_key_obj

    @staticmethod
    def list_user_api_keys(db: Session, user_id: int) -> List[ApiKeyResponse]:
        """Retrieves active API keys owned by user_id."""
        keys = db.query(ApiKeyModel).filter_by(user_id=user_id, is_active=True).order_by(ApiKeyModel.created_at.desc()).all()
        return [
            ApiKeyResponse(
                id=k.id,
                name=k.name,
                key=None,  # Do not return raw key on listing
                is_active=k.is_active,
                created_at=k.created_at
            )
            for k in keys
        ]

    @staticmethod
    def revoke_api_key(db: Session, user_id: int, key_id: int) -> bool:
        """Deactivates an API key owned by user_id."""
        key_obj = db.query(ApiKeyModel).filter_by(id=key_id, user_id=user_id).first()
        if not key_obj:
            return False

        key_obj.is_active = False
        db.commit()
        logger.info(f"Revoked API Key ID {key_id} for user_id: {user_id}")
        return True
