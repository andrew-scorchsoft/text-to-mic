import tkinter as tk
from tkinter import ttk, messagebox
import keyboard

class HotkeyManager:
    """Class to handle hotkey operations."""
    
    def __init__(self, app):
        self.app = app
        self.setup_hotkeys()
    
    def setup_hotkeys(self):
        """Set up hotkeys based on settings."""
        try:
            # Attempt to clear existing hotkeys
            keyboard.unhook_all()  # This should clear all hotkeys in some versions of the library.
        except AttributeError:
            pass  # Ignore if the method isn't supported

        settings = self.app.load_settings()

        def parse_hotkey(combo):
            return '+'.join(filter(None, combo))

        keyboard.add_hotkey(parse_hotkey(settings["hotkeys"]["record_start_stop"]), lambda: self.hotkey_record_trigger())
        keyboard.add_hotkey(parse_hotkey(settings["hotkeys"]["stop_recording"]), lambda: self.hotkey_stop_trigger())
        keyboard.add_hotkey(parse_hotkey(settings["hotkeys"]["play_last_audio"]), lambda: self.hotkey_play_last_audio_trigger())
    
    def hotkey_play_last_audio_trigger(self):
        """Trigger playing the last audio."""
        if hasattr(self.app, 'last_audio_file'):
            self.app.play_last_audio()
        else:
            self.app.play_sound('assets/no-last-audio.wav')
    
    def hotkey_stop_trigger(self):
        """Trigger stopping the recording."""
        self.app.play_sound('assets/wrong-short.wav')
        if self.app.recording:
            self.app.stop_recording(auto_play=False)
            self.app.recording = False
    
    def hotkey_record_trigger(self):
        """Trigger recording or stop recording and submit."""
        if self.app.recording:
            self.app.play_sound('assets/pop.wav')
            self.app.submit_text()
        else:
            if not self.app.recording:
                self.app.start_recording(play_confirm_sound=True)
            else:
                self.app.stop_recording(auto_play=True)
    
    @staticmethod
    def hotkey_settings_dialog(app):
        """Show the hotkey settings dialog."""
        settings = app.load_settings()
        hotkey_window = tk.Toplevel(app)
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
        save_btn = ttk.Button(main_frame, text="Save", command=lambda: HotkeyManager.save_hotkey_settings(app, {
            "record_start_stop": [record_start_stop_vars[0].get(), record_start_stop_vars[1].get(), record_start_stop_vars[2].get()],
            "stop_recording": [stop_recording_vars[0].get(), stop_recording_vars[1].get(), stop_recording_vars[2].get()],
            "play_last_audio": [play_last_audio_vars[0].get(), play_last_audio_vars[1].get(), play_last_audio_vars[2].get()]
        }))
        save_btn.grid(row=create_hotkey_row.row, column=1, sticky=tk.W + tk.E, pady=10)
    
    @staticmethod
    def save_hotkey_settings(app, hotkeys):
        """Save hotkey settings."""
        settings = app.load_settings()
        settings["hotkeys"] = hotkeys
        app.save_settings_to_JSON(settings)
        app.hotkey_manager.setup_hotkeys()  # Re-register the hotkeys with the new settings
        messagebox.showinfo("Settings Updated", "Your hotkey settings have been saved successfully.")
    
    @staticmethod
    def show_hotkey_instructions(parent):
        """Show instructions for using hotkeys."""
        instruction_window = tk.Toplevel(parent)
        instruction_window.title("Hotkey Instructions")
        instruction_window.geometry("600x400")  # Width x Height

        settings = parent.load_settings()
        record_shortcut = "+".join(filter(None, settings["hotkeys"]["record_start_stop"]))
        play_shortcut = "+".join(filter(None, settings["hotkeys"]["play_last_audio"]))
        stop_shortcut = "+".join(filter(None, settings["hotkeys"]["stop_recording"]))

        instructions = f"""Available Hotkeys:

1. {record_shortcut} - Start/Stop Recording
   This hotkey toggles recording from your selected input device.

2. {play_shortcut} - Play Last Audio
   Play the most recently generated audio.

3. {stop_shortcut} - Stop Recording
   Immediately stops any active recording.

These hotkeys work globally across your system, even when the app is minimized.
You can customize these hotkeys in Settings → Hotkey Settings.

You can also access tone presets from Settings → Manage Tone Presets to modify how your text is spoken.
"""
        
        tk.Label(instruction_window, text=instructions, justify=tk.LEFT, wraplength=580).pack(padx=10, pady=10)
        
        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0)) 