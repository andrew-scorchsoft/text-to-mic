import json
import platform
from pathlib import Path

class SettingsManager:
    """
    Centralizes access to application settings to prevent conflicts between components.
    """
    
    @staticmethod
    def get_settings_file_path(filename="settings.json"):
        """Get the platform-specific path for the settings file."""
        if platform.system() == 'Darwin':  # macOS
            from utils.api_key_manager import APIKeyManager
            mac_path = APIKeyManager.get_app_support_path_mac()
            return f"{mac_path}/{filename}"
        else:
            return filename  # Default to current directory for non-macOS systems
    
    @classmethod
    def get_default_settings(cls):
        """Return the default settings structure."""
        return {
            "chat_gpt_completion": False,
            "model": "gpt-4o-mini",
            "prompt": "",
            "auto_apply_ai_to_recording": False,
            "current_tone": "None",
            "hide_banner": False,
            "input_device": "Default",
            "primary_device": "Select Device",
            "secondary_device": "None",
            "hotkeys": {
                "record_start_stop": ["ctrl", "shift", "0"],
                "stop_recording": ["ctrl", "shift", "9"],
                "play_last_audio": ["ctrl", "shift", "8"],
                "cancel_operation": ["ctrl", "shift", "1"]
            },
            "max_tokens": 750
        }
    
    @classmethod
    def load_settings(cls):
        """Load settings from file, with defaults for missing values."""
        settings_file = cls.get_settings_file_path()
        default_settings = cls.get_default_settings()
        
        try:
            # Try to load existing settings
            with open(settings_file, "r") as f:
                settings = json.load(f)
                
            # Check if settings need to be updated with new defaults
            settings_updated = False
            
            # Recursively update nested dictionaries with missing keys
            def update_missing_settings(existing, defaults):
                nonlocal settings_updated
                for key, value in defaults.items():
                    if key not in existing:
                        existing[key] = value
                        settings_updated = True
                    elif isinstance(value, dict) and isinstance(existing[key], dict):
                        # Recursively update nested dictionaries
                        update_missing_settings(existing[key], value)
                return existing
            
            # Update settings with any missing values
            settings = update_missing_settings(settings, default_settings)
            
            # Save if any settings were updated
            if settings_updated:
                cls.save_settings(settings)
                print("Settings file updated with new default values")
                
        except FileNotFoundError:
            # Create new settings file with defaults if it doesn't exist
            settings = default_settings
            cls.save_settings(settings)
        
        return settings
    
    @classmethod
    def save_settings(cls, settings):
        """Save complete settings to file."""
        settings_file = cls.get_settings_file_path()
        
        with open(settings_file, "w") as f:
            json.dump(settings, f)
    
    @classmethod
    def update_settings(cls, partial_settings):
        """
        Update only specific settings without touching others.
        
        Args:
            partial_settings: Dictionary containing only the settings to update
        """
        # First load existing settings
        current_settings = cls.load_settings()
        
        # Update settings (recursively for nested dictionaries)
        def recursive_update(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    # If both are dictionaries, update recursively
                    recursive_update(target[key], value)
                else:
                    # Otherwise just update the value
                    target[key] = value
        
        recursive_update(current_settings, partial_settings)
        
        # Save the updated settings
        cls.save_settings(current_settings)
        return current_settings 