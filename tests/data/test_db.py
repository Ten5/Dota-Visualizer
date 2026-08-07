import unittest
import os
import tempfile
from PIL import Image
from src.data.db import DotaDB

class TestDotaDB(unittest.TestCase):

    def setUp(self):
        self.temp_db_path = tempfile.mktemp(suffix=".db")
        self.original_db_path = DotaDB.DB_PATH
        DotaDB.DB_PATH = self.temp_db_path

    def tearDown(self):
        DotaDB.DB_PATH = self.original_db_path
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_save_and_get_matches(self):
        """Test saving and retrieving matches from SQLite."""
        matches = [
            {'match_id': 100, 'start_time': 1500000000, 'hero_id': 1},
            {'match_id': 200, 'start_time': 1500001000, 'hero_id': 2}
        ]
        DotaDB.save_matches(999, matches)

        cached = DotaDB.get_matches(999)
        self.assertEqual(len(cached), 2)
        self.assertEqual(cached[0]['match_id'], 100)
        self.assertEqual(cached[1]['match_id'], 200)

        latest_id = DotaDB.get_latest_match_id(999)
        self.assertEqual(latest_id, 200)

    def test_save_and_get_profile(self):
        """Test saving and loading player profile and avatar BLOB."""
        img = Image.new("RGBA", (50, 50), color="blue")
        DotaDB.save_profile(999, "TestDotaPlayer", img)

        profile = DotaDB.get_profile(999)
        self.assertIsNotNone(profile)
        self.assertEqual(profile['name'], "TestDotaPlayer")
        self.assertIsNotNone(profile['avatar'])
        self.assertEqual(profile['avatar'].size, (50, 50))

if __name__ == '__main__':
    unittest.main()
