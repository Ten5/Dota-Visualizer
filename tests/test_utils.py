"""
Test utilities and helpers for the Dota Visualizer test suite.

This module provides common fixtures, mock helpers, and utility functions
to reduce code duplication across test files.
"""

from unittest.mock import MagicMock
import pandas as pd


# ========================================
# Mock Response Builders
# ========================================

def create_mock_response(json_data):
    """Create a mock requests.Response object with JSON data."""
    mock_response = MagicMock()
    mock_response.json.return_value = json_data
    return mock_response


def create_hero_list_response(heroes):
    """
    Create a mock hero list API response.
    
    Args:
        heroes: List of tuples (id, name) or dicts with 'id' and 'localized_name'
    
    Returns:
        Mock response object
    """
    if heroes and isinstance(heroes[0], tuple):
        hero_dicts = [{'id': h[0], 'localized_name': h[1]} for h in heroes]
    else:
        hero_dicts = heroes
    
    return create_mock_response(hero_dicts)


def create_profile_response(name, avatar_url=None):
    """Create a mock player profile API response."""
    profile_data = {'profile': {'personaname': name}}
    if avatar_url:
        profile_data['profile']['avatarfull'] = avatar_url
    
    return create_mock_response(profile_data)


# ========================================
# Match Data Fixtures
# ========================================

def create_match(match_id, start_time, hero_id, player_slot=0, 
                 radiant_win=True, **extra_fields):
    """
    Create a match dictionary with common fields.
    
    Args:
        match_id: Unique match identifier
        start_time: Unix timestamp
        hero_id: Hero ID played
        player_slot: Player slot (0-127 = Radiant, 128+ = Dire)
        radiant_win: Whether Radiant team won
        **extra_fields: Additional match fields (kills, deaths, items, etc.)
    
    Returns:
        Match dictionary
    """
    match = {
        'match_id': match_id,
        'start_time': start_time,
        'hero_id': hero_id,
        'player_slot': player_slot,
        'radiant_win': radiant_win,
    }
    match.update(extra_fields)
    return match


def create_match_with_items(match_id, start_time, hero_id, items, 
                            player_slot=0, radiant_win=True):
    """
    Create a match with item slots populated.
    
    Args:
        match_id: Unique match identifier
        start_time: Unix timestamp
        hero_id: Hero ID played
        items: List of up to 6 item IDs
        player_slot: Player slot
        radiant_win: Whether Radiant team won
    
    Returns:
        Match dictionary with item_0 through item_5 fields
    """
    item_fields = {f'item_{i}': items[i] if i < len(items) else 0 
                   for i in range(6)}
    
    return create_match(match_id, start_time, hero_id, player_slot, 
                       radiant_win, **item_fields)


def create_sample_matches():
    """
    Create a standard set of test matches.
    
    Returns three matches:
    - Match 1: 2020-01-01, Hero 1 (Radiant), WIN
    - Match 2: 2020-02-01, Hero 1 (Dire), LOSS  
    - Match 3: 2020-02-02, Hero 2 (Dire), WIN
    """
    return [
        create_match_with_items(
            match_id=1,
            start_time=1577836800,  # 2020-01-01
            hero_id=1,
            items=[10],
            player_slot=0,
            radiant_win=True
        ),
        create_match_with_items(
            match_id=2,
            start_time=1580515200,  # 2020-02-01
            hero_id=1,
            items=[10],
            player_slot=128,
            radiant_win=True
        ),
        create_match_with_items(
            match_id=3,
            start_time=1580601600,  # 2020-02-02
            hero_id=2,
            items=[20],
            player_slot=129,
            radiant_win=False
        )
    ]


# ========================================
# DataFrame Helpers
# ========================================

def create_test_dataframe(data, dates):
    """
    Create a pandas DataFrame with datetime index.
    
    Args:
        data: Dictionary of column_name: values
        dates: List of date strings (YYYY-MM-DD format)
    
    Returns:
        pandas DataFrame
    """
    index = pd.to_datetime(dates)
    return pd.DataFrame(data, index=index)


def assert_dataframe_last_row(test_case, df, expected_values):
    """
    Assert values in the last row of a DataFrame.
    
    Args:
        test_case: unittest.TestCase instance
        df: pandas DataFrame
        expected_values: Dictionary of column_name: expected_value
    """
    last_row = df.iloc[-1]
    for column, expected_value in expected_values.items():
        test_case.assertEqual(
            last_row[column], 
            expected_value,
            f"Column '{column}' mismatch"
        )


# ========================================
# Mock Setup Helpers
# ========================================

class MockDotaAPI:
    """Helper class to create consistent DotaAPI mocks."""
    
    @staticmethod
    def setup_basic_mocks(mock_api_class, matches=None, heroes=None, profile=None):
        """
        Setup standard DotaAPI mock responses.
        
        Args:
            mock_api_class: Mocked DotaAPI class
            matches: List of match dictionaries (default: sample matches)
            heroes: Dict of hero_id: name (default: {1: 'Pudge'})
            profile: Dict with 'name' and 'avatar' (default: {'name': 'TestPlayer'})
        """
        if matches is None:
            matches = create_sample_matches()
        if heroes is None:
            heroes = {1: 'Pudge', 2: 'Axe'}
        if profile is None:
            profile = {'name': 'TestPlayer', 'avatar': None}
        
        mock_api_class.fetch_all_matches.return_value = matches
        mock_api_class.get_hero_map.return_value = heroes
        mock_api_class.get_player_profile.return_value = profile
        
        return mock_api_class


# ========================================
# Pagination Helpers
# ========================================

def create_paginated_responses(page_sizes):
    """
    Create mock responses for pagination testing.
    
    Args:
        page_sizes: List of integers representing matches per page
    
    Returns:
        List of mock response objects
    """
    responses = []
    match_id_offset = 0
    
    for size in page_sizes:
        page_data = [
            {'match_id': match_id_offset + i, 'start_time': 1000 * (i + 1)}
            for i in range(size)
        ]
        responses.append(MagicMock(json=lambda data=page_data: data))
        match_id_offset += size
    
    return responses


# ========================================
# Assertion Helpers
# ========================================

def assert_mock_called_with_kwargs(test_case, mock_obj, **expected_kwargs):
    """
    Assert that a mock was called with specific keyword arguments.
    
    Args:
        test_case: unittest.TestCase instance
        mock_obj: Mock object to check
        **expected_kwargs: Expected keyword arguments
    """
    test_case.assertTrue(mock_obj.called, f"{mock_obj} was not called")
    
    _, actual_kwargs = mock_obj.call_args
    for key, expected_value in expected_kwargs.items():
        test_case.assertIn(key, actual_kwargs, f"Missing kwarg: {key}")
        test_case.assertEqual(
            actual_kwargs[key], 
            expected_value,
            f"Kwarg '{key}' mismatch"
        )


def assert_cache_hit(test_case, mock_get):
    """
    Assert that a cached API call didn't trigger a new request.
    
    Args:
        test_case: unittest.TestCase instance
        mock_get: Mocked requests.get function
    """
    initial_call_count = mock_get.call_count
    test_case.assertEqual(
        mock_get.call_count,
        initial_call_count,
        "Cache miss: API was called again"
    )
