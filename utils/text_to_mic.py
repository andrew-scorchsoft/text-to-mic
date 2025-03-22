import tkinter as tk
import platform
import os
import threading
import pyaudio
import wave
import webbrowser
import json
import sys
import time

from pystray import Icon as icon, MenuItem as item, Menu as menu
from PIL import Image, ImageDraw, ImageTk
from tkinter import ttk, messagebox, simpledialog, Menu, Frame, Canvas, Scrollbar
import customtkinter as ctk
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from pydub import AudioSegment

# Import our refactored classes
from utils.api_key_manager import APIKeyManager
from utils.hotkey_manager import HotkeyManager
from utils.resource_utils import ResourceUtils
from utils.tone_presets_manager import TonePresetsManager
from utils.presets_manager import PresetsManager
from utils.ai_editor_manager import AIEditorManager
from utils.settings_manager import SettingsManager

# Modify the load environment variables to load from config/.env
def load_env_file():
    env_path = Path("config") / ".env"
    load_dotenv(dotenv_path=env_path)

class TextToMic(tk.Tk):

    def __init__(self):
        super().__init__()

        self.version = "1.3.5"
        self.title(f"Text to Mic by Scorchsoft.com - v{self.version}")
        
        
        # Add these lines to set up the window icon
        icon_path = self.resource_path("assets/logo-circle-32.png")
        self.iconphoto(False, tk.PhotoImage(file=icon_path))
        
        # For Windows compatibility, also set the iconbitmap
        try:
            self.iconbitmap(self.resource_path("assets/icon.ico"))
        except:
            # This might fail on Mac, which is fine as we have iconphoto as backup
            pass
        
        # Fixed window dimensions for all states - DEFINED ONCE as class constants
        # These are the ONLY values that should be used throughout the application
        self.BASE_WIDTH = 590
        self.BASE_HEIGHT_WITH_BANNER = 860
        self.BASE_HEIGHT_NO_BANNER = 700
        self.COLLAPSED_HEIGHT_WITH_BANNER = 630
        self.COLLAPSED_HEIGHT_NO_BANNER = 512
        
        # Initial window geometry
        self.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT_WITH_BANNER}")

        self.available_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
        self.default_model = "gpt-4o-mini"

        # Cache for icons - will store loaded and resized icon images
        self.icon_cache = {}

        self.style = ttk.Style(self)
        if self.tk.call('tk', 'windowingsystem') == 'aqua':
            self.style.theme_use('aqua')
        else:
            # Create a custom theme instead of using 'clam'
            self.style.theme_use('clam')
            
            # Define a modern color scheme with clean light greys
            bg_color = "#f5f5f7"       # Very light grey background
            accent_color = "#e0e0e4"   # Slightly darker grey for accents
            text_color = "#333333"     # Dark grey for text
            button_bg = "#e8e8ec"      # Light grey for buttons
            
            # Configure default styles for various widgets
            self.style.configure('TFrame', background=bg_color)
            self.style.configure('TLabel', background=bg_color, foreground=text_color)
            self.style.configure('TButton', background=button_bg, foreground=text_color)
            self.style.configure('TCheckbutton', background=bg_color, foreground=text_color)
            self.style.configure('TRadiobutton', background=bg_color, foreground=text_color)
            self.style.configure('TMenubutton', background=button_bg, foreground=text_color)
            self.style.configure('TEntry', fieldbackground=bg_color, foreground=text_color)
            self.style.configure('TCombobox', fieldbackground=bg_color, foreground=text_color)
            
            # Override the background color of the main window
            self.configure(background=bg_color)

        #Define styles
        self.style.configure('Recording.TButton', background='red', foreground='white')
        self.style.configure("Green.TButton", background="green", foreground="white")

        # Ensure that the config directory exists
        self.ensure_config_directory()
        load_env_file()

        # Get API key using APIKeyManager
        self.api_key = APIKeyManager.get_api_key(self)
        if not self.api_key:
            messagebox.showinfo("API Key Needed", "Please provide your OpenAI API Key.")
            self.destroy()
            return

        
        self.client = OpenAI(api_key=self.api_key)

        # Initializing device index variables before they are used
        self.device_index = tk.StringVar(self)
        self.device_index_2 = tk.StringVar(self)

        self.available_devices = self.get_audio_devices()  # Load audio devices
        self.available_input_devices = self.get_input_devices() # Load input devices

        # Load tone presets
        self.tone_presets = TonePresetsManager.load_tone_presets(self)
        self.current_tone_name = self.load_current_tone_from_settings()
        
        # Create the category variable for the dropdown
        self.category_var = tk.StringVar(value="Select Category")

        # Add toggle for banner visibility before presets manager initialization
        self.banner_var = tk.BooleanVar()
        settings = self.load_settings()
        self.banner_var.set(settings.get("hide_banner", False))

        # Create the presets manager before initializing the GUI
        self.presets_manager = PresetsManager(self)
        
        # Create the AI Editor Manager
        self.ai_editor = AIEditorManager(self)
        
        # Store reference to presets state 
        self.presets_collapsed = self.presets_manager.presets_collapsed

        # Create menu and initialize GUI after presets manager is created
        self.create_menu()
        self.initialize_gui()
        
        # Initialize our HotkeyManager
        self.hotkey_manager = HotkeyManager(self)
        
        # If banner should be hidden based on settings, hide it now
        if self.banner_var.get():
            self.toggle_banner()

    def ensure_config_directory(self):
        """Ensure the config directory exists."""
        config_dir = Path("config")
        config_dir.mkdir(parents=True, exist_ok=True)

    def show_version(self):
        instruction_window = tk.Toplevel(self)
        instruction_window.title("App Version")
        instruction_window.geometry("300x150")  # Width x Height

        instructions = f"""Version {self.version}\n\n App by Scorchsoft.com"""
        
        tk.Label(instruction_window, text=instructions, justify=tk.LEFT, wraplength=280).pack(padx=10, pady=10)
        
        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0))

    def create_menu(self):
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        # File or settings menu
        settings_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change API Key", command=self.change_api_key)
        settings_menu.add_command(label="AI Copy Editing", command=self.show_ai_editor_settings)
        settings_menu.add_command(label="Hotkey Settings", command=self.show_hotkey_settings)  
        settings_menu.add_command(label="Manage Tone Presets", command=self.show_tone_presets_manager)

        # Playback menu
        playback_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Playback", menu=playback_menu)
        playback_menu.add_command(label="Play Last Audio", command=self.play_last_audio)

        #apply_ai
        input_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Input", menu=input_menu)
        input_menu.add_command(label="Apply AI Manipulation to Input Text", command=self.apply_ai_to_input)


        # Help menu
        help_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_instructions)
        help_menu.add_command(label="Terms of Use and Licence", command=self.show_terms_of_use)
        help_menu.add_command(label="Version", command=self.show_version)
        help_menu.add_command(label="Hotkey Instructions", command=self.show_hotkey_instructions)
        
        # Add toggle for banner visibility - use the existing banner_var from __init__
        help_menu.add_checkbutton(label="Hide Banner", variable=self.banner_var, command=self.toggle_banner)

    def show_hotkey_settings(self):
        """Show the hotkey settings dialog."""
        HotkeyManager.hotkey_settings_dialog(self)

    def show_hotkey_instructions(self):
        """Show hotkey instructions."""
        HotkeyManager.show_hotkey_instructions(self)

    def change_api_key(self):
        """Change the API key using APIKeyManager."""
        new_key = APIKeyManager.change_api_key(self)
        if new_key:
            self.api_key = new_key
            self.client = OpenAI(api_key=self.api_key)

    def get_audio_file_path(self, filename):
        if platform.system() == 'Darwin':  # Check if the OS is macOS
            mac_path = APIKeyManager.get_app_support_path_mac()
            return f"{mac_path}/{filename}"
        else:
            return Path(filename)  # Default to current directory for non-macOS systems

    def play_sound(self, sound_file):
        """Play a sound file using ResourceUtils."""
        ResourceUtils.play_sound(sound_file)

    def resource_path(self, relative_path):
        """Get the resource path using ResourceUtils."""
        return ResourceUtils.resource_path(relative_path)

    def initialize_gui(self):
        # Get saved settings
        settings = self.load_settings()

        self.input_device_index = tk.StringVar(self)
        self.device_index = tk.StringVar(self)
        self.device_index_2 = tk.StringVar(self)

        # Set default values
        default_input = "Default"
        default_output = "Select Device"
        default_secondary = "None"
        
        # Get saved device names from settings
        saved_input_device = settings.get("input_device", default_input)
        saved_primary_device = settings.get("primary_device", default_output)
        saved_secondary_device = settings.get("secondary_device", default_secondary)
        
        # Validate that saved devices are still available, otherwise use defaults
        if saved_input_device in self.available_input_devices:
            self.input_device_index.set(saved_input_device)
        else:
            self.input_device_index.set(default_input)
        
        if saved_primary_device in self.available_devices:
            self.device_index.set(saved_primary_device)
        else:
            self.device_index.set(default_output)
        
        if saved_secondary_device in self.available_devices or saved_secondary_device == "None":
            self.device_index_2.set(saved_secondary_device)
        else:
            self.device_index_2.set(default_secondary)

        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Use the background color from our style for the text widget
        bg_color = self.style.lookup('TFrame', 'background')
        text_color = self.style.lookup('TLabel', 'foreground')

        # Define custom button styles for pill-shaped buttons
        self.style.configure('Pill.TButton', 
                             font=('Arial', 13, 'bold'),
                             borderwidth=0,
                             relief='flat',
                             padding=(20, 8))
                             
        self.style.configure('RecordPill.TButton', 
                             font=('Arial', 13, 'bold'),
                             background='#d32f2f',
                             foreground='white',
                             borderwidth=0,
                             relief='flat',
                             padding=(20, 8))
                             
        self.style.configure('PlayPill.TButton', 
                             font=('Arial', 13, 'bold'),
                             background='#058705',
                             foreground='white',
                             borderwidth=0,
                             relief='flat',
                             padding=(20, 8))

        # Create frames for better organization
        voice_frame = ttk.Frame(main_frame)
        voice_frame.grid(column=0, row=0, columnspan=2, sticky="ew")
        voice_frame.columnconfigure(1, weight=1)  # Make the second column expandable

        device_frame = ttk.Frame(main_frame)
        device_frame.grid(column=0, row=1, columnspan=2, sticky="ew", pady=(10, 0))
        device_frame.columnconfigure(1, weight=1)  # Make the second column expandable

        # Set fixed width for dropdown menus
        dropdown_width = 30

        # Create a style for compact dropdowns
        self.style.configure('Compact.TMenubutton', padding=(5, 2))

        # Voice and Tone Settings
        ttk.Label(voice_frame, text="Voice Settings", font=("Arial", 10, "bold")).grid(column=0, row=0, sticky=tk.W, pady=(0, 10), columnspan=2)

        self.voice_var = tk.StringVar(value="fable")
        voices = ['alloy', 'ash', 'ballad', 'coral', 'echo', 'fable', 'onyx', 'nova', 'sage', 'shimmer']
        ttk.Label(voice_frame, text="Voice:").grid(column=0, row=1, sticky=tk.W, pady=(0, 5))
        voice_menu = ttk.OptionMenu(voice_frame, self.voice_var, self.voice_var.get(), *voices)
        voice_menu.grid(column=1, row=1, sticky=tk.E, pady=(0, 5))
        voice_menu.config(width=dropdown_width, style='Compact.TMenubutton')

        self.tone_var = tk.StringVar(value=self.current_tone_name)
        tone_options = ["None"] + list(self.tone_presets.keys())
        ttk.Label(voice_frame, text="Tone Preset:").grid(column=0, row=2, sticky=tk.W, pady=(0, 5))
        self.tone_menu = ttk.OptionMenu(voice_frame, self.tone_var, self.tone_var.get(), *tone_options, command=self.on_tone_change)
        self.tone_menu.grid(column=1, row=2, sticky=tk.E, pady=(0, 5))
        self.tone_menu.config(width=dropdown_width, style='Compact.TMenubutton')

        # Separator between Voice Settings and Device Settings
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.grid(column=0, row=2, columnspan=2, sticky="ew", pady=10)

        # Device Settings
        ttk.Label(device_frame, text="Device Settings", font=("Arial", 10, "bold")).grid(column=0, row=0, sticky=tk.W, pady=(0, 10), columnspan=2)

        ttk.Label(device_frame, text="Input Device (optional):").grid(column=0, row=1, sticky=tk.W, pady=(0, 5))
        input_device_menu = ttk.OptionMenu(device_frame, self.input_device_index, self.input_device_index.get(), 
                                          *self.available_input_devices.keys(), 
                                          command=self.on_input_device_change)
        input_device_menu.grid(column=1, row=1, sticky=tk.E, pady=(0, 5))
        input_device_menu.config(width=dropdown_width, style='Compact.TMenubutton')

        ttk.Label(device_frame, text="Primary Playback Device:").grid(column=0, row=2, sticky=tk.W, pady=(0, 5))
        primary_device_menu = ttk.OptionMenu(device_frame, self.device_index, self.device_index.get(), 
                                            *self.available_devices.keys(),
                                            command=self.on_primary_device_change)
        primary_device_menu.grid(column=1, row=2, sticky=tk.E, pady=(0, 5))
        primary_device_menu.config(width=dropdown_width, style='Compact.TMenubutton')

        ttk.Label(device_frame, text="Secondary Playback Device (optional):").grid(column=0, row=3, sticky=tk.W, pady=(0, 5))
        secondary_device_menu = ttk.OptionMenu(device_frame, self.device_index_2, self.device_index_2.get(), 
                                              "None", *self.available_devices.keys(),
                                              command=self.on_secondary_device_change)
        secondary_device_menu.grid(column=1, row=3, sticky=tk.E, pady=(0, 5))
        secondary_device_menu.config(width=dropdown_width, style='Compact.TMenubutton')

        # Text to Read section with proper layout
        text_read_frame = ttk.Frame(main_frame)
        text_read_frame.grid(column=0, row=4, columnspan=2, sticky="ew", pady=(10, 0))
        text_read_frame.columnconfigure(0, weight=1)  # Left side expands
        text_read_frame.columnconfigure(1, weight=0)  # Right side fixed width

        # Text to Read label - Updated to match other section titles
        ttk.Label(text_read_frame, text="Text to Read", font=("Arial", 10, "bold")).grid(column=0, row=0, sticky=tk.W, pady=(0, 10))

        # Create a frame to contain the dropdown and save button
        save_frame = ttk.Frame(text_read_frame)
        save_frame.grid(column=1, row=0, sticky=tk.E)

        # Preset Category dropdown
        categories = [cat["category"] for cat in self.presets_manager.presets]
        category_menu = ttk.OptionMenu(save_frame, self.category_var, *categories)
        category_menu.grid(column=0, row=0, sticky=tk.E, padx=(0, 5))
        category_menu.config(style='Compact.TMenubutton')

        # Create a compact style for the Save button to match dropdown height
        self.style.configure('Compact.TButton', padding=(2, 1))

        # Save button with matching height
        save_button = ttk.Button(save_frame, text="Save", width=8, style='Compact.TButton', command=self.save_current_text_as_preset)
        save_button.grid(column=1, row=0, sticky=tk.E)

        # Text input area with proper spacing
        self.text_input = tk.Text(main_frame, height=5, width=68)
        # Use white background for text input instead of the system background color
        text_color = self.style.lookup('TLabel', 'foreground')
        self.text_input.configure(bg="white", fg=text_color, insertbackground=text_color, wrap=tk.WORD)
        self.text_input.grid(column=0, row=5, columnspan=2, pady=(0, 20), sticky="nsew")  # Proper spacing

        # Add a status frame at the bottom of the text input with white background
        status_frame = ttk.Frame(main_frame, style='White.TFrame')
        status_frame.grid(column=0, row=5, columnspan=2, sticky=(tk.S, tk.E), pady=(0, 25))
        
        # Create a custom style for the white frame
        self.style.configure('White.TFrame', background='white')
        
        # Status indicator showing if editing is enabled
        status_text = "AI Copyediting Disabled"
        if settings.get("chat_gpt_completion", False):
            if settings.get("auto_apply_ai_to_recording", False):
                status_text = f"AI Copyediting Enabled (Auto) - {settings.get('model', self.default_model)}"
            else:
                status_text = f"AI Copyediting Enabled (Manual) - {settings.get('model', self.default_model)}"
        
        self.editing_status = ttk.Label(status_frame, text=status_text, foreground="#888888", font=("Arial", 8, "italic"), background="white")
        self.editing_status.pack(side=tk.RIGHT, padx=5)

        # Create a frame for the buttons to allow for better styling
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(column=0, row=6, columnspan=2, sticky="ew", pady=(0, 20))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        # Get keyboard shortcuts from settings
        settings = self.load_settings()
        record_shortcut = "+".join(filter(None, settings["hotkeys"]["record_start_stop"]))
        play_shortcut = "+".join(filter(None, settings["hotkeys"]["play_last_audio"]))

        # Button configuration
        self.recording = False  # State to check if currently recording
        self.is_playing = False  # State to check if audio is playing
        
        # Create CTk buttons with proper rounded corners
        button_height = 35
        button_width = 250
        
        # Record button with CTkButton
        self.record_button = ctk.CTkButton(
            button_frame,
            text=f"Record Mic ({record_shortcut})",
            corner_radius=20,
            height=button_height,
            width=button_width,
            fg_color="#058705",
            font=("Arial", 13, "bold"),
            command=self.handle_record_button_click
        )
        self.record_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        # Play button with CTkButton
        self.submit_button = ctk.CTkButton(
            button_frame,
            text=f"Play Audio ({play_shortcut})",
            corner_radius=20,
            height=button_height,
            width=button_width,
            fg_color="#058705",
            font=("Arial", 13, "bold"),
            command=self.handle_submit_button_click
        )
        self.submit_button.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        #Credits
        # Banner image that links to Scorchsoft
        self.banner_frame = ttk.Frame(main_frame)
        self.banner_frame.grid(column=0, row=7, columnspan=2, pady=(10, 10))
        
        banner_path = self.resource_path("assets/ss-banner-550.png")
        try:
            banner_img = tk.PhotoImage(file=banner_path)
            banner_label = tk.Label(self.banner_frame, image=banner_img, cursor="hand2")
            banner_label.image = banner_img  # Keep a reference to prevent garbage collection
            banner_label.pack()
            banner_label.bind("<Button-1>", lambda e: self.open_scorchsoft())
        except Exception as e:
            print(f"Error loading banner image: {e}")
            # Fallback to text if image fails to load
            info_label = tk.Label(self.banner_frame, text="Visit Scorchsoft.com for custom app development", 
                               fg="blue", cursor="hand2")
            info_label.pack()
            info_label.bind("<Button-1>", lambda e: self.open_scorchsoft())
        
        # If the banner should be hidden based on settings, hide it now
        if self.banner_var.get():
            self.toggle_banner()

    def open_scorchsoft(self, event=None):
        webbrowser.open('https://www.scorchsoft.com')

    def save_current_text_as_preset(self):
        """Forward the save request to the presets manager."""
        self.presets_manager.save_current_text_as_preset()

    def show_instructions(self):
        instruction_window = tk.Toplevel(self)
        instruction_window.title("How to Use")
        instruction_window.geometry("600x720")  # Width x Height

        instructions = """How to Use Scorchsoft Text to Mic:

1. Install VB-Cable if you haven't already
https://vb-audio.com/Cable/
This tool creates a virtual microphone on your Windows computer or Mac. Once installed you can then trigger audio to be played on this virual cable.

2. Open the Text to Mic app by Scorchsoft, and input your OpenAPI key. How to set up an API key:
https://platform.openai.com/docs/quickstart/account-setup
(note that this may require you to add your billing details to OpenAI's playground before a key can be generated)
In short, you sign up, go to playground, add billing details, go to API keys, add one, copy it, paste into Text to Mic.

WARNING: This will use your OpenAI key to generate audio via the OpenAI API, which will incur charges per use. So please make sure to carefully monitor use.
OpenAI pricing: openai.com/pricing

3. Choose a voice that you prefer for the speech synthesis.

4. (Optional) Select a Tone Preset to modify how the text is spoken. You can use the built-in presets or create your own under 'Settings > Manage Tone Presets'. Tone presets add special instructions to make the voice sound cheerful, angry, like a bedtime story, etc.

5. Select a playback device. I recommend you select one device to be your headphones, and the other the virtuall microphone installed above (Which is usually labelled "Cable Input (VB-Audio))"

6. Enter the text in the provided text area that you want to convert to speech.

7. Click 'Play Audio' to hear the spoken version of your text.

8. The 'Record Mic' button can be used to record from your microphone and transcribe it to text, which can then be played back.

9. You can change the API key at any time under the 'Settings' menu.

This tool was brought to you by Scorchsoft - We build custom apps to your requirements. Please contact us if you have a requirement for a custom app project.

If you like this tool then please help us out and give us a backlink to help others find it at:
https://www.scorchsoft.com/blog/text-to-mic-for-meetings/

Please also make sure you read the Terms of use and licence statement before using this app."""
        
        tk.Label(instruction_window, text=instructions, justify=tk.LEFT, wraplength=580).pack(padx=10, pady=10)
        
        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0))

    def show_terms_of_use(self):
        # Try multiple approaches to find the LICENSE.md file
        license_content = None
        possible_paths = [
            "LICENSE.md",                            # Direct path when running as script
            self.resource_path("LICENSE.md"),        # Using resource_path helper
            self.resource_path("assets/LICENSE.md"), # Check in assets folder
            Path("assets") / "LICENSE.md"            # Alternative assets path
        ]
        
        # Try each path until we find the file
        for path in possible_paths:
            try:
                with open(path, "r", encoding="utf-8") as file:
                    license_content = file.read()
                    break
            except (FileNotFoundError, PermissionError, UnicodeDecodeError):
                continue
        
        # If we couldn't find the file in the filesystem, provide a fallback
        if license_content is None:
            license_content = """
            Scorchsoft Text to Mic License

            This application is provided for personal and commercial use, subject to the following conditions:

            1. You may use this application for personal or commercial purposes.
            2. You may not redistribute, sell, or include this application as part of another product without explicit permission.
            3. This application uses the OpenAI API, and you are responsible for any charges incurred through your API key.
            4. The developer assumes no liability for any misuse or charges incurred through use of this application.

            For the complete license text, please visit:
            https://www.scorchsoft.com/text-to-mic-license

            Copyright © Scorchsoft.com
            """
        
        # Create a new window to display the terms of use
        instruction_window = tk.Toplevel(self)
        instruction_window.title("Terms of Use")
        instruction_window.geometry("800x700")  # Width x Height

        # Create a frame to contain the text widget and scrollbar
        frame = ttk.Frame(instruction_window)
        frame.pack(fill=tk.BOTH, expand=True)

        # Add a scrolling text widget to display the license content
        text_widget = tk.Text(frame, wrap=tk.WORD)
        text_widget.insert(tk.END, license_content)
        text_widget.config(state=tk.DISABLED)  # Make the text read-only
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a vertical scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the scrollbar to work with the text widget
        text_widget.config(yscrollcommand=scrollbar.set)

        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0))

    def get_app_support_path_mac(self):
        home = Path.home()
        app_support_path = home / 'Library' / 'Application Support' / 'scorchsoft-text-to-mic'
        app_support_path.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        return app_support_path
    
    def save_api_key_mac(self, api_key):
        env_path = self.get_app_support_path_mac() / 'config' / '.env'
        with open(env_path, 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        # Consider manually loading this .env file into your environment as needed

    def save_api_key(self, api_key):
        """Save the API key to the config/.env file."""
        try:
            config_dir = Path("config")
            config_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

            env_path = config_dir / ".env"
            with open(env_path, 'w') as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")

            load_dotenv(dotenv_path=env_path)  # Reload environment to include the new API key

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key: {str(e)}")

    def load_api_key_mac(self):
        env_path = self.get_app_support_path_mac() / '.env'
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY'):
                        return line.strip().split('=')[1]
        return None

 
    def get_api_key(self):
        # First, try to load the API key from environment variables or local file
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:  # Check for macOS and use the macOS-specific method
            if platform.system() == 'Darwin':  # Darwin is the system name for macOS
                api_key = self.load_api_key_mac()
            
            # If no API key is found, prompt the user
            if not api_key:
                self.show_instructions()  # Show the "How to Use" modal after setting the key
                api_key = simpledialog.askstring("API Key", "Enter your OpenAI API Key:", parent=self)
                if api_key:
                    try:
                        if platform.system() == 'Darwin':
                            self.save_api_key_mac(api_key)
                        else:
                            self.save_api_key(api_key)
                        messagebox.showinfo("API Key Set", "The OpenAI API Key has been updated successfully.")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to save API key: {str(e)}")
        
        return api_key





    def get_audio_devices(self):
        p = pyaudio.PyAudio()
        devices = {}
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:  # Filter for output-capable devices
                devices[info['name']] = i
        p.terminate()
        return devices
    
    def get_input_devices(self):
        p = pyaudio.PyAudio()
        devices = {}
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:  # Filter for input-capable devices
                devices[info['name']] = i
        p.terminate()
        return devices

    
    def get_audio_file_path(self, filename):
        if platform.system() == 'Darwin':  # Check if the OS is macOS
            mac_path = APIKeyManager.get_app_support_path_mac()
            return f"{mac_path}/{filename}"
        else:
            return Path(filename)  # Default to current directory for non-macOS systems


    def submit_text(self, play_text = None):
        print(f"submit text self recording: {self.recording}")
        if self.recording:
            print("Stopping recording")
            self.stop_recording(auto_play = True)
        else:
            print("Submitting text")
            self.submit_text_helper(play_text = play_text)
    
    def submit_text_helper(self, play_text = None):

        if play_text is None:
            #Load from GUI if play text not set
            text = self.text_input.get("1.0", tk.END).strip()
        else:
            text = play_text

        if not text:
            messagebox.showinfo("Error", "Please enter some text to synthesize.")
            return
        
        selected_voice = self.voice_var.get()
        
        # Check if a tone preset is selected and add it to the text
        selected_tone_name = self.tone_var.get()
        
        # Get the actual tone instructions from the tone_presets dictionary
        tone_instructions = None
        if selected_tone_name != "None" and selected_tone_name in self.tone_presets:
            tone_instructions = self.tone_presets[selected_tone_name]
        else:
            tone_instructions = ""  # Empty string if "None" or not found
        
        # Convert device names to indices
        primary_index = self.available_devices.get(self.device_index.get(), None)
        secondary_index = self.available_devices.get(self.device_index_2.get(), None) if self.device_index_2.get() != "None" else None

        if primary_index is None:
            messagebox.showerror("Error", "Primary device not selected or unavailable.")
            return
        
        print(f"Primary Index: {primary_index}, Secondary Index: {secondary_index}")
        print(f"Selected Tone: {selected_tone_name}")
        print(f"Tone Instructions: {tone_instructions}")
        try:

            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=selected_voice,
                input=text,
                instructions=tone_instructions,
                response_format='wav'
            )

            self.last_audio_file = self.get_audio_file_path("last_output.wav")
            response.stream_to_file(str(self.last_audio_file))

            #Play to either two or a single stream
            if primary_index and secondary_index != "None" and secondary_index is not None:
                self.play_audio_multiplexed([self.last_audio_file, self.last_audio_file],
                                            [primary_index, secondary_index])
            else:
                self.play_audio_multiplexed([self.last_audio_file],
                                            [primary_index])


        except Exception as e:
            messagebox.showerror("API Error", f"Failed to generate audio: {str(e)}")


    def resample_audio(self, file_path, target_sample_rate):
        sound = AudioSegment.from_file(file_path)
        resampled_sound = sound.set_frame_rate(target_sample_rate)
        resampled_file_path = "resampled_" + file_path
        resampled_sound.export(resampled_file_path, format="wav")
        return resampled_file_path

    def play_audio_multiplexed(self, file_paths, device_indices):
        """Play audio files to multiple devices with better cancellation handling."""
        # Stop any existing playback first
        if hasattr(self, 'is_playing') and self.is_playing:
            self.stop_playback()
            # Add a small delay to ensure previous resources are cleaned up
            time.sleep(0.2)
        
        # Make p and streams accessible for stop_playback
        try:
            self.current_playback_p = pyaudio.PyAudio()
            self.current_playback_streams = []
            self.is_playing = True
            
            # Update button text to show Stop with cancel operation shortcut
            self.update_buttons_for_playback(True)
            
        except Exception as e:
            print(f"Error initializing PyAudio: {e}")
            messagebox.showerror("Audio Error", f"Failed to initialize audio system: {e}")
            return
        
        try:
            # Open all files and start all streams
            for file_path, device_index in zip(file_paths, device_indices):
                if not self.is_playing:
                    print("Playback canceled during initialization")
                    break
                    
                try:
                    # Ensure the file_path is a string when opening the file
                    wf = wave.open(str(file_path), 'rb')
                except FileNotFoundError:
                    messagebox.showerror("File Not Found", f"Could not find audio file: {file_path}")
                    continue  # Skip this iteration and proceed with other files if any
                except wave.Error as e:
                    messagebox.showerror("Wave Error", f"Error reading audio file: {file_path}. Error: {str(e)}")
                    continue

                try:
                    # Ensure output audio sample rate matches that of the selected device
                    device_info = self.get_device_info(device_index)
                    sample_rate = int(device_info['defaultSampleRate'])  # Fetch default sample rate from device info
                    wf_frame_rate = wf.getframerate()

                    print(f"Sample Rate: {sample_rate}")
                    print(f"WF Sample Width: {wf_frame_rate}")

                    if sample_rate is None:
                        sample_rate = wf_frame_rate

                    # Make the audio file sample rate match the device output sample rate
                    # if there is a mismatch (prevents playback speed issues or crashes)
                    if sample_rate != wf_frame_rate:
                        # If mismatch, make a new resampled version that matches the output device
                        resampled_file_path = self.resample_audio(str(file_path), sample_rate)
                        # Update the playback file to the new resampled file
                        file_path = resampled_file_path
                        # Re-open the new file for processing
                        wf.close()  # Close the original file first
                        wf = wave.open(str(file_path), 'rb')
                  
                    # Create a stream from our file
                    stream = self.current_playback_p.open(
                        format=self.current_playback_p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=sample_rate,
                        output=True,
                        output_device_index=int(device_index)
                    )
                    
                except Exception as e:
                    messagebox.showerror("Stream Creation Error", f"Failed to create audio stream for device index {device_index}: {str(e)}")
                    wf.close()
                    continue

                self.current_playback_streams.append((stream, wf))

            # Play interleaved using a more robust approach
            self._play_audio_streams()
            
        except Exception as e:
            print(f"Playback setup error: {e}")
            messagebox.showerror("Playback Error", f"Error setting up playback: {e}")
            self.stop_playback()
    
    def _play_audio_streams(self):
        """Handle the actual audio playback in chunks, with better error handling."""
        if not hasattr(self, 'current_playback_streams') or not self.current_playback_streams:
            print("No streams to play")
            self.stop_playback()
            return
            
        try:
            finished_streams = []
            
            # Process one chunk from each stream
            for stream, wf in self.current_playback_streams:
                if not self.is_playing:
                    print("Playback canceled during streaming")
                    break
                    
                try:
                    data = wf.readframes(1024)
                    if data:
                        stream.write(data)
                    else:
                        # Mark this stream as finished
                        finished_streams.append((stream, wf))
                except Exception as e:
                    print(f"Error during stream playback: {e}")
                    # Add to finished streams if there's an error
                    finished_streams.append((stream, wf))
            
            # Remove finished streams
            for stream_pair in finished_streams:
                try:
                    stream, wf = stream_pair
                    stream.stop_stream()
                    stream.close()
                    wf.close()
                    self.current_playback_streams.remove(stream_pair)
                except Exception as e:
                    print(f"Error cleaning up finished stream: {e}")
            
            # If we still have streams and playback is active, schedule the next chunk
            if self.current_playback_streams and self.is_playing:
                self.after(1, self._play_audio_streams)  # Schedule next chunk processing
            else:
                # All done or canceled, clean up
                self.stop_playback()
                
        except Exception as e:
            print(f"Error in _play_audio_streams: {e}")
            self.stop_playback()
    
    def stop_playback(self):
        """Stop any active audio playback."""
        print("Attempting to stop playback")
        
        # Set flag first to exit any playback loops
        self.is_playing = False
        
        # Revert buttons to normal state
        self.update_buttons_for_playback(False)
        
        try:
            # Close any active streams
            if hasattr(self, 'current_playback_streams'):
                # Make a copy of the list to safely iterate while potentially modifying
                streams_to_close = list(self.current_playback_streams)
                
                for stream, wf in streams_to_close:
                    try:
                        # Check if stream exists and is active before attempting to stop it
                        if stream and stream.is_active():
                            stream.stop_stream()
                        if stream:
                            stream.close()
                        if wf:
                            wf.close()
                    except Exception as e:
                        print(f"Error closing stream: {e}")
                
                # Clear the list after processing all streams
                self.current_playback_streams = []
            
            # Terminate PyAudio instance - do this last and carefully
            if hasattr(self, 'current_playback_p') and self.current_playback_p:
                try:
                    # Add a small delay to ensure streams are properly closed before terminating
                    self.after(100, self._complete_playback_termination)
                except Exception as e:
                    print(f"Error scheduling PyAudio termination: {e}")
        
        except Exception as e:
            print(f"Error in stop_playback: {e}")
            # Don't reraise - we want to prevent crashes
    
    def _complete_playback_termination(self):
        """Complete the termination of PyAudio in a separate step to avoid crashes."""
        try:
            if hasattr(self, 'current_playback_p') and self.current_playback_p:
                self.current_playback_p.terminate()
                self.current_playback_p = None
                print("PyAudio terminated successfully")
        except Exception as e:
            print(f"Error terminating PyAudio: {e}")
            # Still clear the reference even if termination fails
            self.current_playback_p = None

    def play_last_audio(self):

        if hasattr(self, 'last_audio_file'):
            primary_index = self.available_devices.get(self.device_index.get(), None)
            secondary_index = self.available_devices.get(self.device_index_2.get(), None) if self.device_index_2.get() != "None" else None

            # Check if a secondary device is selected
            if primary_index and secondary_index != "None" and secondary_index is not None:
                self.play_audio_multiplexed([self.last_audio_file, self.last_audio_file],
                                            [primary_index, secondary_index])
            else:
                self.play_audio_multiplexed([self.last_audio_file],
                                            [primary_index])

        else:
            messagebox.showinfo("No Audio", "No audio has been generated yet.")

    def play_saved_audio(self, file_path, device_name):
        device_index = self.available_devices.get(device_name, None)
        if device_index is None:
            messagebox.showerror("Error", "Selected audio device is not available.")
            return
        
        wf = wave.open(file_path, 'rb')
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True,
                            output_device_index=device_index)
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
        finally:
            stream.stop_stream()
            stream.close()
            wf.close()
            p.terminate()

            
    def show_ai_editor_settings(self):
        """Show the AI copy editing settings dialog"""
        self.ai_editor.show_settings()

    def apply_ai_to_input(self):
        """Apply AI to the current input text"""
        self.ai_editor.apply_ai()

    def chat_gpt_settings(self):
        """Delegate to AIEditorManager"""
        self.show_ai_editor_settings()

    def save_chat_gpt_settings(self, settings):
        """Delegate to AIEditorManager"""
        self.ai_editor.save_settings(settings)

    def apply_ai(self, input_text=None):
        """Delegate to AIEditorManager"""
        return self.ai_editor.apply_ai(input_text)

    def get_device_info(self, device_index):
        p = pyaudio.PyAudio()
        try:
            device_info = p.get_device_info_by_index(device_index)
            return device_info
        finally:
            p.terminate()
    
    def toggle_recording(self, auto_play=False):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording(auto_play)

    def stop_recording_btn_change(self, btn_text):
        self.record_button.config(text=btn_text)

    def start_recording(self, play_confirm_sound=False):
        input_device_index = self.input_device_index.get()  # Assuming input_device_index is a StringVar
        input_device_id = self.available_input_devices.get(input_device_index)

        if input_device_id is None:
            if play_confirm_sound:
                self.play_sound('assets/please-select-input.wav')
            else:
                messagebox.showerror("Error", "Selected audio device is not available.")
            return

        device_info = self.get_device_info(input_device_id)
        sample_rate = int(device_info['defaultSampleRate'])

        print(f"Device info: {device_info}")

        if sample_rate is None:
            sample_rate = 44100

        if input_device_id is None:
            messagebox.showerror("Error", "Selected audio device is not available.")
            return
        
        try:
            self.recording = True
            
            # Get keyboard shortcuts from settings
            settings = self.load_settings()
            record_shortcut = "+".join(filter(None, settings["hotkeys"]["record_start_stop"]))
            play_shortcut = "+".join(filter(None, settings["hotkeys"]["play_last_audio"]))
            stop_shortcut = "+".join(filter(None, settings["hotkeys"]["stop_recording"]))
            
            # Update CTkButton for recording state, keeping shortcuts visible
            self.record_button.configure(text=f"Stop and Insert", fg_color="#d32f2f")
            self.submit_button.configure(text=f"Stop and Play ({record_shortcut})", fg_color="#d32f2f")

            self.frames = []

            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, input=True, frames_per_buffer=1024, input_device_index=input_device_id)

            if play_confirm_sound:
                self.play_sound('assets/pop.wav')

            def record():
                while self.recording:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    self.frames.append(data)

            self.record_thread = threading.Thread(target=record)
            self.record_thread.start()

        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to record audio: {str(e)}")
            self.stop_recording(True)

    def stop_recording(self, cancel_save=False, auto_play=False):
        self.recording = False
        if hasattr(self, 'record_thread') and self.record_thread:
            self.record_thread.join()

        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if hasattr(self, 'p') and self.p:
            self.p.terminate()

        if cancel_save==False:
            self.save_recording(auto_play=auto_play)
        
        # Get keyboard shortcuts from settings
        settings = self.load_settings()
        record_shortcut = "+".join(filter(None, settings["hotkeys"]["record_start_stop"]))
        play_shortcut = "+".join(filter(None, settings["hotkeys"]["play_last_audio"]))
        
        # Reset button appearance
        self.record_button.configure(text=f"Record Mic ({record_shortcut})", fg_color="#058705")
        self.submit_button.configure(text=f"Play Audio ({play_shortcut})", fg_color="#058705")

    def save_recording(self, auto_play = False):
        file_path = "output.wav"
        wf = wave.open(file_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print("Recording saved.")

        # If auto_play is requested, we'll handle it through the transcribe_audio callback
        # This ensures proper button state updates regardless of how playback is triggered
        self.after(0, self.transcribe_audio, file_path, auto_play)
        
    def transcribe_audio(self, file_path, auto_play = False):
        try:
            with open(str(file_path), "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="gpt-4o-transcribe",
                    response_format="json"
                )

            settings = self.load_settings()
            
            # Always update the text with the raw transcription first
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", transcription.text)

            if settings["chat_gpt_completion"] and settings["auto_apply_ai_to_recording"]:
                auto_apply_ai = settings["auto_apply_ai_to_recording"]
            else:
                auto_apply_ai = False

            print(f"auto_apply_ai: {auto_apply_ai}")

            # If AI processing is enabled, apply it and update the text input again
            if auto_apply_ai:
                print("applying ai")
                # Set the update_ui parameter to True to ensure the text gets updated
                play_text = self.ai_editor.apply_ai(transcription.text, update_ui=True)
            else:
                print("outputting without ai")
                play_text = transcription.text

            if auto_play:
                print(f"Triggering auto play with: {play_text} ")
                # Use a slight delay to allow UI to update before playback starts
                self.after(100, lambda: self.submit_text_helper(play_text = play_text))
            
            print("Transcription Complete: The audio has been transcribed and the text has been placed in the input area.")
        
        except Exception as e:
            print(f"Transcription error: An error occurred during transcription: {str(e)}")

    def load_settings(self):
        """Load settings using the SettingsManager."""
        return SettingsManager.load_settings()

    def save_settings_to_JSON(self, settings):
        """Save complete settings using the SettingsManager."""
        SettingsManager.save_settings(settings)

    def update_settings(self, partial_settings):
        """Update specific settings without overwriting others."""
        return SettingsManager.update_settings(partial_settings)

    def get_settings_file_path(self, filename):
        """Get the settings file path using SettingsManager."""
        return SettingsManager.get_settings_file_path(filename)

    # Methods for tone preset management
    def show_tone_presets_manager(self):
        """Show the tone presets manager dialog."""
        TonePresetsManager(self)
    
    def load_current_tone_from_settings(self):
        """Load the current tone preset from settings."""
        settings = self.load_settings()
        return settings.get("current_tone", "None")
    
    def save_current_tone_to_settings(self):
        """Save the current tone preset to settings."""
        settings = self.load_settings()
        settings["current_tone"] = self.current_tone_name
        self.save_settings_to_JSON(settings)
    
    def on_tone_change(self, event):
        """Handle tone selection change in the dropdown."""
        self.current_tone_name = self.tone_var.get()
        self.save_current_tone_to_settings()
    
    def update_tone_selection(self):
        """Update the tone selection dropdown with current presets."""
        # Update the variable
        self.tone_var.set(self.current_tone_name)
        
        # Rebuild the dropdown menu
        menu = self.tone_menu["menu"]
        menu.delete(0, "end")
        
        tone_options = ["None"] + list(self.tone_presets.keys())
        for tone in tone_options:
            menu.add_command(label=tone, 
                            command=lambda value=tone: self.tone_var.set(value))
    
    def save_tone_presets(self, tone_presets):
        """Save tone presets using the TonePresetsManager."""
        return TonePresetsManager.save_tone_presets(self, tone_presets)

    # Add a new method to toggle banner visibility
    def toggle_banner(self):
        """Toggle the visibility of the banner image."""
        settings = self.load_settings()
        hide_banner = self.banner_var.get()
        
        # Get current presets state
        presets_visible = hasattr(self, 'presets_manager') and not self.presets_manager.presets_collapsed
        
        # Calculate width that preserves current width if manually resized
        current_width = self.winfo_width()
        width_to_use = max(current_width, self.BASE_WIDTH)
        
        if hide_banner:
            # Hide the banner
            self.banner_frame.grid_remove()
            
            # Set window geometry based on presets state
            if presets_visible:
                # Presets visible, banner hidden
                self.geometry(f"{width_to_use}x{self.BASE_HEIGHT_NO_BANNER}")
            else:
                # Presets collapsed, banner hidden
                self.geometry(f"{width_to_use}x{self.COLLAPSED_HEIGHT_NO_BANNER}")
        else:
            # Show the banner
            self.banner_frame.grid()
            
            # Set window geometry based on presets state
            if presets_visible:
                # Presets visible, banner visible
                self.geometry(f"{width_to_use}x{self.BASE_HEIGHT_WITH_BANNER}")
            else:
                # Presets collapsed, banner visible
                self.geometry(f"{width_to_use}x{self.COLLAPSED_HEIGHT_WITH_BANNER}")
        
        # Update the settings
        settings["hide_banner"] = hide_banner
        self.save_settings_to_JSON(settings)
        
        # Make sure presets are laid out correctly if visible
        if presets_visible and hasattr(self, 'presets_manager'):
            self.presets_manager.refresh_presets_display()
        
        # Ensure the presets button is correctly positioned using grid
        if hasattr(self, 'presets_manager') and hasattr(self.presets_manager, 'presets_button'):
            if self.presets_manager.presets_button.winfo_exists():
                # Use grid (not pack) to ensure proper positioning
                self.presets_manager.presets_button.grid_configure(column=0, row=0, sticky=tk.W, padx=0, pady=2)

    def toggle_presets(self):
        """Toggle the visibility of the presets panel."""
        if hasattr(self, 'presets_manager'):
            # Toggle presets via presets manager
            self.presets_manager.toggle_presets()
            
            # Update our local tracking of presets state
            self.presets_collapsed = self.presets_manager.presets_collapsed
            
            # Get banner visibility state
            banner_hidden = self.banner_var.get()
            
            # Calculate a width that preserves the current width if it's larger than default
            current_width = self.winfo_width()
            width_to_use = max(current_width, self.BASE_WIDTH)
            
            # Set window geometry based on both states
            if self.presets_collapsed:
                # Presets collapsed - ensure minimum height with current width
                if banner_hidden:
                    # Banner hidden, presets collapsed
                    self.geometry(f"{width_to_use}x{self.COLLAPSED_HEIGHT_NO_BANNER}")
                else:
                    # Banner visible, presets collapsed
                    self.geometry(f"{width_to_use}x{self.COLLAPSED_HEIGHT_WITH_BANNER}")
            else:
                # Presets expanded - use full height with current width
                if banner_hidden:
                    # Banner hidden, presets expanded
                    self.geometry(f"{width_to_use}x{self.BASE_HEIGHT_NO_BANNER}")
                else:
                    # Banner visible, presets expanded
                    self.geometry(f"{width_to_use}x{self.BASE_HEIGHT_WITH_BANNER}")
            
            # Refresh presets display if they're visible
            if not self.presets_collapsed:
                self.presets_manager.refresh_presets_display()

    def update_buttons_for_playback(self, is_playing):
        """Update button text based on playback state."""
        try:
            # Get keyboard shortcuts from settings
            settings = self.load_settings()
            record_shortcut = "+".join(filter(None, settings["hotkeys"]["record_start_stop"]))
            play_shortcut = "+".join(filter(None, settings["hotkeys"]["play_last_audio"]))
            cancel_shortcut = "+".join(filter(None, settings["hotkeys"]["cancel_operation"]))
            
            if is_playing:
                # Set both buttons to show stop with cancel shortcut
                self.record_button.configure(text=f"Stop Audio ({cancel_shortcut})", fg_color="#d32f2f")
                self.submit_button.configure(text=f"Stop Audio ({cancel_shortcut})", fg_color="#d32f2f")
            else:
                # Reset buttons to normal state
                self.record_button.configure(text=f"Record Mic ({record_shortcut})", fg_color="#058705")
                self.submit_button.configure(text=f"Play Audio ({play_shortcut})", fg_color="#058705")
        except Exception as e:
            print(f"Error updating buttons: {e}")
            # Don't raise the exception further to prevent crashes

    def handle_record_button_click(self):
        """Handle clicks on the record button based on current state."""
        if self.is_playing:
            # If audio is playing, stop it
            self.stop_playback()
        else:
            # Otherwise, toggle recording as before
            self.toggle_recording()
    
    def handle_submit_button_click(self, via_hotkey=False):
        """Handle clicks on the submit/play button based on current state."""
        if self.is_playing:
            # If audio is playing, stop it
            self.stop_playback()
        elif self.recording and via_hotkey:
            # If recording and triggered via hotkey, stop recording and play
            self.recording = False
            self.stop_recording(auto_play=True)
        else:
            # Otherwise, submit text as before
            self.submit_text()

    def on_input_device_change(self, device_name):
        """Save the selected input device in settings."""
        settings = self.load_settings()
        settings["input_device"] = device_name
        self.save_settings_to_JSON(settings)
        
    def on_primary_device_change(self, device_name):
        """Save the selected primary output device in settings."""
        settings = self.load_settings()
        settings["primary_device"] = device_name
        self.save_settings_to_JSON(settings)
        
    def on_secondary_device_change(self, device_name):
        """Save the selected secondary output device in settings."""
        settings = self.load_settings()
        settings["secondary_device"] = device_name
        self.save_settings_to_JSON(settings)


