import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.models.base import Base
from src.backend.models.users import SteamUserModel, ApiKeyModel
from src.backend.services.security import ApiKeyService

class TestApiKeySecurityService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Create dummy user
        self.user = SteamUserModel(
            steam_id64="76561197960265728",
            steam_id32=70388657,
            display_name="TestDeveloper"
        )
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_generate_and_validate_api_key(self):
        # 1. Generate key
        key_res = ApiKeyService.generate_api_key(self.db, name="Prod Key", user_id=self.user.id)
        self.assertIsNotNone(key_res.key)
        self.assertTrue(key_res.key.startswith("dota_live_"))
        self.assertEqual(key_res.name, "Prod Key")

        raw_key = key_res.key

        # 2. Validate valid key
        validated_obj = ApiKeyService.validate_api_key(self.db, raw_key)
        self.assertIsNotNone(validated_obj)
        self.assertEqual(validated_obj.user_id, self.user.id)

        # 3. Validate invalid key
        invalid_obj = ApiKeyService.validate_api_key(self.db, "dota_live_invalid_key_string")
        self.assertIsNone(invalid_obj)

    def test_list_and_revoke_api_keys(self):
        key_res1 = ApiKeyService.generate_api_key(self.db, name="Key 1", user_id=self.user.id)
        key_res2 = ApiKeyService.generate_api_key(self.db, name="Key 2", user_id=self.user.id)

        keys_list = ApiKeyService.list_user_api_keys(self.db, user_id=self.user.id)
        self.assertEqual(len(keys_list), 2)
        self.assertIsNone(keys_list[0].key)  # Raw key is NOT returned on list

        # Revoke Key 1
        success = ApiKeyService.revoke_api_key(self.db, user_id=self.user.id, key_id=key_res1.id)
        self.assertTrue(success)

        # Validation should fail after revocation
        self.assertIsNone(ApiKeyService.validate_api_key(self.db, key_res1.key))

        # Remaining active keys count
        active_keys = ApiKeyService.list_user_api_keys(self.db, user_id=self.user.id)
        self.assertEqual(len(active_keys), 1)

if __name__ == "__main__":
    unittest.main()
