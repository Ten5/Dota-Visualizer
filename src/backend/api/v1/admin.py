from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from src.backend.core.database import get_db
from src.backend.core.config import settings
from src.backend.services.lru_pruner import LRUCachePruner
from src.backend.services.ephemeral_cleaner import EphemeralCleaner
from src.backend.core.logging import get_logger

logger = get_logger("dota.api.admin")

router = APIRouter(prefix="/admin", tags=["Admin Housekeeping Context"])

@router.post(
    "/ephemeral-purge",
    summary="Trigger 1-Hour Ephemeral Media Purge"
)
def trigger_ephemeral_purge(
    ttl_seconds: int = Query(settings.EPHEMERAL_TTL_SECONDS, description="TTL threshold in seconds (default 3600s / 1 hour)"),
    db: Session = Depends(get_db)
):
    """
    Triggers periodic cleanup of expired video MP4 files older than ttl_seconds (default 1 hour).
    Removes files from disk and updates DB job status to EXPIRED.
    """
    logger.info(f"Triggering manual ephemeral media purge with TTL: {ttl_seconds} seconds")
    return EphemeralCleaner.purge_expired_media(db, ttl_seconds=ttl_seconds)

@router.post(
    "/lru-prune",
    summary="Trigger 90-Day LRU Cache Eviction"
)
def trigger_lru_prune(
    days_inactive: int = Query(settings.LRU_INACTIVE_DAYS, description="Inactivity threshold in days"),
    db: Session = Depends(get_db)
):
    """
    Triggers periodic LRU cache eviction of match history unaccessed for > days_inactive.
    """
    logger.info(f"Triggering LRU cache eviction task with threshold: {days_inactive} days")
    return LRUCachePruner.prune_inactive_matches(db, days_inactive=days_inactive)
