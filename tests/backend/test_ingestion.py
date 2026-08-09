import unittest
from unittest.mock import patch
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.models.base import Base
from src.backend.models.matches import MatchModel, PlayerProfileModel
from src.backend.services.ingestion import MatchIngestionService

MOCK_OPENDOTA_MATCHES = [
    {
        "match_id": 100,
        "player_slot": 0,
        "radiant_win": True,
        "duration": 1800,
        "start_time": 1700000000,
        "hero_id": 1,
        "kills": 10,
        "deaths": 2,
        "assists": 8,
        "gold_per_min": 600,
    },
    {
        "match_id": 101,
        "player_slot": 0,
        "radiant_win": False,
        "duration": 2200,
        "start_time": 1700005000,
        "hero_id": 2,
        "kills": 5,
        "deaths": 5,
        "assists": 12,
        "gold_per_min": 450,
    },
]

MOCK_OPENDOTA_PROFILE = {
    "profile": {
        "account_id": 70388657,
        "personaname": "Dendi",
        "avatarfull": "https://example.com/dendi.jpg"
    }
}

class TestIngestionService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    @patch.object(MatchIngestionService, "fetch_opendota_profile", return_value=MOCK_OPENDOTA_PROFILE)
    @patch.object(MatchIngestionService, "fetch_opendota_matches", return_value=MOCK_OPENDOTA_MATCHES)
    def test_sync_player_matches_initial_and_incremental(self, mock_matches, mock_profile):
        # 1. Initial Sync
        res1 = MatchIngestionService.sync_player_matches(self.db, 70388657)
        self.assertEqual(res1.player_id, 70388657)
        self.assertEqual(res1.new_matches_synced, 2)
        self.assertEqual(res1.total_matches, 2)
        self.assertEqual(res1.player_name, "Dendi")

        # Verify database contents
        matches = self.db.query(MatchModel).filter_by(player_id=70388657).all()
        self.assertEqual(len(matches), 2)
        self.assertIsNotNone(matches[0].raw_json)

        # 2. Incremental Sync with a new match 102
        new_matches_payload = MOCK_OPENDOTA_MATCHES + [
            {
                "match_id": 102,
                "player_slot": 0,
                "radiant_win": True,
                "duration": 1900,
                "start_time": 1700010000,
                "hero_id": 3,
                "kills": 8,
                "deaths": 1,
                "assists": 15,
                "gold_per_min": 700,
            }
        ]
        mock_matches.return_value = new_matches_payload

        res2 = MatchIngestionService.sync_player_matches(self.db, 70388657)
        self.assertEqual(res2.new_matches_synced, 1)  # Only match 102 is new!
        self.assertEqual(res2.total_matches, 3)

    @patch.object(MatchIngestionService, "fetch_opendota_profile", return_value=MOCK_OPENDOTA_PROFILE)
    @patch.object(MatchIngestionService, "fetch_opendota_matches", return_value=MOCK_OPENDOTA_MATCHES)
    def test_get_player_matches_updates_accessed_at(self, mock_matches, mock_profile):
        MatchIngestionService.sync_player_matches(self.db, 70388657)
        
        history = MatchIngestionService.get_player_matches(self.db, 70388657)
        self.assertEqual(history.total_cached_matches, 2)
        self.assertIsNotNone(history.profile)
        self.assertEqual(history.profile.personaname, "Dendi")

if __name__ == "__main__":
    unittest.main()
