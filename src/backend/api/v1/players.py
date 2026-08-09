from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.backend.core.database import get_db
from src.backend.services.ingestion import MatchIngestionService
from src.backend.services.lru_pruner import LRUCachePruner
from src.backend.schemas.matches import PlayerSyncResponse, PlayerMatchHistoryResponse
from src.backend.core.logging import get_logger

logger = get_logger("dota.api.players")

router = APIRouter(tags=["Match Ingestion & Players"])

@router.post(
    "/players/{player_id}/sync",
    response_model=PlayerSyncResponse,
    summary="Synchronize Player Match History (Incremental OpenDota Sync)"
)
def sync_player(player_id: int, db: Session = Depends(get_db)):
    """
    Triggers an offline-first incremental match sync for player_id.
    Fetches raw OpenDota JSON payloads and saves new matches to the database.
    """
    logger.info(f"Received sync request for player_id: {player_id}")
    return MatchIngestionService.sync_player_matches(db, player_id)

@router.get(
    "/players/{player_id}/matches",
    response_model=PlayerMatchHistoryResponse,
    summary="Get Player Profile and Cached Match History"
)
def get_player_matches(player_id: int, db: Session = Depends(get_db)):
    """
    Retrieves cached player profile and match history.
    Updates the player's last_accessed_at timestamp to prevent LRU cache eviction.
    """
    logger.info(f"Fetching match history for player_id: {player_id}")
    return MatchIngestionService.get_player_matches(db, player_id)


