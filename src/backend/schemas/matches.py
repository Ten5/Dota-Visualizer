from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class MatchSchema(BaseModel):
    match_id: int
    player_id: int
    start_time: int
    hero_id: Optional[int] = None
    player_slot: Optional[int] = None
    radiant_win: Optional[bool] = None
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    tower_damage: int = 0
    hero_damage: int = 0
    gold_per_min: int = 0
    duration: int = 0
    lane_role: int = 0
    item_0: int = 0
    item_1: int = 0
    item_2: int = 0
    item_3: int = 0
    item_4: int = 0
    item_5: int = 0
    
    class Config:
        from_attributes = True

class PlayerProfileSchema(BaseModel):
    player_id: int
    personaname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_public: bool = True
    last_synced_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PlayerSyncResponse(BaseModel):
    player_id: int
    player_name: Optional[str] = None
    total_matches: int
    new_matches_synced: int
    last_synced_at: datetime
    message: str = "Player matches synchronized successfully."

class PlayerMatchHistoryResponse(BaseModel):
    player_id: int
    profile: Optional[PlayerProfileSchema] = None
    total_cached_matches: int
    matches: List[MatchSchema] = []
