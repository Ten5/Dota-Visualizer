import unittest
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.models.base import Base
from src.backend.models.matches import MatchModel, PlayerProfileModel
from src.backend.models.users import SteamUserModel, ApiKeyModel
from src.backend.models.renders import RenderJobModel

class TestBackendModels(unittest.TestCase):
    def setUp(self):
        # Create an in-memory SQLite database for testing
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_match_model_crud(self):
        raw_data = {"match_id": 123456789, "kills": 15, "deaths": 2}
        match = MatchModel(
            match_id=123456789,
            player_id=70388657,
            start_time=1700000000,
            hero_id=1,
            kills=15,
            deaths=2,
            assists=10,
            raw_json=json.dumps(raw_data)
        )
        self.session.add(match)
        self.session.commit()

        saved_match = self.session.query(MatchModel).filter_by(match_id=123456789).first()
        self.assertIsNotNone(saved_match)
        self.assertEqual(saved_match.player_id, 70388657)
        self.assertEqual(saved_match.kills, 15)
        self.assertEqual(json.loads(saved_match.raw_json)["kills"], 15)
        self.assertIsNotNone(saved_match.last_accessed_at)

    def test_player_profile_model(self):
        profile = PlayerProfileModel(
            player_id=70388657,
            personaname="Dendi",
            avatar_url="https://example.com/avatar.jpg",
            is_public=True
        )
        self.session.add(profile)
        self.session.commit()

        saved_profile = self.session.query(PlayerProfileModel).filter_by(player_id=70388657).first()
        self.assertIsNotNone(saved_profile)
        self.assertEqual(saved_profile.personaname, "Dendi")
        self.assertTrue(saved_profile.is_public)

    def test_steam_user_and_api_key_relationship(self):
        user = SteamUserModel(
            steam_id64="76561197960265728",
            steam_id32=70388657,
            display_name="Dendi"
        )
        self.session.add(user)
        self.session.commit()

        api_key = ApiKeyModel(
            key_hash="hash_abc123",
            name="Default Key",
            user_id=user.id
        )
        self.session.add(api_key)
        self.session.commit()

        saved_user = self.session.query(SteamUserModel).filter_by(steam_id64="76561197960265728").first()
        self.assertIsNotNone(saved_user)
        self.assertEqual(len(saved_user.api_keys), 1)
        self.assertEqual(saved_user.api_keys[0].name, "Default Key")

    def test_render_job_model(self):
        render_job = RenderJobModel(
            job_id="job_uuid_12345",
            player_id=70388657,
            metric="Hero Versatility",
            status="PENDING",
            progress=0
        )
        self.session.add(render_job)
        self.session.commit()

        saved_job = self.session.query(RenderJobModel).filter_by(job_id="job_uuid_12345").first()
        self.assertIsNotNone(saved_job)
        self.assertEqual(saved_job.status, "PENDING")
        self.assertEqual(saved_job.metric, "Hero Versatility")

if __name__ == "__main__":
    unittest.main()
