import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.backend.models  # noqa: F401
from src.backend.main import app
from src.backend.core.database import Base, get_db
from src.backend.services.auth import JWTManager, SteamAuthService

class TestKeysAPI(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Create user & auth token
        self.user = SteamAuthService.authenticate_or_create_user(self.db, "76561197960265728")
        self.token = JWTManager.create_access_token({"sub": str(self.user.id)})
        self.headers = {"Authorization": f"Bearer {self.token}"}

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

    def test_api_keys_crud_flow(self):
        # 1. Create API Key
        create_resp = self.client.post(
            "/api/v1/keys",
            json={"name": "CLI App Key"},
            headers=self.headers
        )
        self.assertEqual(create_resp.status_code, 201)
        key_data = create_resp.json()
        self.assertEqual(key_data["name"], "CLI App Key")
        self.assertTrue(key_data["key"].startswith("dota_live_"))

        key_id = key_data["id"]

        # 2. List API Keys
        list_resp = self.client.get("/api/v1/keys", headers=self.headers)
        self.assertEqual(list_resp.status_code, 200)
        keys_list = list_resp.json()
        self.assertEqual(len(keys_list), 1)

        # 3. Revoke API Key
        del_resp = self.client.delete(f"/api/v1/keys/{key_id}", headers=self.headers)
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json()["status"], "success")

        # 4. List after Revocation
        list_resp_after = self.client.get("/api/v1/keys", headers=self.headers)
        self.assertEqual(len(list_resp_after.json()), 0)

if __name__ == "__main__":
    unittest.main()
