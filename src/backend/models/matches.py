from sqlalchemy import Column, BigInteger, Integer, Boolean, Text, DateTime, String, LargeBinary, Index
from src.backend.models.base import Base, TimestampMixin, utc_now

class MatchModel(Base, TimestampMixin):
    __tablename__ = "matches"

    match_id = Column(BigInteger, primary_key=True, index=True)
    player_id = Column(BigInteger, nullable=False, index=True)
    start_time = Column(BigInteger, nullable=False, index=True)
    hero_id = Column(Integer, nullable=True)
    player_slot = Column(Integer, nullable=True)
    radiant_win = Column(Boolean, nullable=True)
    
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    tower_damage = Column(Integer, default=0)
    hero_damage = Column(Integer, default=0)
    gold_per_min = Column(Integer, default=0)
    duration = Column(Integer, default=0)
    lane_role = Column(Integer, default=0)
    
    item_0 = Column(Integer, default=0)
    item_1 = Column(Integer, default=0)
    item_2 = Column(Integer, default=0)
    item_3 = Column(Integer, default=0)
    item_4 = Column(Integer, default=0)
    item_5 = Column(Integer, default=0)
    
    # Raw JSON payload retention for future strategy extensions
    raw_json = Column(Text, nullable=True)
    
    # Timestamp for 90-day LRU cache pruning engine
    last_accessed_at = Column(DateTime, default=utc_now, nullable=False, index=True)

    __table_args__ = (
        Index("idx_matches_player_time", "player_id", "start_time"),
        Index("idx_matches_player_access", "player_id", "last_accessed_at"),
    )

class PlayerProfileModel(Base, TimestampMixin):
    __tablename__ = "profiles"

    player_id = Column(BigInteger, primary_key=True, index=True)
    personaname = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    avatar_blob = Column(LargeBinary, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    
    last_synced_at = Column(DateTime, default=utc_now, nullable=False)
    last_accessed_at = Column(DateTime, default=utc_now, nullable=False, index=True)
