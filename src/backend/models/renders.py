from sqlalchemy import Column, String, BigInteger, Integer, Text, DateTime
from src.backend.models.base import Base, TimestampMixin, utc_now

class RenderJobModel(Base, TimestampMixin):
    __tablename__ = "render_jobs"

    job_id = Column(String(64), primary_key=True, index=True)
    player_id = Column(BigInteger, nullable=False, index=True)
    metric = Column(String(100), nullable=False)
    aspect_ratio = Column(String(10), default="9:16", nullable=False)
    theme = Column(String(100), default="Midnight Cyberpunk", nullable=False)
    quality = Column(String(50), default="Normal", nullable=False)
    custom_audio_id = Column(String(128), nullable=True)
    
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)
    video_url = Column(String(512), nullable=True)
    file_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)
    
    expires_at = Column(DateTime, nullable=True, index=True)
