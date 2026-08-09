from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class RenderJobCreate(BaseModel):
    player_id: int = Field(..., description="32-bit Steam ID of the target player")
    metric: str = Field(default="Hero Versatility", description="Visualization strategy metric name")
    quality: str = Field(default="Normal", description="Rendering quality preset ('Low', 'Normal', 'High')")
    aspect_ratio: str = Field(default="9:16", description="Video dimensions ('9:16' portrait or '16:9' landscape)")
    theme: str = Field(default="Midnight Cyberpunk", description="Visual theme palette name")
    custom_audio_id: Optional[str] = Field(default=None, description="Optional ID of custom uploaded music track")

class RenderJobResponse(BaseModel):
    job_id: str
    player_id: int
    metric: str
    aspect_ratio: str
    theme: str
    quality: str
    status: str
    progress: int = 0
    created_at: datetime
    video_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class RenderJobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    video_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None
