import unittest
from unittest.mock import patch, MagicMock
from src.visualizer import library_extensions as my_extensions

class TestPatch(unittest.TestCase):

    @patch('os.path.exists')
    def test_get_hero_image(self, mock_exists):
        """Test finding hero images with sanitization"""
        
        # Scenario 1: File exists directly
        # Input: "Pudge" -> Checks "assets/Pudge.png" -> Found
        mock_exists.return_value = True
        result = my_extensions.get_hero_image("Pudge", "assets")
        self.assertEqual(result, "assets/Pudge.png")
        
        # Scenario 2: Name needs sanitization (Slash -> Underscore)
        # Input: "Hero/Name" -> Checks "assets/Hero/Name.png" (Fail) -> Checks "assets/Hero_Name.png" (Pass)
        def side_effect(path):
            if "Hero/Name.png" in path: return False # OS can't handle slashes in filenames
            if "Hero_Name.png" in path: return True  # Sanitized version exists
            return False
            
        mock_exists.side_effect = side_effect
        result = my_extensions.get_hero_image("Hero/Name", "assets")
        self.assertEqual(result, "assets/Hero_Name.png")

    def test_patched_make_animation_logic(self):
        """Ensure our patch fixes the Matplotlib FPS crash"""
        
        # 1. Setup a fake BarChartRace object
        mock_bcr_self = MagicMock()
        mock_bcr_self.fig = MagicMock()
        mock_bcr_self.df_values = [1, 2, 3] # Fake frames
        mock_bcr_self.period_length = 500
        mock_bcr_self.steps_per_period = 10
        mock_bcr_self.filename = "out.mp4"
        
        # 2. Mock the Animation object that gets created inside
        with patch('src.visualizer.library_extensions.FuncAnimation') as MockAnim:
            mock_anim_instance = MagicMock()
            MockAnim.return_value = mock_anim_instance
            
            # CASE A: Writer is a String (e.g. 'ffmpeg') -> MUST pass fps
            mock_bcr_self.writer = 'ffmpeg'
            mock_bcr_self.fps = 30
            
            # Run the patched function manually
            my_extensions.patched_make_animation(mock_bcr_self)
            
            # Assert fps IS passed
            mock_anim_instance.save.assert_called_with("out.mp4", fps=30, writer='ffmpeg')
            
            # CASE B: Writer is an Object (ProgressWriter) -> MUST NOT pass fps
            mock_bcr_self.writer = MagicMock() # It's an object now
            
            # Run again
            my_extensions.patched_make_animation(mock_bcr_self)
            
            # Assert fps IS NOT passed
            mock_anim_instance.save.assert_called_with("out.mp4", writer=mock_bcr_self.writer)

if __name__ == '__main__':
    unittest.main()