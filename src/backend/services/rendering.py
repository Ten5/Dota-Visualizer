import uuid
import threading
from typing import List, Optional
from sqlalchemy.orm import Session

from src.backend.models.renders import RenderJobModel
from src.backend.models.base import utc_now
from src.backend.schemas.renders import (
    RenderJobCreate,
    RenderJobResponse,
    RenderJobStatusResponse,
)
from src.backend.core.logging import get_logger

logger = get_logger("dota.service.rendering")

class RenderService:
    @classmethod
    def create_render_job(cls, db: Session, job_data: RenderJobCreate) -> RenderJobResponse:
        """
        Creates a new render job record and enqueues async video rendering task.
        Fallback to background thread execution if Redis/Celery queue is unavailable.
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now = utc_now()

        render_job = RenderJobModel(
            job_id=job_id,
            player_id=job_data.player_id,
            metric=job_data.metric,
            aspect_ratio=job_data.aspect_ratio,
            theme=job_data.theme,
            quality=job_data.quality,
            custom_audio_id=job_data.custom_audio_id,
            status="PENDING",
            progress=0,
            created_at=now
        )

        db.add(render_job)
        db.commit()
        db.refresh(render_job)

        # Enqueue rendering task via Celery with fallback thread
        cls._dispatch_render_task(job_id)

        logger.info(f"Created render job {job_id} for player {job_data.player_id}")

        return RenderJobResponse.model_validate(render_job)

    @classmethod
    def _dispatch_render_task(cls, job_id: str):
        """Attempts Celery task dispatch; falls back to threading if Redis is offline."""
        try:
            from src.backend.worker import render_video_task
            render_video_task.delay(job_id)
            logger.info(f"Enqueued job {job_id} to Celery worker queue.")
        except Exception as e:
            logger.warning(f"Celery dispatch failed ({e}), running job {job_id} in background thread.")
            from src.backend.worker import process_render_job
            from src.backend.core.database import SessionLocal

            def thread_target():
                thread_db = SessionLocal()
                try:
                    process_render_job(job_id, thread_db)
                finally:
                    thread_db.close()

            thread = threading.Thread(target=thread_target, daemon=True)
            thread.start()

    @staticmethod
    def get_render_job_status(db: Session, job_id: str) -> Optional[RenderJobStatusResponse]:
        """Queries job status, progress, video URL, and expiration timestamp."""
        job = db.query(RenderJobModel).filter_by(job_id=job_id).first()
        if not job:
            return None

        return RenderJobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            video_url=job.video_url,
            expires_at=job.expires_at,
            error_message=job.error_message
        )

    @staticmethod
    def list_player_render_jobs(db: Session, player_id: Optional[int] = None) -> List[RenderJobResponse]:
        """Lists all render jobs submitted for player_id or all recent jobs if player_id is None."""
        query = db.query(RenderJobModel)
        if player_id and player_id > 0:
            query = query.filter_by(player_id=player_id)
        jobs = query.order_by(RenderJobModel.created_at.desc()).limit(20).all()
        return [RenderJobResponse.model_validate(j) for j in jobs]
