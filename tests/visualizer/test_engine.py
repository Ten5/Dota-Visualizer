import unittest
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock
from src.visualizer.engine import VideoEngine, get_best_ffmpeg_codec
from tests.test_utils import create_test_dataframe

class TestOpenCVVideoEngine(unittest.TestCase):
    """Tests for native OpenCV VideoEngine rendering."""

    def setUp(self):
        self.test_df = create_test_dataframe(
            data={'Anti-Mage': [1, 2], 'Axe': [0, 1]},
            dates=['2020-01-31', '2020-02-29']
        )
        self.output_file = tempfile.mktemp(suffix=".mp4")
        self.title = "Dendi\nMatches Played"

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_codec_detection(self):
        """Test OS-specific hardware acceleration codec selection."""
        codec = get_best_ffmpeg_codec()
        self.assertIn(codec, ['h264_videotoolbox', 'libx264', 'h264_nvenc'])

    @patch('src.visualizer.engine.subprocess.Popen')
    def test_render_race_pipes_frames(self, mock_popen):
        """Test that OpenCV VideoEngine pipes frame bytes to FFmpeg stdin."""
        mock_proc = MagicMock()
        mock_proc.stdin = MagicMock()
        mock_popen.return_value = mock_proc

        progress_calls = []
        def on_progress(p): progress_calls.append(p)

        VideoEngine.render_race(
            self.test_df, 
            self.output_file, 
            self.title, 
            n_bars=2, 
            progress_callback=on_progress,
            steps_per_period=2
        )

        # Verify FFmpeg process was launched and frames written to stdin
        self.assertTrue(mock_popen.called)
        self.assertTrue(mock_proc.stdin.write.called)
        self.assertGreater(mock_proc.stdin.write.call_count, 0)
        self.assertGreater(len(progress_calls), 0)

class TestAddAudio(unittest.TestCase):
    """Tests for audio integration functionality."""

    @patch('src.visualizer.engine.afx')
    @patch('src.visualizer.engine.AudioFileClip')
    @patch('src.visualizer.engine.VideoFileClip')
    @patch('src.visualizer.engine.concatenate_videoclips')
    def test_add_audio_loads_video(self, mock_concat, mock_clip, mock_audio, mock_afx):
        """Test that video file is loaded correctly and audio is blended."""
        mock_video = MagicMock()
        mock_video.duration = 10
        mock_clip.return_value = mock_video
        mock_concat.return_value = mock_video

        mock_audio_clip = MagicMock()
        mock_audio_clip.duration = 5
        mock_audio.return_value = mock_audio_clip
        mock_audio_clip.subclip.return_value = mock_audio_clip
        mock_audio_clip.audio_fadeout.return_value = mock_audio_clip
        mock_afx.audio_loop.return_value = mock_audio_clip

        VideoEngine.add_audio("in.mp4", "out.mp4", music_dir="tests/mock_music")
        mock_clip.assert_called_with("in.mp4")

if __name__ == '__main__':
    unittest.main()