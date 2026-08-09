from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.backend.models.base import Base, TimestampMixin, utc_now

class SteamUserModel(Base, TimestampMixin):
    __tablename__ = "steam_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    steam_id64 = Column(String(64), unique=True, index=True, nullable=False)
    steam_id32 = Column(BigInteger, index=True, nullable=False)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login_at = Column(DateTime, default=utc_now, nullable=False)

    api_keys = relationship("ApiKeyModel", back_populates="user", cascade="all, delete-orphan")

class ApiKeyModel(Base, TimestampMixin):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_hash = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("steam_users.id", ondelete="CASCADE"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("SteamUserModel", back_populates="api_keys")
