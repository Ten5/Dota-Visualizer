import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.models.matches import MatchModel, PlayerProfileModel
from src.backend.models.base import utc_now
from src.backend.schemas.matches import (
    PlayerSyncResponse,
    PlayerMatchHistoryResponse,
    PlayerProfileSchema,
    MatchSchema,
)
from src.backend.core.logging import get_logger

logger = get_logger("dota.service.ingestion")

OPENDOTA_BASE_URL = "https://api.opendota.com/api"

class MatchIngestionService:
    @staticmethod
    def fetch_opendota_profile(player_id: int) -> Dict[str, Any]:
        """Fetches player profile information from OpenDota API."""
        url = f"{OPENDOTA_BASE_URL}/players/{player_id}"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.warning(f"Failed to fetch profile from OpenDota for {player_id}: {e}")
        return {}

    @staticmethod
    def fetch_opendota_matches(player_id: int) -> List[Dict[str, Any]]:
        """Fetches complete match history from OpenDota API."""
        url = f"{OPENDOTA_BASE_URL}/players/{player_id}/matches"
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list):
                        return data
        except Exception as e:
            logger.error(f"Failed to fetch matches from OpenDota for {player_id}: {e}")
        return []

    @classmethod
    def sync_player_matches(cls, db: Session, player_id: int) -> PlayerSyncResponse:
        """
        Performs offline-first incremental match sync.
        Only new matches (match_id > highest_cached_match_id) are inserted.
        Stores full raw_json for future strategy extensibility.
        """
        now = utc_now()
        
        # Determine highest existing match_id for player
        max_match_id = db.query(func.max(MatchModel.match_id)).filter(
            MatchModel.player_id == player_id
        ).scalar()

        # Fetch matches from API
        api_matches = cls.fetch_opendota_matches(player_id)
        
        new_matches_count = 0
        if api_matches:
            for m in api_matches:
                m_id = m.get("match_id")
                if not m_id:
                    continue

                # Incremental sync check: skip if we already have this match or older
                if max_match_id and m_id <= max_match_id:
                    continue

                # Prepare MatchModel object
                match_obj = MatchModel(
                    match_id=m_id,
                    player_id=player_id,
                    start_time=m.get("start_time", 0),
                    hero_id=m.get("hero_id"),
                    player_slot=m.get("player_slot"),
                    radiant_win=m.get("radiant_win"),
                    kills=m.get("kills", 0),
                    deaths=m.get("deaths", 0),
                    assists=m.get("assists", 0),
                    tower_damage=m.get("tower_damage", 0),
                    hero_damage=m.get("hero_damage", 0),
                    gold_per_min=m.get("gold_per_min", 0),
                    duration=m.get("duration", 0),
                    lane_role=m.get("lane_role", 0),
                    item_0=m.get("item_0", 0),
                    item_1=m.get("item_1", 0),
                    item_2=m.get("item_2", 0),
                    item_3=m.get("item_3", 0),
                    item_4=m.get("item_4", 0),
                    item_5=m.get("item_5", 0),
                    raw_json=json.dumps(m, default=str),
                    last_accessed_at=now
                )
                db.merge(match_obj)
                new_matches_count += 1

        # Fetch and sync profile metadata
        profile_data = cls.fetch_opendota_profile(player_id)
        personaname = "Unknown Player"
        avatar_url = None
        
        if profile_data and isinstance(profile_data, dict):
            prof = profile_data.get("profile", {})
            if isinstance(prof, dict):
                personaname = prof.get("personaname") or personaname
                avatar_url = prof.get("avatarfull") or prof.get("avatar")

        profile_obj = db.query(PlayerProfileModel).filter_by(player_id=player_id).first()
        if not profile_obj:
            profile_obj = PlayerProfileModel(
                player_id=player_id,
                personaname=personaname,
                avatar_url=avatar_url,
                is_public=True,
                last_synced_at=now,
                last_accessed_at=now
            )
            db.add(profile_obj)
        else:
            if personaname != "Unknown Player":
                profile_obj.personaname = personaname
            if avatar_url:
                profile_obj.avatar_url = avatar_url
            profile_obj.last_synced_at = now
            profile_obj.last_accessed_at = now

        db.commit()

        total_matches = db.query(MatchModel).filter_by(player_id=player_id).count()

        logger.info(
            f"Synced player {player_id} ({personaname}): "
            f"new={new_matches_count}, total={total_matches}"
        )

        return PlayerSyncResponse(
            player_id=player_id,
            player_name=personaname,
            total_matches=total_matches,
            new_matches_synced=new_matches_count,
            last_synced_at=now,
            message=f"Successfully synced {new_matches_count} new matches."
        )

    @classmethod
    def get_player_matches(cls, db: Session, player_id: int) -> PlayerMatchHistoryResponse:
        """
        Retrieves cached player profile and match history.
        Updates last_accessed_at timestamp to mark player data as active in LRU cache.
        """
        now = utc_now()
        
        profile = db.query(PlayerProfileModel).filter_by(player_id=player_id).first()
        if profile:
            profile.last_accessed_at = now
            db.commit()

        matches = db.query(MatchModel).filter_by(player_id=player_id).order_by(MatchModel.start_time.asc()).all()

        if matches:
            # Touch last_accessed_at for queried matches
            for m in matches:
                m.last_accessed_at = now
            db.commit()

        match_schemas = [MatchSchema.model_validate(m) for m in matches]
        profile_schema = PlayerProfileSchema.model_validate(profile) if profile else None

        return PlayerMatchHistoryResponse(
            player_id=player_id,
            profile=profile_schema,
            total_cached_matches=len(match_schemas),
            matches=match_schemas
        )
