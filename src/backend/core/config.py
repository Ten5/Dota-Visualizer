import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Dota 2 Visualizer API"
    VERSION: str = "4.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite:///cache/dota_visualizer_v4.db",
        env="DATABASE_URL"
    )
    
    # Redis & Worker Queue
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    @property
    def normalized_redis_url(self) -> str:
        url = self.REDIS_URL.strip() if self.REDIS_URL else ""
        if url.startswith("rediss://") and "ssl_cert_reqs" not in url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}ssl_cert_reqs=none"
        return url
    
    # Auth & Security
    JWT_SECRET_KEY: str = Field(
        default="dev_secret_key_change_in_production_32bytes_min",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 Days
    STEAM_API_KEY: str = Field(default="", env="STEAM_API_KEY")
    
    # Ephemeral Storage & Purge Engine
    EPHEMERAL_STORAGE_DIR: str = Field(
        default="output/ephemeral",
        env="EPHEMERAL_STORAGE_DIR"
    )
    EPHEMERAL_TTL_SECONDS: int = Field(default=3600, env="EPHEMERAL_TTL_SECONDS")  # 1 hour
    LRU_INACTIVE_DAYS: int = Field(default=90, env="LRU_INACTIVE_DAYS")  # 90 days
    
    # CORS Policy
    CORS_ORIGINS: List[str] = [
        "http://localhost:3050",
        "http://127.0.0.1:3050",
        "http://localhost:8050",
        "http://127.0.0.1:8050",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ]
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "60/minute"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
