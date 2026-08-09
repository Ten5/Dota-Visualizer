import unittest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.backend.models  # noqa: F401
from src.backend.main import app
from src.backend.core.database import Base, get_db
from src.backend.services.auth import (
    steam_id64_to_32,
    JWTManager,
    SteamAuthService,
)

class TestAuthModule(unittest.TestCase):
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

    def test_steam_id_conversion(self):
        steam_id64 = "76561197960265728"
        steam_id32 = steam_id64_to_32(steam_id64)
        self.assertEqual(steam_id32, 70388657)

    def test_jwt_token_encoding_and_decoding(self):
        payload = {"sub": "1", "steam_id64": "76561197960265728", "role": "user"}
        token = JWTManager.create_access_token(payload)
        self.assertIsInstance(token, str)

        decoded = JWTManager.decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "1")
        self.assertEqual(decoded["steam_id64"], "76561197960265728")

        # Test expired token
        expired_token = JWTManager.create_access_token(payload, expires_delta=timedelta(seconds=-10))
        self.assertIsNone(JWTManager.decode_access_token(expired_token))

    def test_steam_login_url_generation(self):
        url = SteamAuthService.get_steam_login_url("http://localhost:3000/auth/callback")
        self.assertIn("steamcommunity.com/openid/login", url)
        self.assertIn("openid.mode=checkid_setup", url)

    def test_auth_api_endpoints_flow(self):
        # 1. GET /api/v1/auth/steam/login
        resp_login = self.client.get("/api/v1/auth/steam/login")
        self.assertEqual(resp_login.status_code, 200)
        self.assertIn("login_url", resp_login.json())

        # 2. GET /api/v1/auth/me without token -> 401
        resp_unauth = self.client.get("/api/v1/auth/me")
        self.assertEqual(resp_unauth.status_code, 401)

        # 3. GET /api/v1/auth/steam/callback (mock login)
        resp_callback = self.client.get("/api/v1/auth/steam/callback?mock_steam_id64=76561197960265728")
        self.assertEqual(resp_callback.status_code, 200)
        token_data = resp_callback.json()
        self.assertIn("access_token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")

        token = token_data["access_token"]

        # 4. GET /api/v1/auth/me with valid Bearer token -> 200 OK
        headers = {"Authorization": f"Bearer {token}"}
        resp_me = self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(resp_me.status_code, 200)
        user_data = resp_me.json()
        self.assertEqual(user_data["steam_id64"], "76561197960265728")
        self.assertEqual(user_data["steam_id32"], 70388657)

if __name__ == "__main__":
    unittest.main()
