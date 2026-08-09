from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.backend.core.config import settings
from src.backend.core.database import get_db
from src.backend.core.logging import get_logger

logger = get_logger("dota.api.health")

router = APIRouter(tags=["Health"])

@router.get("/health", summary="System Health Check")
def health_check(db: Session = Depends(get_db)):
    """
    Returns server operational status and tests database connectivity.
    """
    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check DB ping failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failure"
        )

    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
