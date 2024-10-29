import tkinter as tk
import platform
import os
import threading
import pyaudio
import wave
import webbrowser
import json
import keyboard
import sys

from pystray import Icon as icon, MenuItem as item, Menu as menu
from PIL import Image, ImageDraw
from tkinter import ttk, messagebox, simpledialog, Menu, Frame, Canvas, Scrollbar
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from pydub import AudioSegment
from audioplayer import AudioPlayer


# Modify the load environment variables to load from config/.env
def load_env_file():
    env_path = Path("config") / ".env"
    load_dotenv(dotenv_path=env_path)

class TextToMic(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Scorchsoft Text to Mic")
        self.default_geometry = "590x750"
        self.geometry(self.default_geometry) 

        self.available_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
        self.default_model = "gpt-4o-mini"

        self.style = ttk.Style(self)
        if self.tk.call('tk', 'windowingsystem') == 'aqua':
            self.style.theme_use('aqua')
        else:
            self.style.theme_use('clam')  # Fallback to 'clam' on non-macOS systems

        #Define stules
        self.style.configure('Recording.TButton', background='red', foreground='white')
        self.style.configure("Green.TButton", background="green", foreground="white")

        self.presets = self.load_presets()
        self.current_category = "All"
        self.presets_collapsed = True 


        # Ensure that the config directory exists
        self.ensure_config_directory()
        load_env_file()

        # Ensure API Key is loaded or prompted for before initializing GUI components
        self.api_key = self.get_api_key()
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

        self.create_menu()
        self.initialize_gui()
        self.setup_hotkeys()


        
    
    def ensure_config_directory(self):
        """Ensure the config directory exists."""
        config_dir = Path("config")
        config_dir.mkdir(parents=True, exist_ok=True)

    def show_version(self):
        instruction_window = tk.Toplevel(self)
        instruction_window.title("App Version")
        instruction_window.geometry("300x150")  # Width x Height

        instructions = """Version 1.2.0\n\n App by Scorchsoft.com"""
        
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
        settings_menu.add_command(label="ChatGPT Manipulation", command=self.chat_gpt_settings)
        settings_menu.add_command(label="Hotkey Settings", command=self.hotkey_settings)  


        # Playback menu
        playback_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Playback", menu=playback_menu)
        playback_menu.add_command(label="Play Last Audio", command=self.play_last_audio)
        #playback_menu.add_command(label="Input Speech to Text", command=self.input_speech_to_text)

        #apply_ai
        input_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Input", menu=input_menu)
        input_menu.add_command(label="Apply AI Manipulation to Input Text", command=self.apply_ai)


        # Help menu
        help_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_instructions)
        help_menu.add_command(label="Terms of Use and Licence", command=self.show_terms_of_use)
        help_menu.add_command(label="Version", command=self.show_version)
        help_menu.add_command(label="Hotkey Instructions", command=self.show_hotkey_instructions)
        


    def hotkey_settings(self):
        settings = self.load_settings()
        hotkey_window = tk.Toplevel(self)
        hotkey_window.title("Hotkey Settings")
        hotkey_window.grab_set()  # Grab the focus on this toplevel window

        main_frame = ttk.Frame(hotkey_window, padding="10")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create dropdowns for each hotkey
        keys = ["", "ctrl", "shift", "alt", "tab", "altgr"]
        main_keys = list("abcdefghijklmnopqrstuvwxyz1234567890[];'#,./`") + \
                [f"f{i}" for i in range(1, 13)]  # Add function keys F1 to F12

        def create_hotkey_row(label_text, key_combo):
            ttk.Label(main_frame, text=label_text).grid(row=create_hotkey_row.row, column=0, sticky=tk.W, pady=2)

            var1 = tk.StringVar(value=key_combo[0] if len(key_combo) > 0 else "")
            var2 = tk.StringVar(value=key_combo[1] if len(key_combo) > 1 else "")
            var3 = tk.StringVar(value=key_combo[2] if len(key_combo) > 2 else "")

            option_menu1 = ttk.OptionMenu(main_frame, var1, key_combo[0], *keys)
            option_menu1.grid(row=create_hotkey_row.row, column=1, sticky=tk.W, pady=2)

            option_menu2 = ttk.OptionMenu(main_frame, var2, key_combo[1] if len(key_combo) > 1 else "", *keys)
            option_menu2.grid(row=create_hotkey_row.row, column=2, sticky=tk.W, pady=2)

            option_menu3 = ttk.OptionMenu(main_frame, var3, key_combo[2] if len(key_combo) > 2 else "", *main_keys)
            option_menu3.grid(row=create_hotkey_row.row, column=3, sticky=tk.W, pady=2)

            create_hotkey_row.row += 1
            return [var1, var2, var3]

        create_hotkey_row.row = 0

        record_start_stop_vars = create_hotkey_row("Record Start/Stop:", settings["hotkeys"]["record_start_stop"])
        stop_recording_vars = create_hotkey_row("Stop Recording:", settings["hotkeys"]["stop_recording"])
        play_last_audio_vars = create_hotkey_row("Play Last Audio:", settings["hotkeys"]["play_last_audio"])

        # Save Button
        save_btn = ttk.Button(main_frame, text="Save", command=lambda: self.save_hotkey_settings({
            "record_start_stop": [record_start_stop_vars[0].get(), record_start_stop_vars[1].get(), record_start_stop_vars[2].get()],
            "stop_recording": [stop_recording_vars[0].get(), stop_recording_vars[1].get(), stop_recording_vars[2].get()],
            "play_last_audio": [play_last_audio_vars[0].get(), play_last_audio_vars[1].get(), play_last_audio_vars[2].get()]
        }))
        save_btn.grid(row=create_hotkey_row.row, column=1, sticky=tk.W + tk.E, pady=10)

    
    def save_hotkey_settings(self, hotkeys):
        settings = self.load_settings()
        settings["hotkeys"] = hotkeys
        self.save_settings_to_JSON(settings)
        self.setup_hotkeys()  # Re-register the hotkeys with the new settings
        messagebox.showinfo("Settings Updated", "Your hotkey settings have been saved successfully.")

    def setup_hotkeys(self):
        try:
            # Attempt to clear existing hotkeys
            keyboard.unhook_all()  # This should clear all hotkeys in some versions of the library.
        except AttributeError:
            pass  # Ignore if the method isn't supported

        settings = self.load_settings()

        def parse_hotkey(combo):
            return '+'.join(filter(None, combo))

        keyboard.add_hotkey(parse_hotkey(settings["hotkeys"]["record_start_stop"]), lambda: self.hotkey_record_trigger())
        keyboard.add_hotkey(parse_hotkey(settings["hotkeys"]["stop_recording"]), lambda: self.hotkey_stop_trigger())
        keyboard.add_hotkey(parse_hotkey(settings["hotkeys"]["play_last_audio"]), lambda: self.hotkey_play_last_audio_trigger())


    def hotkey_play_last_audio_trigger(self):
        if hasattr(self, 'last_audio_file'):
            self.play_last_audio()
        else:
            self.play_sound('assets/no-last-audio.wav')
            

    def hotkey_stop_trigger(self):
        self.play_sound('assets/wrong-short.wav')
        if self.recording:
            self.stop_recording(auto_play=False)
            self.recording=False
        
    # Sounds from https://mixkit.co/free-sound-effects/notification/
    def hotkey_record_trigger(self):

        if self.recording:
            self.play_sound('assets/pop.wav')
            self.submit_text()
        else:

            if not self.recording:
                self.start_recording(play_confirm_sound=True)
            else:
                self.stop_recording(auto_play=True)






    def play_sound(self, sound_file):
        player = AudioPlayer(self.resource_path(sound_file))
        player.play(block=True) 

    def resource_path(self, relative_path):
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




    def initialize_gui(self):

        self.input_device_index = tk.StringVar(self)
        self.device_index = tk.StringVar(self)
        self.device_index_2 = tk.StringVar(self)

        self.input_device_index.set("Default")
        self.device_index.set("Select Device")
        self.device_index_2.set("None")

        # Fetching available devices (no longer needed here?)
        #available_devices = self.get_audio_devices()
        #available_input_devices = self.get_input_devices()
        #device_names = list(self.available_devices.keys())
        #input_device_names = list(self.available_input_devices.keys())

        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Voice Selection
        self.voice_var = tk.StringVar()
        voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        ttk.Label(main_frame, text="Voice").grid(column=0, row=0, sticky=tk.W, pady=(10, 10))  # Padding added
        voice_menu = ttk.OptionMenu(main_frame, self.voice_var,'fable', *voices)
        voice_menu.grid(column=1, row=0, sticky=tk.W)

        # Microphone Selection Setup
        ttk.Label(main_frame, text="Input Device (optional):").grid(column=0, row=1, sticky=tk.W, pady=(5, 10))  # Padding added
        input_device_menu = ttk.OptionMenu(main_frame, self.input_device_index, "None", *self.available_input_devices.keys())
        input_device_menu.grid(column=1, row=1, sticky=tk.W)

        # Select Primary audio device
        ttk.Label(main_frame, text="Primary Playback Device:").grid(column=0, row=2, sticky=tk.W, pady=(10, 10))  # Padding added
        primary_device_menu = ttk.OptionMenu(main_frame, self.device_index, *self.available_devices.keys())
        primary_device_menu.grid(column=1, row=2, sticky=tk.W)

        # Select Secondary audio device
        ttk.Label(main_frame, text="Secondary Playback Device (optional):").grid(column=0, row=3, sticky=tk.W, pady=(5, 10))  # Padding added
        secondary_device_menu = ttk.OptionMenu(main_frame, self.device_index_2, "None", *self.available_devices.keys())
        secondary_device_menu.grid(column=1, row=3, sticky=tk.W)


        spacer = ttk.Frame(main_frame, height=20)  # Adjust height as needed
        spacer.grid(column=0, row=4, columnspan=2)  # Place spacer in the grid


        # Text to Read Label
        ttk.Label(main_frame, text="Text to Read:").grid(column=0, row=5, sticky=tk.W, pady=(10, 0))

        # Create a frame to contain the dropdown and save button
        save_frame = ttk.Frame(main_frame)
        save_frame.grid(column=1, row=5, sticky=tk.E, padx=(5, 0), pady=(5, 0))  # Align to the top right

        # Preset Category dropdown
        self.category_var = tk.StringVar(value="Select Category")
        categories = [cat["category"] for cat in self.presets]
        category_menu = ttk.OptionMenu(save_frame, self.category_var, *categories)
        category_menu.grid(column=0, row=0, sticky=tk.E, padx=(0, 5))  # Adjust padding for alignment

        # Save button, reduced size
        save_button = ttk.Button(save_frame, text="Save", width=8, command=self.save_current_text_as_preset)

        save_button.grid(column=1, row=0, sticky=tk.E)  # Align to the right
        
        # Specify the text to read
        self.text_input = tk.Text(main_frame, height=5, width=68)
        self.text_input.grid(column=0, row=6, columnspan=2, pady=(0, 20), sticky="nsew")  # Fill available width




        

        # Button configuration

        self.recording = False  # State to check if currently recording
        self.record_button = ttk.Button(main_frame, text="Record Mic", command=self.toggle_recording)
        self.record_button.grid(column=0, row=7, sticky=tk.W + tk.E, pady=(0, 20), padx=(0, 10))  # Left padding to separate buttons

        self.submit_button = ttk.Button(main_frame, text="Play Audio", style="Green.TButton", command=self.submit_text )
        self.submit_button.grid(column=1, row=7, sticky=tk.W + tk.E, pady=(0, 20), padx=(10, 0))  # Right padding to separate buttons




        self.create_presets_section()


        #Credits
        info_label = tk.Label(main_frame, text="Created by Scorchsoft.com App Development", fg="blue", cursor="hand2")
        info_label.grid(column=0, row=10, columnspan=2, pady=(0, 0))
        info_label.bind("<Button-1>", lambda e: self.open_scorchsoft())



    def create_presets_section(self):
        # Accordion frame to show/hide presets section
        self.presets_frame = ttk.Frame(self)
        self.presets_button = ttk.Button(self, text="▶ Presets", command=self.toggle_presets)
        self.presets_button.grid(column=0, row=8, columnspan=2, sticky=tk.W)
        self.presets_frame.grid(column=0, row=9, columnspan=2, sticky=(tk.W, tk.E))

        # Tabs for categories with scrolling arrows
        self.tab_frame = ttk.Frame(self.presets_frame)
        self.tab_frame.pack(fill=tk.X)

        # Thinner left arrow for tabs
        self.left_arrow = ttk.Button(self.tab_frame, text="◀", command=self.scroll_left, width=2, style="Flat.TButton")
        self.left_arrow.pack(side=tk.LEFT, padx=1)  # Reduced padding

        # Canvas for scrolling tabs horizontally, removing the horizontal scrollbar
        self.tabs_canvas = Canvas(self.tab_frame, height=30)
        self.tabs_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tabs_frame_inner = ttk.Frame(self.tabs_canvas)
        self.tabs_canvas.create_window((0, 0), window=self.tabs_frame_inner, anchor="nw")

        # Thinner right arrow for tabs
        self.right_arrow = ttk.Button(self.tab_frame, text="▶", command=self.scroll_right, width=2, style="Flat.TButton")
        self.right_arrow.pack(side=tk.RIGHT, padx=1)  # Reduced padding

        # Presets display area with a fixed height and vertical scrollbar
        self.presets_canvas = Canvas(self.presets_frame, height=250, width=self.presets_frame.winfo_width())
        self.presets_scrollbar = Scrollbar(self.presets_frame, orient="vertical", command=self.presets_canvas.yview)
        self.presets_canvas.configure(yscrollcommand=self.presets_scrollbar.set)

        # Frame inside the canvas to hold presets
        self.presets_scrollable_frame = ttk.Frame(self.presets_canvas)
        self.presets_canvas.create_window((0, 0), window=self.presets_scrollable_frame, anchor="nw")

        # Pack the canvas and scrollbar
        self.presets_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.presets_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the scroll region to update when the frame changes
        self.presets_scrollable_frame.bind("<Configure>", lambda e: self.presets_canvas.configure(scrollregion=self.presets_canvas.bbox("all")))

        # Populate tabs and presets
        self.populate_tabs()
        self.refresh_presets_display()
        self.toggle_presets()
        self.toggle_presets()
        self.enable_mouse_wheel_scrolling()



    def scroll_left(self):
        self.tabs_canvas.xview_scroll(-5, "units")

    def scroll_right(self):
        self.tabs_canvas.xview_scroll(5, "units")


    def enable_mouse_wheel_scrolling(self):
        """Enable conditional mouse wheel scrolling for the presets canvas and category tabs canvas."""

        def on_vertical_scroll(event):
            # Scroll the presets_canvas vertically
            if event.num == 4:  # macOS scroll up
                self.presets_canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # macOS scroll down
                self.presets_canvas.yview_scroll(1, "units")
            else:  # Windows and Linux
                self.presets_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_horizontal_scroll(event):
            # Scroll the tabs_canvas horizontally
            if event.num == 4:  # macOS scroll left
                self.tabs_canvas.xview_scroll(-1, "units")
            elif event.num == 5:  # macOS scroll right
                self.tabs_canvas.xview_scroll(1, "units")
            else:  # Windows and Linux
                self.tabs_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        # Bind scroll events when mouse enters or leaves the presets canvas area
        self.presets_canvas.bind("<Enter>", lambda e: self.presets_canvas.bind_all("<MouseWheel>", on_vertical_scroll))
        self.presets_canvas.bind("<Leave>", lambda e: self.presets_canvas.unbind_all("<MouseWheel>"))

        # Bind scroll events when mouse enters or leaves the tabs canvas area
        self.tabs_canvas.bind("<Enter>", lambda e: self.tabs_canvas.bind_all("<MouseWheel>", on_horizontal_scroll))
        self.tabs_canvas.bind("<Leave>", lambda e: self.tabs_canvas.unbind_all("<MouseWheel>"))


    
    def open_scorchsoft(self, event=None):
        webbrowser.open('https://www.scorchsoft.com')




    def show_hotkey_instructions(self):
        instruction_window = tk.Toplevel(self)
        instruction_window.title("Hotkey Instructions")
        instruction_window.geometry("400x300")  # Width x Height

        instructions = """How to use Hotkeys
ctrl+shift+0
This starts a recording, then converts to text and plays when you press this hotkey again.

ctrl+shift+9
If you are recording, you can press this hotkey to stop recording without playing

ctrl+shift+8
This replays the last audio clip played

        """
        tk.Label(instruction_window, text=instructions, justify=tk.LEFT, wraplength=380).pack(padx=10, pady=10)
        
        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0))

    def show_instructions(self):
        instruction_window = tk.Toplevel(self)
        instruction_window.title("How to Use")
        instruction_window.geometry("600x680")  # Width x Height

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

4. Select a playback device. I recommend you select one device to be your headphones, and the other the virtuall microphone installed above (Which is usually labelled "Cable Input (VB-Audio))"

3. Enter the text in the provided text area that you want to convert to speech.

4. Click 'Submit' to hear the spoken version of your text.

5. The 'Play Last Audio' button can be used to replay the last generated speech output.

6. You can change the API key at any time under the 'Settings' menu.

This tool was brought to you by Scorchsoft - We build custom apps to your requirements. Please contact us if you have a requirement for a custom app project.

If you like this tool then please help us out and give us a backlink to help others find it at:
https://www.scorchsoft.com/blog/text-to-mic-for-meetings/

Please also make sure you read the Terms of use and licence statement before using this app."""
        
        tk.Label(instruction_window, text=instructions, justify=tk.LEFT, wraplength=580).pack(padx=10, pady=10)
        
        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0))


    def show_terms_of_use(self):
        # Get the path to the LICENSE.md file using the resource_path method
        license_path = self.resource_path("LICENSE.md")

        # Attempt to read the content of the LICENSE.md file
        try:
            # Open the file with 'r' (read mode) and specify 'utf-8' encoding
            with open(license_path, "r", encoding="utf-8") as file:
                license_content = file.read()
        except FileNotFoundError:
            license_content = "License file not found. Please ensure the LICENSE.md file exists in the application directory."
        except PermissionError:
            license_content = "Permission denied. Please ensure the script has read access to LICENSE.md."
        except UnicodeDecodeError as e:
            license_content = f"Error reading license file due to encoding issue: {e}"
        except Exception as e:
            license_content = f"An unexpected error occurred while reading the license file: {e}"

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
            mac_path = self.get_app_support_path_mac()
            #return self.get_app_support_path_mac() / filename
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
        
        # Convert device names to indices
        primary_index = self.available_devices.get(self.device_index.get(), None)
        secondary_index = self.available_devices.get(self.device_index_2.get(), None) if self.device_index_2.get() != "None" else None

        if primary_index is None:
            messagebox.showerror("Error", "Primary device not selected or unavailable.")
            return
        
        print(f"Primary Index: {primary_index}, Secondary Index: {secondary_index}")

        try:

            response = self.client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=text,
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

        p = pyaudio.PyAudio()
        streams = []
        
        try:
            # Open all files and start all streams
            for file_path, device_index in zip(file_paths, device_indices):

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
                        #if mismatch, make a new resampled version that matches the output device
                        resampled_file_path = self.resample_audio(str(file_path), sample_rate)
                        #update the playback file to the new resampled file
                        file_path = resampled_file_path
                        #re-open the new file for processing
                        wf = wave.open(str(file_path), 'rb')
                  
                    #Create a stream from our file
                    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                    channels=wf.getnchannels(),
                                    rate=sample_rate,
                                    output=True,
                                    output_device_index=int(device_index))
                    
                except Exception as e:
                    messagebox.showerror("Stream Creation Error", f"Failed to create audio stream for device index {device_index}: {str(e)}")
                    wf.close()
                    continue

                streams.append((stream, wf))

            # Play interleaved
            active_streams = len(streams)
            while active_streams > 0:
                for stream, wf in streams:
                    data = wf.readframes(1024)
                    if data:
                        stream.write(data)
                    else:
                        stream.stop_stream()
                        stream.close()
                        wf.close()
                        streams.remove((stream, wf))
                        active_streams -= 1

        except Exception as e:
            messagebox.showerror("Playback Error", f"Error during multiplexed playback: {e}")
        finally:
            p.terminate()


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

            
    def change_api_key(self):
        new_key = simpledialog.askstring("API Key", "Enter new OpenAI API Key:", parent=self)
        if new_key:
            self.save_api_key(new_key)
            self.api_key = new_key
            self.client = OpenAI(api_key=self.api_key)
            messagebox.showinfo("API Key Updated", "The OpenAI API Key has been updated successfully.")


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

        #Record to GUI selected device ID
        #device_id = None if self.input_device_index.get() == "Default" else input_devices[self.input_device_index.get()]

        if input_device_id is None:
            messagebox.showerror("Error", "Selected audio device is not available.")
            return
        
        try:
            self.recording = True
            self.record_button.config(text="Stop and Insert", style='Recording.TButton')
            self.submit_button.config(text="Stop and Play", style='Recording.TButton')

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
        if self.record_thread:
            self.record_thread.join()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.p:
            self.p.terminate()

        if cancel_save==False:
            self.save_recording(auto_play=auto_play)
        
        self.record_button.config(text="Record Mic", style='TButton')  # Revert to default style
        self.submit_button.config(text="Play", style='Green.TButton')  # Revert to default style


    def save_recording(self, auto_play = False):
        file_path = "output.wav"
        wf = wave.open(file_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print("Recording saved.")

        self.after(0, self.transcribe_audio, file_path, auto_play)
    



    def transcribe_audio(self, file_path, auto_play = False):
        try:
            with open(str(file_path), "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-1",
                    response_format="verbose_json"
                )

            settings = self.load_settings()

            if settings["chat_gpt_completion"] and settings["auto_apply_ai_to_recording"]:
                auto_apply_ai = settings["auto_apply_ai_to_recording"]
            else:
                auto_apply_ai = False

            print(f"auto_apply_ai: {auto_apply_ai}")

            if auto_apply_ai:
                print("applying ai")
                play_text = self.apply_ai(transcription.text)
            else:
                print("outputting without ai")
                #This prevents issues with trying to upload TK after thread operations
                #whcih can cause crashes with no error displayed
                self.text_input.delete("1.0", tk.END)  # Clear existing text
                self.text_input.insert("1.0", transcription.text)  # Insert new text
                play_text = transcription.text

            if auto_play:
                #self.submit_text(play_text = playtext)#
                print(f"Triggering auto play with: {play_text} ")
                self.submit_text_helper(play_text = play_text)
                # TODO: PLAY THE TEXT IMMEDIATELY
            
            print("Transcription Complete: The audio has been transcribed and the text has been placed in the input area.")
            #messagebox.showinfo("Transcription Complete", "The audio has been transcribed and the text has been placed in the input area.")
        
        except Exception as e:
            print(f"Transcription error: An error occurred during transcription: {str(e)}")
    

    def load_settings(self):
        settings_file = self.get_settings_file_path("settings.json")
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
        except FileNotFoundError:
            # Default settings
            settings = {
                "chat_gpt_completion": False,
                "model": self.default_model,
                "prompt": "",
                "auto_apply_ai_to_recording": False,
                "hotkeys": {
                    "record_start_stop": ["ctrl", "shift", "0"],
                    "stop_recording": ["ctrl", "shift", "9"],
                    "play_last_audio": ["ctrl", "shift", "8"]
                }
            }
            self.save_settings_to_JSON(settings)
        return settings

    def save_settings_to_JSON(self, settings):
        settings_file = self.get_settings_file_path("settings.json")
        
        with open(settings_file, "w") as f:
            json.dump(settings, f)

    def get_settings_file_path(self, filename):
        if platform.system() == 'Darwin':  # Check if the OS is macOS
            mac_path = self.get_app_support_path_mac()
            return f"{mac_path}/{filename}"
        else:
            return filename  # Default to current directory for non-macOS systems
        
    def chat_gpt_settings(self):
        settings = self.load_settings()
        settings_window = tk.Toplevel(self)
        settings_window.title("ChatGPT Manipulation Settings")
        settings_window.grab_set()  # Grab the focus on this toplevel window

        main_frame = ttk.Frame(settings_window, padding="10")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Use the ttk style for uniformity
        style = ttk.Style()
        style.theme_use('clam')

        enable_completion = tk.BooleanVar(value=settings.get("chat_gpt_completion", False))
        ttk.Checkbutton(main_frame, text="Enable ChatGPT Completion", variable=enable_completion).grid(row=0, column=1, sticky=tk.W, pady=2)

        # Model selection#


        model_var = tk.StringVar(value=settings.get("model", self.default_model))
        ttk.Label(main_frame, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=2)
        model_menu = ttk.OptionMenu(main_frame, model_var, model_var.get(), *self.available_models)
        model_menu.grid(row=1, column=1, sticky=tk.W, pady=2)

        # Max Tokens selection
        max_tokens_var = tk.IntVar(value=settings.get("max_tokens", 750))
        ttk.Label(main_frame, text="Max Tokens:").grid(row=2, column=0, sticky=tk.W, pady=2)
        max_tokens_menu = ttk.OptionMenu(main_frame, max_tokens_var, 750, 100, 250, 500, 750, 1000, 1250, 1500)
        max_tokens_menu.grid(row=2, column=1, sticky=tk.W, pady=2)

        # Prompt entry as a Text area
        ttk.Label(main_frame, text="Prompt:").grid(row=3, column=0, sticky=tk.NW, pady=2)
        prompt_entry = tk.Text(main_frame, height=4, width=40)
        prompt_entry.insert('1.0', settings.get("prompt", ""))
        prompt_entry.grid(row=3, column=1, sticky=tk.W, pady=2)

        # Auto-apply checkbox
        auto_apply = tk.BooleanVar(value=settings.get("auto_apply_ai_to_recording", False))
        ttk.Checkbutton(main_frame, text="Auto Apply to Recorded Transcript", variable=auto_apply).grid(row=4, column=1, sticky=tk.W, pady=2)

        # Save Button
        save_btn = ttk.Button(main_frame, text="Save", command=lambda: self.save_chat_gpt_settings({
            "chat_gpt_completion": enable_completion.get(),
            "model": model_var.get(),
            "prompt": prompt_entry.get("1.0", tk.END).strip(),
            "auto_apply_ai_to_recording": auto_apply.get(),
            "max_tokens": max_tokens_var.get()
        }))
        save_btn.grid(row=5, column=1, sticky=tk.W + tk.E, pady=10)

    def save_chat_gpt_settings(self, settings):
        self.save_settings_to_JSON(settings)
        messagebox.showinfo("Settings Updated", "Your settings have been saved successfully.")
        self.load_settings()  # Refresh settings if needed elsewhere

    def apply_ai(self, input_text=None):

        if input_text is None:
            print("Will apply AI to UI input box")
            text = self.text_input.get("1.0", tk.END).strip()
        else:
            print("Will apply AI to input_text")
            text = input_text

        settings = self.load_settings()

        if settings["chat_gpt_completion"] and settings["max_tokens"]:
            var_max_tokens = settings["max_tokens"]
        else:
            var_max_tokens = 750

        print(f"GPT Settings: {settings}")
        print(f"Max Tokens: {var_max_tokens}")

        if settings["chat_gpt_completion"]:
            # Assuming OpenAI's completion method is configured correctly
            response = self.client.chat.completions.create(
                model=settings["model"],
                messages=[
                    {"role": "system", "content": settings["prompt"] },
                    {"role": "user", "content": "\n\n# Apply to the following (Do not output system prompt or hyphens markup or anything before this line):\n\n-----\n\n" + text + "\n\n-----"}],
                max_tokens=750
            )
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", response.choices[0].message.content)

            return_text = response.choices[0].message.content
        else:
            return_text = text

        return return_text




    def populate_tabs(self):
        # Clear current tabs
        for widget in self.tabs_frame_inner.winfo_children():
            widget.destroy()

        # Add "All" and "Favourites" tabs along with dynamic categories
        for category in ["All", "Favourites"] + [cat["category"] for cat in self.presets if cat["category"] not in ["All", "Favourites"]]:
            btn = ttk.Button(self.tabs_frame_inner, text=category, command=lambda c=category: self.switch_category(c))
            btn.pack(side=tk.LEFT, padx=2)

            # Style selected category
            if category == self.current_category:
                btn.state(['pressed'])  # Visual style for selected tab
            else:
                btn.state(['!pressed'])

    def switch_category(self, category):
        """Switch displayed category."""
        self.current_category = category
        self.populate_tabs()  # Refresh tabs to show selection
        self.refresh_presets_display()

    def refresh_presets_display(self):
        """Refresh displayed presets based on selected category."""

        # Clear existing items in the scrollable frame
        for widget in self.presets_scrollable_frame.winfo_children():
            widget.destroy()

        # Debounce - cancel any previous refresh call if pending
        if hasattr(self, 'refresh_handle'):
            self.after_cancel(self.refresh_handle)
        self.refresh_handle = self.after(100, self._populate_presets)

    def _populate_presets(self):
        """Populate presets into grid layout with responsive columns."""
        # Filter presets based on current category
        display_phrases = []
        if self.current_category == "All":
            for cat in self.presets:
                display_phrases.extend(cat["phrases"])
        elif self.current_category == "Favourites":
            for cat in self.presets:
                display_phrases.extend([p for p in cat["phrases"] if p["isFavourite"]])
        else:
            display_phrases = next((cat["phrases"] for cat in self.presets if cat["category"] == self.current_category), [])

        # Update canvas width to calculate dynamic column width
        self.presets_canvas.update_idletasks()
        preset_width = max(self.presets_canvas.winfo_width() // 3, 150)  # Minimum width of 100
        preset_height = 100

        print(f"preset width: {preset_width}")

        # Configure columns to fill available space
        for col in range(3):
            self.presets_scrollable_frame.columnconfigure(col, weight=1)


        # Populate filtered presets in grid layout
        for i, phrase in enumerate(display_phrases):
            frame = ttk.Frame(self.presets_scrollable_frame, width=preset_width, height=preset_height, relief="solid", borderwidth=1)
            frame.grid(row=i // 4, column=i % 4, padx=2, pady=2, sticky="nsew")
            frame.grid_propagate(False)

            self.presets_scrollable_frame.grid_columnconfigure(i % 4, weight=1)  # Make columns expandable
            self.presets_scrollable_frame.grid_rowconfigure(i // 4, weight=1)    # Make rows expandable



            # Text label with truncation for long text
            wrapped_text = self.wrap_text(phrase["text"], max_lines=3, max_chars_per_line=20)
            label = ttk.Label(frame, text=wrapped_text, anchor="center", justify="center", width=20)
            label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            label.bind("<Button-1>", lambda e, t=phrase["text"]: self.insert_text(t))
            label.bind("<Double-Button-1>", lambda e, t=phrase["text"]: self.play_preset(t))

            # Bottom frame for icons
            bottom_frame = ttk.Frame(frame)
            bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

            self.style.configure("Flat.TButton",
                     borderwidth=0,
                     highlightthickness=0,
                     font=("Arial", 12),  # Adjust font and size
                     anchor="center")     # Center text


            # Favourite button
            fav_icon = "❤️" if phrase["isFavourite"] else "♡"
            fav_btn = ttk.Button(bottom_frame, text=fav_icon, command=lambda p=phrase: self.toggle_favourite(p), width=2, style="Flat.TButton")
            fav_btn.pack(side=tk.RIGHT, padx=2)
            #fav_btn.config(borderwidth=0, highlightthickness=0)  # Remove border

            # Delete button
            del_btn = ttk.Button(bottom_frame, text="🗑️", command=lambda t=phrase["text"]: self.delete_preset(self.current_category, t), width=2, style="Flat.TButton")
            del_btn.pack(side=tk.RIGHT, padx=2)
            #del_btn.config(borderwidth=0, highlightthickness=0)  # Remove border


        # Update scroll region after populating all items
        self.presets_canvas.configure(scrollregion=self.presets_canvas.bbox("all"))


    def wrap_text(self, text, max_lines=3, max_chars_per_line=20):
        """Wrap text to fit within a limited number of lines and characters."""
        words = text.split()
        wrapped_text = ""
        line = ""
        line_count = 0

        for word in words:
            if len(line + word) <= max_chars_per_line:
                line += word + " "
            else:
                wrapped_text += line.strip() + "\n"
                line = word + " "
                line_count += 1
                if line_count >= max_lines - 1:  # Leave space for ellipsis
                    break

        # Add final line and handle overflow with ellipsis
        wrapped_text += line.strip()
        if line_count >= max_lines - 1 and len(wrapped_text.splitlines()) >= max_lines:
            wrapped_text = "\n".join(wrapped_text.splitlines()[:max_lines - 1]) + "\n..."

        return wrapped_text



    def insert_text(self, text):
        """Insert preset text into the text area."""
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", text)

    def play_preset(self, text):
        """Insert text and play audio immediately."""
        self.insert_text(text)
        self.submit_text()

    def toggle_favourite(self, phrase):
        """Toggle the favourite status of a preset."""
        phrase["isFavourite"] = not phrase["isFavourite"]
        self.save_presets()
        self.refresh_presets_display()

    def toggle_presets(self):
        if self.presets_collapsed:
            self.presets_frame.grid()
            self.presets_button.config(text="▼ Presets")
            self.geometry(self.default_geometry)  
        else:
            self.presets_frame.grid_remove()
            self.presets_button.config(text="▶ Presets")
            self.geometry("590x460") 
        self.presets_collapsed = not self.presets_collapsed


    def save_current_text_as_preset(self):
        """Save current text to the selected category as a preset."""
        text = self.text_input.get("1.0", tk.END).strip()
        category = self.category_var.get()
        if text and category != "Select Category":
            self.add_preset(category, text, is_favourite=False)
            # Show success message with category information
            messagebox.showinfo("Save Successful", f"The text has been successfully saved to the category: '{category}'.")
        else:
            messagebox.showinfo("Error", "Please enter text and select a category before saving.")


    def load_presets(self):
        """Load presets from the JSON file, copying from example if necessary."""
        presets_path = Path("config/presets.json")
        example_path = self.resource_path("assets/presets.example.json")  # Path for the example file

        # Check if presets.json exists, and if not, copy presets.example.json to config
        if not presets_path.exists():
            try:
                # Ensure config directory exists
                presets_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy example presets to config directory
                with open(example_path, "r", encoding="utf-8") as example_file:
                    with open(presets_path, "w", encoding="utf-8") as config_file:
                        config_file.write(example_file.read())
            except Exception as e:
                messagebox.showerror("Error", f"Failed to copy example presets: {e}")
                return []  # Return empty if unable to load or copy presets

        # Load presets.json as usual
        try:
            with open(presets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("presets", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Error loading presets: {e}")
            return []  # Default to empty if load fails

    def save_presets(self):
        """Save presets to the JSON file."""
        data = {"presets": self.presets}
        with open("config/presets.json", "w") as f:
            json.dump(data, f, indent=2)

    def add_preset(self, category, text, is_favourite=False):
        """Add a new preset and save it."""
        for cat in self.presets:
            if cat["category"] == category:
                cat["phrases"].append({"text": text, "isFavourite": is_favourite})
                break
        else:
            # Add a new category if not found
            self.presets.append({"category": category, "phrases": [{"text": text, "isFavourite": is_favourite}]})
        self.save_presets()
        self.refresh_presets_display()

    def delete_preset(self, category, text):
        """Delete a preset by category and text."""
        for cat in self.presets:
            if cat["category"] == category:
                cat["phrases"] = [p for p in cat["phrases"] if p["text"] != text]
                break
        self.save_presets()
        self.refresh_presets_display()


