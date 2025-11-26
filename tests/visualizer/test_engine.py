import unittest
from unittest.mock import patch, MagicMock
from src.visualizer.engine import VideoEngine
from tests.test_utils import (
    create_test_dataframe,
    assert_mock_called_with_kwargs
)


class TestRenderRace(unittest.TestCase):
    """Tests for video rendering functionality."""

    def setUp(self):
        """Setup common test data for rendering tests."""
        self.test_df = create_test_dataframe(
            data={'Anti-Mage': [1, 2], 'Axe': [0, 1]},
            dates=['2020-01-31', '2020-02-29']
        )
        self.output_file = "test_output.mp4"
        self.title = "Test Title"

    @patch('src.visualizer.engine.bcr.bar_chart_race')
    @patch('src.visualizer.engine.plt')
    def test_render_calls_library_with_settings(self, mock_plt, mock_bcr):
        """Ensure render_race passes dynamic quality settings correctly"""
        
        # Fix mock unpacking for subplots
        mock_plt.subplots.return_value = (MagicMock(), MagicMock())
        
        # --- TEST: High Quality Settings ---
        VideoEngine.render_race(
            self.test_df, self.output_file, self.title, 
            steps_per_period=50, 
            period_length=2500, 
            dpi=120
        )

        # Verify bar_chart_race was called
        self.assertTrue(mock_bcr.called)

        # Verify correct parameters
        assert_mock_called_with_kwargs(
            self,   
            mock_bcr,
            filename=self.output_file,
            title=self.title,
            n_bars=20,
            steps_per_period=50,
            period_length=2500
        )
        
        # Assert DPI passed to Matplotlib
        _, plt_kwargs = mock_plt.subplots.call_args
        self.assertEqual(plt_kwargs['dpi'], 120)

    @patch('src.visualizer.engine.bcr.bar_chart_race')
    @patch('src.visualizer.engine.plt')
    def test_render_calls_bar_chart_race(self, mock_plt, mock_bcr):
        """Test that render_race correctly calls bar_chart_race library."""
        # Setup matplotlib mocks
        mock_plt.subplots.return_value = (MagicMock(), MagicMock())
        
        VideoEngine.render_race(self.test_df, self.output_file, self.title)
        
        # Verify bar_chart_race was called
        self.assertTrue(mock_bcr.called)
        
        # Verify correct parameters
        assert_mock_called_with_kwargs(
            self,   
            mock_bcr,
            filename=self.output_file,
            title=self.title,
            n_bars=20
        )
    
    @patch('src.visualizer.engine.bcr.bar_chart_race')
    @patch('src.visualizer.engine.plt')
    def test_render_uses_dark_theme(self, mock_plt, mock_bcr):
        """Test that dark background theme is applied."""
        mock_plt.subplots.return_value = (MagicMock(), MagicMock())
        
        VideoEngine.render_race(self.test_df, self.output_file, self.title)
        
        mock_plt.style.use.assert_called_with('dark_background')


class TestAddAudio(unittest.TestCase):
    """Tests for audio integration functionality."""

    @patch('src.visualizer.engine.VideoFileClip')
    @patch('src.visualizer.engine.concatenate_videoclips')
    def test_add_audio_loads_video(self, mock_concat, mock_clip):
        """Test that video file is loaded correctly."""
        mock_video = MagicMock()
        mock_video.duration = 10
        mock_clip.return_value = mock_video
        
        VideoEngine.add_audio("in.mp4", "out.mp4", music_dir="tests/mock_music")
        
        mock_clip.assert_called_with("in.mp4")
    
    @patch('src.visualizer.engine.VideoFileClip')
    @patch('src.visualizer.engine.concatenate_videoclips')
    def test_add_audio_creates_buffer(self, mock_concat, mock_clip):
        """Test that audio concatenation/buffering is triggered."""
        mock_video = MagicMock()
        mock_video.duration = 10
        mock_clip.return_value = mock_video
        
        VideoEngine.add_audio("in.mp4", "out.mp4", music_dir="tests/mock_music")
        
        mock_concat.assert_called()

if __name__ == '__main__':
    unittest.main()