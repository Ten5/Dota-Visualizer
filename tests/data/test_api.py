import unittest
import requests
from unittest.mock import patch, MagicMock
from src.data.api import DotaAPI
from tests.test_utils import (
    create_hero_list_response,
    create_profile_response,
    create_paginated_responses,
    create_mock_response
)


class DotaAPITestBase(unittest.TestCase):
    """Base test class with common setup for DotaAPI tests."""
    
    def setUp(self):
        """Clear all caches before each test to ensure isolation."""
        self._clear_api_cache()
    
    def _clear_api_cache(self):
        """Helper to clear all DotaAPI caches."""
        DotaAPI._match_cache = {}
        DotaAPI._hero_map_cache = None
        DotaAPI._profile_cache = {}


class TestHeroMap(DotaAPITestBase):
    """Tests for hero map fetching and caching."""

    @patch('src.data.api.requests.get')
    def test_get_hero_map_success(self, mock_get):
        """Test successful hero map retrieval."""
        heroes = [(1, 'Anti-Mage'), (2, 'Axe')]
        mock_get.return_value = create_hero_list_response(heroes)

        result = DotaAPI.get_hero_map()
        
        self.assertEqual(result[1], 'Anti-Mage')
        self.assertEqual(result[2], 'Axe')
        self.assertEqual(len(result), 2)
    
    @patch('src.data.api.requests.get')
    def test_get_hero_map_caching(self, mock_get):
        """Test that hero map is cached and not re-fetched."""
        heroes = [(1, 'Anti-Mage'), (2, 'Axe')]
        mock_get.return_value = create_hero_list_response(heroes)

        # First call
        DotaAPI.get_hero_map()
        # Second call should use cache
        DotaAPI.get_hero_map()
        
        mock_get.assert_called_once()

    @patch('src.data.api.requests.get')
    def test_get_hero_map_malformed_data(self, mock_get):
        """Test handling of malformed API response."""
        # API returns dict instead of list
        mock_get.return_value = create_mock_response({'error': 'rate limit exceeded'})
        
        result = DotaAPI.get_hero_map()
        
        self.assertEqual(result, {})


class TestMatchFetching(DotaAPITestBase):
    """Tests for match data fetching."""

    @patch('src.data.api.requests.get')
    def test_fetch_matches_pagination(self, mock_get):
        """Test correct handling of paginated match data."""
        # Simulate 2 pages: 1000 matches + 50 matches
        mock_get.side_effect = create_paginated_responses([1000, 50])

        matches = DotaAPI.fetch_all_matches(12345)
        
        self.assertEqual(len(matches), 1050)
        self.assertEqual(mock_get.call_count, 2)

    @patch('src.data.api.requests.get')
    def test_fetch_matches_api_failure(self, mock_get):
        """Test graceful handling of API errors."""
        mock_get.side_effect = requests.exceptions.RequestException("API Down")
        
        matches = DotaAPI.fetch_all_matches(12345)
        
        self.assertEqual(matches, [])


class TestPlayerProfile(DotaAPITestBase):
    """Tests for player profile fetching."""

    @patch('src.data.api.requests.get')
    def test_get_player_profile_with_avatar(self, mock_get):
        """Test profile retrieval with avatar URL."""
        mock_get.return_value = create_profile_response(
            'Dendi', 
            'http://fake.url/img.png'
        )

        with patch('src.data.api.Image.open'):
            profile = DotaAPI.get_player_profile(999)
            
            self.assertEqual(profile['name'], 'Dendi')
            self.assertTrue(mock_get.called)

if __name__ == '__main__':
    unittest.main()