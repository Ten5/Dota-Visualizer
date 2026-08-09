import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.backend.models  # noqa: F401
from src.backend.main import app
from src.backend.core.database import Base, get_db
from src.backend.services.ingestion import MatchIngestionService

MOCK_MATCHES = [
    {
        "match_id": 500,
        "player_slot": 0,
        "radiant_win": True,
        "duration": 1800,
        "start_time": 1700000000,
        "hero_id": 10,
        "kills": 12,
        "deaths": 3,
        "assists": 9,
    }
]

MOCK_PROFILE = {
    "profile": {
        "account_id": 70388657,
        "personaname": "Dendi",
        "avatarfull": "https://example.com/dendi.jpg"
    }
}

class TestPlayersAPI(unittest.TestCase):
    def setUp(self):
        # Set up shared multi-thread in-memory SQLite database for FastAPI TestClient
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)

        def override_get_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=self.engine)

    @patch.object(MatchIngestionService, "fetch_opendota_profile", return_value=MOCK_PROFILE)
    @patch.object(MatchIngestionService, "fetch_opendota_matches", return_value=MOCK_MATCHES)
    def test_sync_and_get_matches_flow(self, mock_matches, mock_profile):
        # 1. Trigger Sync Endpoint
        sync_resp = self.client.post("/api/v1/players/70388657/sync")
        self.assertEqual(sync_resp.status_code, 200)
        sync_data = sync_resp.json()
        self.assertEqual(sync_data["player_id"], 70388657)
        self.assertEqual(sync_data["player_name"], "Dendi")
        self.assertEqual(sync_data["new_matches_synced"], 1)

        # 2. Get Cached Matches Endpoint
        get_resp = self.client.get("/api/v1/players/70388657/matches")
        self.assertEqual(get_resp.status_code, 200)
        get_data = get_resp.json()
        self.assertEqual(get_data["player_id"], 70388657)
        self.assertEqual(get_data["total_cached_matches"], 1)
        self.assertEqual(get_data["matches"][0]["match_id"], 500)

    def test_lru_prune_endpoint(self):
        response = self.client.post("/api/v1/admin/lru-prune?days_inactive=90")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("pruned_matches", data)

if __name__ == "__main__":
    unittest.main()
