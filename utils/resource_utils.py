import os
import sys
from audioplayer import AudioPlayer

class ResourceUtils:
    """Utility class for handling resources and audio playback."""
    
    @staticmethod
    def resource_path(relative_path):
        """Get the absolute path to the resource, works for both development and PyInstaller environments."""
        try:
            # When running in a PyInstaller bundle, use the '_MEIPASS' directory
            base_path = sys._MEIPASS
        except AttributeError:
            # When running normally (not bundled), use the directory where the main script is located
            base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

        # Resolve the absolute path
        abs_path = os.path.join(base_path, relative_path)

        # Debugging: Print the absolute path to check if it's correct
        print(f"Resolved path for {relative_path}: {abs_path}")

        return abs_path
    
    @staticmethod
    def play_sound(sound_file):
        """Play a sound file."""
        player = AudioPlayer(ResourceUtils.resource_path(sound_file))
        player.play(block=True) 