import unittest
import pandas as pd
from unittest.mock import patch
from src.data.strategies import (
    MatchesPlayedStrategy, 
    WinsStrategy, 
    WinRateStrategy,
    ItemRaceStrategy
)
from tests.test_utils import (
    create_sample_matches,
    assert_dataframe_last_row
)


class StrategyTestBase(unittest.TestCase):
    """Base class for strategy tests with common fixtures."""

    def setUp(self):
        """Setup common test data for all strategy tests."""
        self.mock_matches = create_sample_matches()
        self.hero_map = {1: 'Anti-Mage', 2: 'Axe'}
    
    def _process_and_get_last_row(self, strategy):
        """Helper to process matches and return the last row of results."""
        df, year = strategy.process(self.mock_matches, self.hero_map)
        return df.iloc[-1]


class TestMatchesPlayedStrategy(StrategyTestBase):
    """Tests for MatchesPlayedStrategy."""

    def test_matches_played_count(self):
        """Test that matches are counted correctly per hero."""
        strategy = MatchesPlayedStrategy()
        df, year = strategy.process(self.mock_matches, self.hero_map)
        
        assert_dataframe_last_row(self, df, {
            'Anti-Mage': 2,  # Played in matches 1 and 2
            'Axe': 1         # Played in match 3
        })


class TestWinsStrategy(StrategyTestBase):
    """Tests for WinsStrategy."""

    def test_wins_logic(self):
        """Test win/loss detection based on player_slot and radiant_win."""
        strategy = WinsStrategy()
        df, year = strategy.process(self.mock_matches, self.hero_map)
        
        # Match 1: Radiant Win, Player Radiant (slot 0) -> WIN
        # Match 2: Radiant Win, Player Dire (slot 128) -> LOSS
        # Match 3: Dire Win, Player Dire (slot 129) -> WIN
        assert_dataframe_last_row(self, df, {
            'Anti-Mage': 1,  # 1 Win, 1 Loss = 1 total win
            'Axe': 1         # 1 Win
        })


class TestWinRateStrategy(StrategyTestBase):
    """Tests for WinRateStrategy."""

    def test_win_rate_calculation(self):
        """Test that win rates are calculated correctly as percentages."""
        strategy = WinRateStrategy()
        df, year = strategy.process(self.mock_matches, self.hero_map)
        
        assert_dataframe_last_row(self, df, {
            'Anti-Mage': 50.0,   # 1 win / 2 games = 50%
            'Axe': 100.0         # 1 win / 1 game = 100%
        })


class TestItemRaceStrategy(StrategyTestBase):
    """Tests for ItemRaceStrategy."""

    @patch('src.data.strategies.DotaAPI.get_item_map')
    def test_item_counting(self, mock_item_map):
        """Test that items are counted correctly across matches."""
        mock_item_map.return_value = {10: 'Blink Dagger', 20: 'Black King Bar'}
        
        strategy = ItemRaceStrategy()
        df, year = strategy.process(self.mock_matches, self.hero_map)
        
        # Blink Dagger in matches 1 and 2, BKB in match 3
        assert_dataframe_last_row(self, df, {
            'Blink Dagger': 2,
            'Black King Bar': 1
        })

if __name__ == '__main__':
    unittest.main()