import os
import time
from datetime import timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.backend.core.config import settings
from src.backend.models.renders import RenderJobModel
from src.backend.models.base import utc_now
from src.backend.core.logging import get_logger

logger = get_logger("dota.service.ephemeral_cleaner")

class EphemeralCleaner:
    @staticmethod
    def purge_expired_media(db: Session, ttl_seconds: int = 3600) -> Dict[str, Any]:
        """
        Purges rendered video MP4 files older than ttl_seconds (default 1 hour)
        from ephemeral storage and updates database render job records to 'EXPIRED'.
        Also removes any orphaned MP4 files on disk.
        """
        now = utc_now()
        cutoff_time = now - timedelta(seconds=ttl_seconds)

        logger.info(f"Running Ephemeral Media Storage Purge task. TTL threshold: {ttl_seconds}s (Cutoff: {cutoff_time.isoformat()})")

        # 1. Query expired render jobs in DB
        expired_jobs = db.query(RenderJobModel).filter(
            or_(
                RenderJobModel.expires_at <= now,
                RenderJobModel.created_at <= cutoff_time
            ),
            RenderJobModel.status != "EXPIRED"
        ).all()

        purged_jobs_count = 0
        freed_bytes = 0

        for job in expired_jobs:
            if job.file_path and os.path.exists(job.file_path):
                try:
                    freed_bytes += os.path.getsize(job.file_path)
                    os.remove(job.file_path)
                    logger.info(f"Deleted expired media file for job {job.job_id}: {job.file_path}")
                except Exception as e:
                    logger.error(f"Error removing file {job.file_path}: {e}")

            job.status = "EXPIRED"
            job.video_url = None
            purged_jobs_count += 1

        db.commit()

        # 2. Clean orphaned files in output/ephemeral directory
        ephemeral_dir = settings.EPHEMERAL_STORAGE_DIR
        orphaned_files_count = 0

        if os.path.exists(ephemeral_dir):
            now_ts = time.time()
            for filename in os.listdir(ephemeral_dir):
                if filename.endswith(".mp4"):
                    file_path = os.path.join(ephemeral_dir, filename)
                    try:
                        file_age = now_ts - os.path.getmtime(file_path)
                        if file_age > ttl_seconds:
                            freed_bytes += os.path.getsize(file_path)
                            os.remove(file_path)
                            orphaned_files_count += 1
                            logger.info(f"Deleted orphaned media file: {file_path} (Age: {int(file_age)}s)")
                    except Exception as e:
                        logger.error(f"Error checking/deleting file {file_path}: {e}")

        logger.info(f"Ephemeral Media Purge completed: {purged_jobs_count} DB jobs expired, {orphaned_files_count} orphan files deleted, {freed_bytes} bytes freed.")

        return {
            "status": "success",
            "ttl_seconds": ttl_seconds,
            "cutoff_time": cutoff_time.isoformat(),
            "purged_jobs_count": purged_jobs_count,
            "orphaned_files_count": orphaned_files_count,
            "freed_bytes": freed_bytes,
            "message": f"Successfully purged {purged_jobs_count} expired jobs and {orphaned_files_count} orphan files."
        }
