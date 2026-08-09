import unittest
from src.backend.core.config import Settings
from src.backend.core.logging import setup_logging, get_logger

class TestBackendConfig(unittest.TestCase):
    def test_default_settings(self):
        settings = Settings()
        self.assertEqual(settings.PROJECT_NAME, "Dota 2 Visualizer API")
        self.assertEqual(settings.API_V1_STR, "/api/v1")
        self.assertEqual(settings.EPHEMERAL_TTL_SECONDS, 3600)
        self.assertEqual(settings.LRU_INACTIVE_DAYS, 90)

    def test_logging_setup(self):
        setup_logging()
        logger = get_logger("test.logger")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test.logger")

if __name__ == "__main__":
    unittest.main()
