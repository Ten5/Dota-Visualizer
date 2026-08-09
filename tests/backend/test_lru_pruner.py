import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.models.base import Base, utc_now
from src.backend.models.matches import MatchModel, PlayerProfileModel
from src.backend.services.lru_pruner import LRUCachePruner

class TestLRUCachePruner(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_lru_cache_prune_inactive_matches(self):
        now = utc_now()
        recent_date = now - timedelta(days=10)
        stale_date = now - timedelta(days=100)

        # Active player (accessed 10 days ago)
        active_prof = PlayerProfileModel(player_id=1, personaname="ActivePlayer", last_accessed_at=recent_date)
        active_match = MatchModel(match_id=1001, player_id=1, start_time=1700000000, last_accessed_at=recent_date)

        # Inactive player (accessed 100 days ago)
        inactive_prof = PlayerProfileModel(player_id=2, personaname="InactivePlayer", last_accessed_at=stale_date)
        inactive_match = MatchModel(match_id=2001, player_id=2, start_time=1600000000, last_accessed_at=stale_date)

        self.db.add_all([active_prof, active_match, inactive_prof, inactive_match])
        self.db.commit()

        # Execute 90-day LRU Cache Pruning task
        res = LRUCachePruner.prune_inactive_matches(self.db, days_inactive=90)
        
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["pruned_matches"], 1)
        self.assertEqual(res["pruned_profiles"], 1)

        # Verify active player data remains
        remaining_matches = self.db.query(MatchModel).all()
        self.assertEqual(len(remaining_matches), 1)
        self.assertEqual(remaining_matches[0].match_id, 1001)

        remaining_profiles = self.db.query(PlayerProfileModel).all()
        self.assertEqual(len(remaining_profiles), 1)
        self.assertEqual(remaining_profiles[0].player_id, 1)

if __name__ == "__main__":
    unittest.main()
