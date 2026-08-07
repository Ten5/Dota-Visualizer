import unittest
from unittest.mock import patch, MagicMock

# Setup fake customtkinter before importing app
from tests.ui.test_fixtures import (
    setup_fake_customtkinter,
    create_mock_app_widgets
)
from tests.test_utils import MockDotaAPI

# Initialize fake customtkinter
setup_fake_customtkinter()

# Now safe to import app
from src.ui.app import DotaRaceApp

class AppTestBase(unittest.TestCase):
    """Base test class for app logic tests."""
    
    def setUp(self):
        """Setup app instance with mocked widgets."""
        self.app = DotaRaceApp()
        self.mocks = create_mock_app_widgets(self.app)
        # Mock the selection var
        self.app.quality_var = MagicMock()
        self.app.quality_var.get.return_value = "Draft (Fast)"


class TestGenerateWorkflow(AppTestBase):
    """Tests for the video generation workflow."""

    def test_successful_generation_flow(self):
        """Test a complete successful video generation workflow."""
        with patch('src.ui.app.DotaAPI') as MockAPI, \
             patch('src.ui.app.VideoEngine') as MockEngine, \
             patch('src.ui.app.DotaAPI.download_hero_images') as MockDownload:
            
            # Setup API mocks
            MockDotaAPI.setup_basic_mocks(
                MockAPI,
                matches=[
                    {'match_id': 1, 'start_time': 1600000000, 'hero_id': 1, 'player_slot': 0, 'radiant_win': True},
                    {'match_id': 2, 'start_time': 1605000000, 'hero_id': 1, 'player_slot': 0, 'radiant_win': True}
                ],
                heroes={1: 'Pudge'},
                profile={'name': 'Dendi', 'avatar': None}
            )

            test_settings = {"steps": 10, "period": 500, "dpi": 72}
            self.app.run_process("12345", "Matches Played", test_settings)
            
            # Verify API calls
            MockAPI.fetch_all_matches.assert_called()
            MockDownload.assert_called()
            
            # Verify rendering
            self.assertTrue(MockEngine.render_race.called)
            _, kwargs = MockEngine.render_race.call_args
            self.assertEqual(kwargs['steps_per_period'], 10) # Should match test_settings
            self.assertEqual(kwargs['dpi'], 72)
            self.assertIn("Dendi", kwargs['title'])

    def test_quality_selection_logic(self):
        """Test that the UI selects the correct dictionary from the presets"""
        
        # We mock on_generate (the button click)
        # But on_generate starts a thread, which is hard to test.
        # Instead, let's just verify the dictionary lookups work.
        
        # 1. User selects "Draft"
        selected_key = "Draft (Fast)"
        result = self.app.quality_presets[selected_key]
        
        self.assertEqual(result['steps'], 10)
        self.assertEqual(result['dpi'], 80)
        
        # 2. User selects "High"
        selected_key = "High (Slow)"
        result = self.app.quality_presets[selected_key]
        
        self.assertEqual(result['steps'], 40)
        self.assertEqual(result['dpi'], 120)

    def test_no_matches_error_handling(self):
        """Test proper error handling when no matches are found."""
        with patch('src.ui.app.DotaAPI') as MockAPI:
            MockAPI.fetch_all_matches.return_value = []

            test_settings = {"steps": 10, "period": 500, "dpi": 72}
            self.app.run_process("999", "Matches Played", test_settings)
            
            # Verify error is logged
            log_calls = self.mocks['log_box'].insert.call_args_list
            all_text = " ".join([str(call.args) for call in log_calls])
            self.assertTrue(
                "No matches found" in all_text or "Error" in all_text,
                f"Expected error message in logs"
            )

class TestVideoActions(AppTestBase):
    """Tests for video launcher and management buttons."""

    @patch('src.ui.app.open_file_or_folder')
    def test_open_folder_action(self, mock_open):
        """Test that open folder triggers file launcher."""
        self.app.on_open_folder()
        mock_open.assert_called_with("output")

    @patch('src.ui.app.open_file_or_folder')
    @patch('glob.glob')
    def test_play_latest_video_action(self, mock_glob, mock_open):
        """Test playing latest video."""
        mock_glob.return_value = ["output/Dendi_KDA.mp4"]
        with patch('os.path.getmtime', return_value=100):
            self.app.on_play_latest()
            mock_open.assert_called_with("output/Dendi_KDA.mp4")

    @patch('src.ui.app.messagebox.askyesno', return_value=True)
    @patch('glob.glob')
    @patch('os.remove')
    def test_delete_videos_action(self, mock_remove, mock_glob, mock_confirm):
        """Test video deletion action."""
        mock_glob.return_value = ["output/video1.mp4", "output/video2.mp4"]
        self.app.on_delete_videos()
        self.assertEqual(mock_remove.call_count, 2)

if __name__ == '__main__':
    unittest.main()