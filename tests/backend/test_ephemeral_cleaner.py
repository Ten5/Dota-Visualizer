import unittest
import os
import tempfile
import time
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import src.backend.models  # noqa: F401
from src.backend.models.base import Base, utc_now
from src.backend.models.renders import RenderJobModel
from src.backend.services.ephemeral_cleaner import EphemeralCleaner
from src.backend.main import app
from src.backend.core.database import get_db

class TestEphemeralCleaner(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Temporary test storage directory
        self.test_dir = tempfile.mkdtemp()

        def override_get_db():
            try:
                yield self.db
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_purge_expired_media_files_and_db_status(self):
        # 1. Create a dummy file on disk
        dummy_file = os.path.join(self.test_dir, "test_job_1.mp4")
        with open(dummy_file, "wb") as f:
            f.write(b"dummy mp4 video bytes")

        # 2. Insert an expired job record into DB
        expired_job = RenderJobModel(
            job_id="test_job_1",
            player_id=70388657,
            metric="Hero Versatility",
            status="COMPLETED",
            progress=100,
            file_path=dummy_file,
            video_url="/api/v1/render/media/test_job_1.mp4",
            expires_at=utc_now() - timedelta(minutes=10)
        )
        self.db.add(expired_job)
        self.db.commit()

        # 3. Execute purge
        result = EphemeralCleaner.purge_expired_media(self.db, ttl_seconds=3600)

        # 4. Verify file was deleted and status updated
        self.assertFalse(os.path.exists(dummy_file))

        refreshed_job = self.db.query(RenderJobModel).filter_by(job_id="test_job_1").first()
        self.assertEqual(refreshed_job.status, "EXPIRED")
        self.assertIsNone(refreshed_job.video_url)

    def test_ephemeral_purge_admin_api_endpoint(self):
        response = self.client.post("/api/v1/admin/ephemeral-purge?ttl_seconds=3600")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("purged_jobs_count", data)

if __name__ == "__main__":
    unittest.main()
