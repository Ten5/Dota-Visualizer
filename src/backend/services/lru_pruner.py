from datetime import timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.backend.models.matches import MatchModel, PlayerProfileModel
from src.backend.models.base import utc_now
from src.backend.core.config import settings
from src.backend.core.logging import get_logger

logger = get_logger("dota.service.lru_pruner")

class LRUCachePruner:
    @staticmethod
    def prune_inactive_matches(db: Session, days_inactive: Optional[int] = None) -> Dict[str, Any]:
        """
        Least Recently Used (LRU) Cache Eviction Engine.
        Prunes match records for public lookups whose last_accessed_at timestamp
        is older than `days_inactive` (default 90 days).
        """
        if days_inactive is None:
            days_inactive = settings.LRU_INACTIVE_DAYS

        cutoff_date = utc_now() - timedelta(days=days_inactive)
        logger.info(f"Running LRU Cache Pruning task. Cutoff date: {cutoff_date.isoformat()}")

        # Find public player profiles that are inactive
        inactive_profiles = db.query(PlayerProfileModel).filter(
            PlayerProfileModel.is_public == True,
            PlayerProfileModel.last_accessed_at < cutoff_date
        ).all()

        inactive_player_ids = [p.player_id for p in inactive_profiles]

        # Find matches with last_accessed_at < cutoff_date
        pruned_matches_count = 0
        pruned_profiles_count = len(inactive_profiles)

        if inactive_player_ids:
            deleted_matches = db.query(MatchModel).filter(
                MatchModel.player_id.in_(inactive_player_ids),
                MatchModel.last_accessed_at < cutoff_date
            ).delete(synchronize_session=False)
            
            pruned_matches_count += deleted_matches

            # Delete the inactive profiles
            db.query(PlayerProfileModel).filter(
                PlayerProfileModel.player_id.in_(inactive_player_ids)
            ).delete(synchronize_session=False)

        # Also delete orphaned matches older than cutoff_date
        orphaned_deleted = db.query(MatchModel).filter(
            MatchModel.last_accessed_at < cutoff_date
        ).delete(synchronize_session=False)

        pruned_matches_count += orphaned_deleted

        db.commit()

        logger.info(
            f"LRU Cache Pruning completed: {pruned_matches_count} matches, "
            f"{pruned_profiles_count} profiles evicted."
        )

        return {
            "status": "success",
            "days_inactive_threshold": days_inactive,
            "cutoff_date": cutoff_date.isoformat(),
            "pruned_matches": pruned_matches_count,
            "pruned_profiles": pruned_profiles_count,
            "message": f"Evicted {pruned_matches_count} inactive matches and {pruned_profiles_count} profiles."
        }
