import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.backend.models  # noqa: F401
from src.backend.main import app
from src.backend.core.database import Base, get_db

class TestRendersAPI(unittest.TestCase):
    def setUp(self):
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

    @patch("src.backend.services.rendering.RenderService._dispatch_render_task")
    def test_render_job_submission_and_polling_flow(self, mock_dispatch):
        # 1. Submit Render Job
        payload = {
            "player_id": 70388657,
            "metric": "Hero Versatility",
            "quality": "Normal",
            "aspect_ratio": "9:16",
            "theme": "Midnight Cyberpunk"
        }
        create_resp = self.client.post("/api/v1/render/jobs", json=payload)
        self.assertEqual(create_resp.status_code, 201)
        data = create_resp.json()
        self.assertIn("job_id", data)
        self.assertEqual(data["player_id"], 70388657)
        self.assertEqual(data["status"], "PENDING")

        job_id = data["job_id"]

        # 2. Poll Status
        poll_resp = self.client.get(f"/api/v1/render/jobs/{job_id}")
        self.assertEqual(poll_resp.status_code, 200)
        status_data = poll_resp.json()
        self.assertEqual(status_data["job_id"], job_id)
        self.assertEqual(status_data["status"], "PENDING")

        # 3. List Jobs for Player
        list_resp = self.client.get("/api/v1/render/jobs?player_id=70388657")
        self.assertEqual(list_resp.status_code, 200)
        jobs_list = list_resp.json()
        self.assertEqual(len(jobs_list), 1)

if __name__ == "__main__":
    unittest.main()
