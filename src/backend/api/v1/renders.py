import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from src.backend.core.database import get_db
from src.backend.core.config import settings
from src.backend.schemas.renders import (
    RenderJobCreate,
    RenderJobResponse,
    RenderJobStatusResponse,
)
from src.backend.services.rendering import RenderService
from src.backend.core.logging import get_logger

logger = get_logger("dota.api.renders")

router = APIRouter(prefix="/render", tags=["Media Rendering Context"])

@router.post(
    "/jobs",
    response_model=RenderJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enqueue Video Render Job"
)
def create_render_job(job_data: RenderJobCreate, db: Session = Depends(get_db)):
    """
    Submits a video rendering task to the async worker queue.
    Returns the created job_id and initial PENDING status.
    """
    logger.info(f"Submitting render job for player_id: {job_data.player_id}, metric: '{job_data.metric}'")
    return RenderService.create_render_job(db, job_data)

@router.get(
    "/jobs/{job_id}",
    response_model=RenderJobStatusResponse,
    summary="Poll Render Job Status and Progress"
)
def get_render_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Polls the current status, progress percentage (0-100%), video URL, and expiration timestamp.
    """
    status_res = RenderService.get_render_job_status(db, job_id)
    if not status_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Render job '{job_id}' not found."
        )
    return status_res

@router.get(
    "/jobs",
    response_model=List[RenderJobResponse],
    summary="List Render Jobs for Player or All Recent Jobs"
)
def list_player_jobs(
    player_id: Optional[int] = Query(None, description="32-bit Steam ID of player"),
    db: Session = Depends(get_db)
):
    """Retrieves render jobs for player_id or all recent render jobs if player_id is omitted."""
    return RenderService.list_player_render_jobs(db, player_id)

@router.get(
    "/media/{filename}",
    summary="Stream or Download Rendered MP4 Video"
)
def get_rendered_media(filename: str):
    """
    Streams or downloads the rendered MP4 video file from ephemeral storage.
    """
    # Security check: prevent path traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.abspath(os.path.join(settings.EPHEMERAL_STORAGE_DIR, safe_filename))

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendered video file not found or has expired."
        )

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        content_disposition_type="inline",
        headers={"Accept-Ranges": "bytes"}
    )
