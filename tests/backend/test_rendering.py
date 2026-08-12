import unittest
from unittest.mock import patch, MagicMock
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.models.base import Base
from src.backend.models.renders import RenderJobModel
from src.backend.models.matches import MatchModel
from src.backend.schemas.renders import RenderJobCreate
from src.backend.services.rendering import RenderService
from src.backend.worker import process_render_job

class TestRenderingService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    @patch("src.backend.services.rendering.RenderService._dispatch_render_task")
    def test_create_and_get_render_job(self, mock_dispatch):
        job_create = RenderJobCreate(
            player_id=70388657,
            metric="Hero Versatility",
            quality="Normal",
            aspect_ratio="9:16",
            theme="Midnight Cyberpunk"
        )
        res = RenderService.create_render_job(self.db, job_create)

        self.assertIsNotNone(res.job_id)
        self.assertEqual(res.player_id, 70388657)
        self.assertEqual(res.status, "PENDING")
        self.assertEqual(res.progress, 0)
        mock_dispatch.assert_called_once()

        # Query status
        status_res = RenderService.get_render_job_status(self.db, res.job_id)
        self.assertIsNotNone(status_res)
        self.assertEqual(status_res.status, "PENDING")
        self.assertEqual(status_res.progress, 0)

    @patch("src.visualizer.engine.VideoEngine.add_audio")
    @patch("src.visualizer.engine.VideoEngine.render_race")
    @patch("src.data.api.DotaAPI.get_hero_map", return_value={1: "Anti-Mage", 2: "Axe"})
    def test_process_render_job_success(self, mock_hero_map, mock_render_race, mock_add_audio):
        # Insert dummy matches across 2 distinct months
        match1 = MatchModel(
            match_id=999,
            player_id=70388657,
            start_time=1700000000,  # Nov 2023
            hero_id=1,
            raw_json=json.dumps({"match_id": 999, "start_time": 1700000000, "hero_id": 1})
        )
        match2 = MatchModel(
            match_id=1000,
            player_id=70388657,
            start_time=1703000000,  # Dec 2023
            hero_id=2,
            raw_json=json.dumps({"match_id": 1000, "start_time": 1703000000, "hero_id": 2})
        )
        job = RenderJobModel(
            job_id="job_test_123",
            player_id=70388657,
            metric="Hero Impact Score",
            status="PENDING",
            progress=0
        )
        self.db.add_all([match1, match2, job])
        self.db.commit()

        # Execute render processing
        process_render_job("job_test_123", self.db)

        saved_job = self.db.query(RenderJobModel).filter_by(job_id="job_test_123").first()
        self.assertEqual(saved_job.status, "COMPLETED")
        self.assertEqual(saved_job.progress, 100)
        self.assertIn("job_test_123.mp4", saved_job.video_url)
        self.assertIsNotNone(saved_job.expires_at)

if __name__ == "__main__":
    unittest.main()
