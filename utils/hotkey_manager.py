import tkinter as tk
from tkinter import ttk, messagebox
import keyboard
import platform

class HotkeyManager:
    """Class to handle hotkey operations."""
    
    def __init__(self, app):
        self.app = app
        self.hotkeys = []  # Track registered hotkeys
        self.is_mac = platform.system() == 'Darwin'
        self.setup_hotkeys()
    
    def setup_hotkeys(self):
        """Set up hotkeys based on settings."""
        # First, clear all existing hotkeys
        self.clear_hotkeys()
        
        settings = self.app.load_settings()

        # Register the hotkeys and track them
        self.register_hotkeys(settings["hotkeys"])
    
    def register_hotkeys(self, hotkey_settings):
        """Register hotkeys from settings and track them."""
        try:
            self.hotkeys.append(keyboard.add_hotkey(
                self.format_shortcut(hotkey_settings["record_start_stop"]), 
                lambda: self.hotkey_record_trigger()
            ))
            
            self.hotkeys.append(keyboard.add_hotkey(
                self.format_shortcut(hotkey_settings["stop_recording"]), 
                lambda: self.hotkey_stop_trigger()
            ))
            
            self.hotkeys.append(keyboard.add_hotkey(
                self.format_shortcut(hotkey_settings["play_last_audio"]), 
                lambda: self.hotkey_play_last_audio_trigger()
            ))
            
            # Add cancel operation hotkey
            self.hotkeys.append(keyboard.add_hotkey(
                self.format_shortcut(hotkey_settings["cancel_operation"]), 
                lambda: self.hotkey_cancel_operation_trigger()
            ))
            
            return True
        except Exception as e:
            print(f"Error registering hotkeys: {e}")
            return False
    
    def clear_hotkeys(self):
        """Clear all registered hotkeys."""
        try:
            # Clear tracked hotkeys
            for hotkey in self.hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                except:
                    pass
            self.hotkeys.clear()
            
            # Also attempt to use the more aggressive approach
            try:
                keyboard.unhook_all()
            except AttributeError:
                pass  # Ignore if the method isn't supported
            
            # Try to reset internal keyboard state
            try:
                keyboard._recording = False
                keyboard._pressed_events.clear()
                keyboard._physically_pressed_keys.clear()
                keyboard._logically_pressed_keys.clear()
            except Exception as e:
                print(f"Warning: Error while resetting keyboard state: {e}")
                
        except Exception as e:
            print(f"Error clearing hotkeys: {e}")
    
    def force_hotkey_refresh(self, callback=None):
        """Force a complete refresh of all hotkeys."""
        print("Forcing hotkey refresh")
        
        try:
            # Clear all existing keyboard hooks
            self.clear_hotkeys()
            
            # Get current settings
            settings = self.app.load_settings()
            
            # Re-register hotkeys
            success = self.register_hotkeys(settings["hotkeys"])
            
            if success and self.hotkeys:
                print(f"Hotkey refresh completed successfully with {len(self.hotkeys)} hotkeys")
                if callback:
                    callback(True)
                return True
            else:
                print("Failed to register hotkeys")
                if callback:
                    callback(False)
                messagebox.showerror("Hotkey Error", "Failed to re-register hotkeys.")
                return False
                
        except Exception as e:
            print(f"Error during hotkey refresh: {e}")
            if callback:
                callback(False)
            return False
    
    def verify_hotkeys(self):
        """Verify that hotkeys are working."""
        try:
            # Simple check if hotkeys are registered
            return len(self.hotkeys) > 0
        except:
            return False
    
    def format_shortcut(self, key_combo):
        """Format key combination consistently."""
        if isinstance(key_combo, (list, set)):
            # Convert to list if it's a set
            if isinstance(key_combo, set):
                key_combo = list(key_combo)
                
            # Filter out empty values first
            filtered_combo = list(filter(None, key_combo))
            
            # Define modifier order
            modifier_order = ['ctrl', 'alt', 'shift', 'win', 'command']
            
            # Split into modifiers and regular keys
            modifiers = [k for k in filtered_combo if k.lower() in modifier_order]
            regular_keys = [k for k in filtered_combo if k.lower() not in modifier_order]
            
            # Sort modifiers according to preferred order
            sorted_modifiers = sorted(modifiers, key=lambda x: modifier_order.index(x.lower()) if x.lower() in modifier_order else 999)
            
            # For regular keys, we don't want to sort them as they might be multiple characters
            # We only need one non-modifier key anyway
            if len(regular_keys) > 1:
                # Keep only the first non-modifier key to avoid confusion
                print(f"Warning: Multiple non-modifier keys detected: {regular_keys}. Using only: {regular_keys[0]}")
                regular_keys = [regular_keys[0]]
            
            # Combine sorted modifiers and regular keys
            combined_keys = sorted_modifiers + regular_keys
            
            # Make sure we have at least one key
            if not combined_keys:
                return ""
                
            # Join with plus signs
            return "+".join(combined_keys)
        elif isinstance(key_combo, str):
            # If it's already a string, split it and re-format it
            return self.format_shortcut(key_combo.split('+'))
        else:
            return ""
    
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
            # When stopping via hotkey, we want to correctly update UI for playback
            # We'll use the same methods as the button click handlers would use
            if hasattr(self.app, 'handle_submit_button_click'):
                # This will properly handle stopping recording and playing audio
                # with appropriate UI updates
                self.app.handle_submit_button_click(via_hotkey=True)
            else:
                # Fall back to the old behavior if the handler isn't available
                self.app.submit_text()
        else:
            if not self.app.recording:
                self.app.start_recording(play_confirm_sound=True)
            else:
                self.app.stop_recording(auto_play=True)
    
    def hotkey_cancel_operation_trigger(self):
        """Cancel current operation (recording or playback)."""
        print("Cancel operation hotkey triggered")
        
        # Play feedback sound first
        self.app.play_sound('assets/pop.wav')
        
        # For recording cancellation
        if self.app.recording:
            print("Canceling recording operation")
            # Schedule the stop_recording call on the main thread to avoid threading issues
            self.app.after(100, lambda: self._safe_cancel_recording())
            return
            
        # For playback cancellation
        if hasattr(self.app, 'is_playing') and self.app.is_playing:
            print("Canceling playback operation")
            # Schedule the stop_playback call on the main thread to avoid threading issues
            self.app.after(100, lambda: self._safe_cancel_playback())
            return
            
        print("No active operation to cancel")
    
    def _safe_cancel_recording(self):
        """Safely cancel recording on the main thread."""
        try:
            if self.app.recording:
                self.app.stop_recording(cancel_save=True)
                self.app.recording = False
                print("Recording cancelled successfully")
        except Exception as e:
            print(f"Error canceling recording: {e}")
    
    def _safe_cancel_playback(self):
        """Safely cancel playback on the main thread."""
        try:
            if hasattr(self.app, 'stop_playback') and callable(self.app.stop_playback):
                # This will also update the buttons through the stop_playback method
                self.app.stop_playback()
                print("Playback cancelled successfully")
                
                # Ensure buttons are reset (belt and suspenders approach)
                if hasattr(self.app, 'update_buttons_for_playback') and callable(self.app.update_buttons_for_playback):
                    self.app.update_buttons_for_playback(False)
        except Exception as e:
            print(f"Error canceling playback: {e}")
    
    @staticmethod
    def hotkey_settings_dialog(app):
        """Show the hotkey settings dialog with interactive key capture."""
        settings = app.load_settings()
        hotkey_window = tk.Toplevel(app)
        hotkey_window.title("Hotkey Settings")
        hotkey_window.grab_set()  # Grab the focus on this toplevel window
        
        # Temporarily suspend global hotkeys
        old_hotkeys = []
        if hasattr(app, 'hotkey_manager'):
            # Store current hotkeys
            old_hotkeys = app.hotkey_manager.hotkeys.copy()
            # Clear them while dialog is open
            app.hotkey_manager.clear_hotkeys()
        
        # Set size and center the window
        window_width = 500
        window_height = 400
        position_x = app.winfo_x() + (app.winfo_width() - window_width) // 2
        position_y = app.winfo_y() + (app.winfo_height() - window_height) // 2
        hotkey_window.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")

        main_frame = ttk.Frame(hotkey_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add title
        title_label = ttk.Label(
            main_frame, 
            text="Keyboard Shortcuts", 
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=(0, 15))

        # Create frame for shortcuts
        shortcuts_frame = ttk.Frame(main_frame)
        shortcuts_frame.pack(fill=tk.BOTH, expand=True)

        hotkey_manager = app.hotkey_manager if hasattr(app, 'hotkey_manager') else HotkeyManager(app)
        
        # Dictionary to store labels for each shortcut for easy updating
        shortcut_labels = {}

        # Function to handle shortcut editing
        def start_shortcut_edit(shortcut_name, button, label):
            # Add check for valid button
            if not button or not button.winfo_exists():
                print("Warning: Button no longer exists")
                return
            
            button.config(text="Press new shortcut...")
            
            # Track pressed keys and modifiers
            pressed_keys = set()
            currently_pressed = set()  # Track keys that are currently held down
            last_state = 0  # Track the last event state
            
            def on_key_press(event):
                nonlocal last_state
                last_state = event.state
                
                # Convert key to lowercase
                key = event.keysym.lower()
                
                # Debug print
                print(f"Key press - key: {key}")
                print(f"State bits: {format(event.state, '016b')}")
                print(f"State value: {event.state}")
                print(f"Currently pressed keys before: {currently_pressed}")
                
                # Map left/right modifier variants to their base form
                modifier_map = {
                    'control_l': 'ctrl', 'control_r': 'ctrl',
                    'alt_l': 'alt', 'alt_r': 'alt',
                    'shift_l': 'shift', 'shift_r': 'shift',
                    'super_l': 'win', 'super_r': 'win',
                    'win_l': 'win', 'win_r': 'win'
                }
                
                # Map for shift+number keys to their actual number
                shift_number_map = {
                    # Standard US layout shift+number keys
                    'exclam': '1',      # Shift+1
                    'at': '2',          # Shift+2
                    'numbersign': '3',  # Shift+3
                    'dollar': '4',      # Shift+4
                    'percent': '5',     # Shift+5
                    'asciicircum': '6', # Shift+6
                    'ampersand': '7',   # Shift+7
                    'asterisk': '8',    # Shift+8
                    'parenleft': '9',   # Shift+9
                    'parenright': '0',  # Shift+0
                    
                    # Additional keys for different keyboard layouts
                    'quotedbl': '2',    # Shift+2 on some layouts
                    'sterling': '3',    # Shift+3 on UK layout
                    'eacute': '2',      # French keyboards
                    'quoteleft': '`',   # Backtick
                    'asciitilde': '`',  # Shift+`
                    'equal': '=',       # Equal sign
                    'plus': '=',        # Shift+=
                    'minus': '-',       # Minus sign
                    'underscore': '-',  # Shift+-
                    'bracketleft': '[', # Left bracket
                    'braceleft': '[',   # Shift+[
                    'bracketright': ']', # Right bracket
                    'braceright': ']',  # Shift+]
                    'backslash': '\\',  # Backslash
                    'bar': '\\',        # Shift+\
                    'semicolon': ';',   # Semicolon
                    'colon': ';',       # Shift+;
                    'apostrophe': "'",  # Apostrophe
                    'comma': ',',       # Comma
                    'less': ',',        # Shift+,
                    'period': '.',      # Period
                    'greater': '.',     # Shift+.
                    'slash': '/',       # Slash
                    'question': '/'     # Shift+/
                }
                
                # Additional direct mappings for numeric keys - handle different representations
                numeric_keys_map = {
                    'kp_0': '0', 'kp_1': '1', 'kp_2': '2', 'kp_3': '3', 'kp_4': '4',
                    'kp_5': '5', 'kp_6': '6', 'kp_7': '7', 'kp_8': '8', 'kp_9': '9',
                    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
                    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
                }
                
                # Check if this is a shift+number key
                if key in shift_number_map:
                    key = shift_number_map[key]
                    print(f"Mapped shift+number key to: {key}")
                # Check if it's a numeric key with a different representation
                elif key in numeric_keys_map:
                    key = numeric_keys_map[key]
                    print(f"Mapped numeric key to: {key}")
                
                # Special handling for numpad keys which might come as "kp_1", "kp_2"
                elif key.startswith('kp_') and len(key) > 3:
                    mapped_key = key[3:]  # Strip the 'kp_' prefix
                    print(f"Mapped keypad key from {key} to {mapped_key}")
                    key = mapped_key
                    
                # Handle direct number key presses - these might be reported with character codes
                if event.char and event.char.isdigit() and not key.isdigit():
                    print(f"Detected digit character: {event.char}")
                    key = event.char
                
                # Add to currently pressed keys
                if key in modifier_map:
                    mod_key = modifier_map[key]
                    currently_pressed.add(mod_key)
                else:
                    # Only add non-modifier keys if they're actual keys (not just state changes)
                    if len(key) == 1 or key in ('left', 'right', 'up', 'down', 'space', 'tab', 'return', 
                                               'backspace', 'delete', 'escape', 'home', 'end', 'pageup', 
                                               'pagedown', 'insert', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6',
                                               'f7', 'f8', 'f9', 'f10', 'f11', 'f12'):
                        currently_pressed.add(key)
                    elif key:  # If it's any other non-empty key, add it anyway
                        print(f"Adding unrecognized key: {key}")
                        currently_pressed.add(key)
                        
                # Store the character directly if it exists and isn't already captured
                if event.char and event.char not in currently_pressed and event.char not in ('', ' '):
                    currently_pressed.add(event.char)
                
                # Update pressed_keys with all current keys
                pressed_keys.clear()
                pressed_keys.update(currently_pressed)
                
                # Add modifiers based on state
                if event.state & 0x4:
                    pressed_keys.add('ctrl')
                if event.state & 0x1:
                    pressed_keys.add('shift')
                if event.state & 0x20000:
                    pressed_keys.add('alt')
                if event.state & 0x40000 or 'win' in currently_pressed:
                    pressed_keys.add('win')
                
                print(f"Currently pressed keys after: {pressed_keys}")
                
                # Update button text to show current combination
                current_combo = "+".join(sorted(pressed_keys))
                button.config(text=f"Press: {current_combo}")
                
                return "break"
            
            def on_key_release(event):
                nonlocal currently_pressed
                key = event.keysym.lower()
                
                print(f"Key release - key: {key}")
                print(f"Key event char: {repr(event.char)}")
                print(f"Currently pressed before release: {currently_pressed}")
                
                # Map for shift+number keys to their actual number (same as in on_key_press)
                shift_number_map = {
                    # Standard US layout shift+number keys
                    'exclam': '1',      # Shift+1
                    'at': '2',          # Shift+2
                    'numbersign': '3',  # Shift+3
                    'dollar': '4',      # Shift+4
                    'percent': '5',     # Shift+5
                    'asciicircum': '6', # Shift+6
                    'ampersand': '7',   # Shift+7
                    'asterisk': '8',    # Shift+8
                    'parenleft': '9',   # Shift+9
                    'parenright': '0',  # Shift+0
                    
                    # Additional keys for different keyboard layouts
                    'quotedbl': '2',    # Shift+2 on some layouts
                    'sterling': '3',    # Shift+3 on UK layout
                    'eacute': '2',      # French keyboards
                    'quoteleft': '`',   # Backtick
                    'asciitilde': '`',  # Shift+`
                    'equal': '=',       # Equal sign
                    'plus': '=',        # Shift+=
                    'minus': '-',       # Minus sign
                    'underscore': '-',  # Shift+-
                    'bracketleft': '[', # Left bracket
                    'braceleft': '[',   # Shift+[
                    'bracketright': ']', # Right bracket
                    'braceright': ']',  # Shift+]
                    'backslash': '\\',  # Backslash
                    'bar': '\\',        # Shift+\
                    'semicolon': ';',   # Semicolon
                    'colon': ';',       # Shift+;
                    'apostrophe': "'",  # Apostrophe
                    'comma': ',',       # Comma
                    'less': ',',        # Shift+,
                    'period': '.',      # Period
                    'greater': '.',     # Shift+.
                    'slash': '/',       # Slash
                    'question': '/'     # Shift+/
                }
                
                # Additional direct mappings for numeric keys - handle different representations
                numeric_keys_map = {
                    'kp_0': '0', 'kp_1': '1', 'kp_2': '2', 'kp_3': '3', 'kp_4': '4',
                    'kp_5': '5', 'kp_6': '6', 'kp_7': '7', 'kp_8': '8', 'kp_9': '9',
                    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
                    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
                }
                
                # Check if this is a shift+number key
                if key in shift_number_map:
                    key = shift_number_map[key]
                    print(f"Mapped shift+number key release to: {key}")
                # Check if it's a numeric key with a different representation
                elif key in numeric_keys_map:
                    key = numeric_keys_map[key]
                    print(f"Mapped numeric key release to: {key}")
                # Special handling for numpad keys
                elif key.startswith('kp_') and len(key) > 3:
                    mapped_key = key[3:]  # Strip the 'kp_' prefix
                    print(f"Mapped keypad key release from {key} to {mapped_key}")
                    key = mapped_key
                    
                # Handle direct number key presses - these might be reported with character codes
                if event.char and event.char.isdigit() and not key.isdigit():
                    print(f"Detected digit character release: {event.char}")
                    key = event.char
                
                # Remove released key from currently pressed set
                if key in currently_pressed:
                    currently_pressed.remove(key)
                else:
                    # Try to find the key in currently_pressed by removing case, digit comparison, etc.
                    # This helps catch edge cases where the key representation changes between press and release
                    for pressed_key in list(currently_pressed):
                        # Check if it's the same key but with different case
                        if pressed_key.lower() == key.lower():
                            print(f"Found case-insensitive match: {pressed_key} for released key: {key}")
                            currently_pressed.remove(pressed_key)
                            break
                        # Check if both are digits but with different representations
                        elif (pressed_key.isdigit() and key.isdigit()) or \
                             (pressed_key == '0' and key == 'parenright') or \
                             (pressed_key in '0123456789' and key in numeric_keys_map.values()):
                            print(f"Found digit key match: {pressed_key} for released key: {key}")
                            currently_pressed.remove(pressed_key)
                            break
                
                # If we're releasing a character key, remove that character too
                if event.char and event.char in currently_pressed:
                    currently_pressed.remove(event.char)
                
                # Handle modifier key releases
                modifier_map = {
                    'control_l': 'ctrl', 'control_r': 'ctrl',
                    'alt_l': 'alt', 'alt_r': 'alt',
                    'shift_l': 'shift', 'shift_r': 'shift',
                    'super_l': 'win', 'super_r': 'win',
                    'win_l': 'win', 'win_r': 'win'
                }
                if key in modifier_map:
                    mod_key = modifier_map[key]
                    if mod_key in currently_pressed:
                        currently_pressed.remove(mod_key)
                
                print(f"Currently pressed after release: {currently_pressed}")
                
                # Process hotkey when all keys are released
                # Or when we have a complete valid hotkey (modifiers + key)
                has_complete_hotkey = (
                    len(pressed_keys) >= 2 and  # At least 2 keys 
                    any(mod in pressed_keys for mod in ('ctrl', 'alt', 'shift', 'win', 'command')) and  # Has modifier
                    any(k not in ('ctrl', 'alt', 'shift', 'win', 'command') for k in pressed_keys)  # Has non-modifier
                )
                
                # Either all keys are released, or we have a complete valid hotkey on key release
                if (not currently_pressed) or (has_complete_hotkey and key not in modifier_map):
                    try:
                        print(f"Processing hotkey: {pressed_keys}")
                        
                        # Check for empty pressed_keys
                        if not pressed_keys:
                            print("Warning: No keys in pressed_keys, aborting shortcut update")
                            button.config(text="Edit")
                            return
                        
                        # Create the shortcut string with consistent ordering
                        new_shortcut = hotkey_manager.format_shortcut(pressed_keys)
                        print(f"Formatted shortcut: '{new_shortcut}'")
                        
                        # Check if the formatting succeeded
                        if not new_shortcut:
                            print("Warning: format_shortcut returned empty string")
                            messagebox.showerror("Error", "Failed to format shortcut keys")
                            button.config(text="Edit")
                            return
                        
                        # Check if there's at least one modifier
                        has_modifier = any(mod in pressed_keys for mod in ('ctrl', 'alt', 'shift', 'win', 'command'))
                        
                        # Validate the shortcut
                        if not has_modifier:
                            messagebox.showerror("Error", 
                                "Please include at least one modifier key (Ctrl, Alt, Shift, or Win)")
                            button.config(text="Edit")
                            return
                        
                        # Check if there's a non-modifier key
                        has_key = any(k not in ('ctrl', 'alt', 'shift', 'win', 'command') for k in pressed_keys)
                        if not has_key:
                            # Keep waiting for a full key combo
                            return
                        
                        # Convert to list format for settings
                        # Get a sorted list of modifiers first
                        modifier_order = ['ctrl', 'alt', 'shift', 'win', 'command']
                        modifiers = sorted([k for k in pressed_keys if k in modifier_order], 
                                          key=lambda x: modifier_order.index(x))
                        
                        # Get the first non-modifier key
                        main_key = next((k for k in pressed_keys if k not in modifier_order), "")
                        
                        # Create the 3-element format: [modifier1, modifier2, main_key]
                        shortcut_list = [
                            modifiers[0] if len(modifiers) > 0 else "",
                            modifiers[1] if len(modifiers) > 1 else "",
                            main_key
                        ]
                        
                        print(f"Shortcut list: {shortcut_list}")
                        
                        # Update settings
                        settings = app.load_settings()
                        settings["hotkeys"][shortcut_name] = shortcut_list
                        app.save_settings_to_JSON(settings)
                        
                        # Update the label immediately with the newly formatted shortcut
                        label.config(text=new_shortcut)
                        # Ensure the update takes effect by forcing a UI update
                        label.update_idletasks()
                        
                        # Update button text
                        button.config(text="Edit")
                        button.update_idletasks()
                        
                        # Force a focus change to ensure the key events are processed
                        hotkey_window.focus_set()
                        
                        # Show a confirmation to the user
                        print(f"Shortcut updated to: '{new_shortcut}'")
                        
                    except Exception as e:
                        print(f"Error saving shortcut: {e}")
                        import traceback
                        traceback.print_exc()
                        messagebox.showerror("Error", f"Failed to update shortcut: {e}")
                        button.config(text="Edit")
                    
                    finally:
                        # Clear the sets
                        pressed_keys.clear()
                        currently_pressed.clear()
                        
                        # Remove key bindings
                        hotkey_window.unbind('<KeyPress>')
                        hotkey_window.unbind('<KeyRelease>')
            
            # Remove any existing bindings first
            hotkey_window.unbind('<KeyPress>')
            hotkey_window.unbind('<KeyRelease>')
            
            # Bind both key press and release events
            hotkey_window.bind('<KeyPress>', on_key_press)
            hotkey_window.bind('<KeyRelease>', on_key_release)

        # Add each shortcut with its edit button
        row = 0
        for name, key_combo in settings["hotkeys"].items():
            # Format readable name
            display_name = name.replace('_', ' ').title() + ":"
            
            # Format the current shortcut for display
            current_shortcut = hotkey_manager.format_shortcut(key_combo)
            
            # Create frame for this shortcut
            frame = ttk.Frame(shortcuts_frame)
            frame.pack(fill=tk.X, pady=5)
            
            # Add shortcut name
            name_label = ttk.Label(frame, text=display_name, width=20, anchor="w")
            name_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Add current shortcut
            shortcut_label = ttk.Label(frame, text=current_shortcut, width=15, anchor="w")
            shortcut_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Store label reference for easy access
            shortcut_labels[name] = shortcut_label
            
            # Add edit button
            edit_button = ttk.Button(
                frame, 
                text="Edit",
                width=10
            )
            edit_button.pack(side=tk.RIGHT)
            
            # Configure button command after creation to avoid stale references
            edit_button.configure(command=lambda n=name, b=edit_button, l=shortcut_label: 
                                 start_shortcut_edit(n, b, l))
            
            row += 1

        # Create a frame for the buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        # Add refresh button
        refresh_button = ttk.Button(
            button_frame,
            text="Save & Close",
            width=15,
            command=lambda: close_and_save()
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

        # Add reset to defaults button
        reset_button = ttk.Button(
            button_frame,
            text="Reset to Defaults",
            width=15,
            command=lambda: HotkeyManager.reset_shortcuts_to_default(app, hotkey_window)
        )
        reset_button.pack(side=tk.LEFT, padx=5)

        # Add note about Windows lock
        note_text = ("Note: If shortcuts stop working after unlocking Windows,\n"
                    "use this dialog to refresh them.")
        
        ttk.Label(
            main_frame, 
            text=note_text,
            justify=tk.CENTER,
            font=("Arial", 9),
            foreground="#666666"
        ).pack(pady=10)

        # Function to properly close the dialog and restore hotkeys
        def close_and_save():
            # Re-register global hotkeys before closing
            if hasattr(app, 'hotkey_manager'):
                app.hotkey_manager.force_hotkey_refresh()
                messagebox.showinfo("Settings Updated", "Your hotkey settings have been saved successfully.")
            hotkey_window.destroy()
        
        # Close button
        close_button = ttk.Button(
            main_frame,
            text="Cancel",
            command=lambda: cancel_and_close()
        )
        close_button.pack(pady=(5, 0))
        
        # Function to cancel without saving
        def cancel_and_close():
            # Re-register the original hotkeys
            if hasattr(app, 'hotkey_manager'):
                # Force reload from settings
                app.hotkey_manager.setup_hotkeys()
            hotkey_window.destroy()
        
        # Make sure hotkeys are re-registered when window is closed
        hotkey_window.protocol("WM_DELETE_WINDOW", cancel_and_close)
    
    @staticmethod
    def reset_shortcuts_to_default(app, parent_window=None):
        """Reset all keyboard shortcuts to their default values."""
        if parent_window is None:
            parent_window = app
            
        # Create custom confirmation dialog
        confirm = messagebox.askyesno(
            "Reset Shortcuts",
            "Are you sure you want to reset all keyboard shortcuts to their default values?",
            parent=parent_window
        )
        
        if confirm:
            try:
                # Default shortcuts
                is_mac = platform.system() == 'Darwin'
                default_shortcuts = {
                    "record_start_stop": ["ctrl", "shift", "0"],
                    "stop_recording": ["ctrl", "shift", "9"],
                    "play_last_audio": ["ctrl", "shift", "8"],
                    "cancel_operation": ["ctrl", "shift", "1"]
                }
                
                # Update settings
                settings = app.load_settings()
                settings["hotkeys"] = default_shortcuts
                app.save_settings_to_JSON(settings)
                
                # Refresh hotkeys
                def on_refresh_complete(success):
                    if success:
                        messagebox.showinfo(
                            "Success", 
                            "Shortcuts have been reset to defaults",
                            parent=parent_window
                        )
                        
                        # If this is a settings dialog, close and reopen it to refresh the UI
                        if parent_window != app and hasattr(parent_window, 'destroy'):
                            parent_window.destroy()
                            app.after(100, lambda: HotkeyManager.hotkey_settings_dialog(app))
                    else:
                        messagebox.showerror(
                            "Error", 
                            "Failed to register default shortcuts.",
                            parent=parent_window
                        )
                
                app.hotkey_manager.force_hotkey_refresh(callback=on_refresh_complete)
                
            except Exception as e:
                messagebox.showerror(
                    "Error", 
                    f"Failed to reset shortcuts: {e}",
                    parent=parent_window
                )
    
    @staticmethod
    def show_hotkey_instructions(parent):
        """Show instructions for using hotkeys."""
        instruction_window = tk.Toplevel(parent)
        instruction_window.title("Hotkey Instructions")
        instruction_window.geometry("600x500")  # Width x Height

        settings = parent.load_settings()
        
        # Format hotkeys consistently for display
        hotkey_manager = parent.hotkey_manager if hasattr(parent, 'hotkey_manager') else HotkeyManager(parent)
        record_shortcut = hotkey_manager.format_shortcut(settings["hotkeys"]["record_start_stop"])
        play_shortcut = hotkey_manager.format_shortcut(settings["hotkeys"]["play_last_audio"])
        stop_shortcut = hotkey_manager.format_shortcut(settings["hotkeys"]["stop_recording"])
        cancel_shortcut = hotkey_manager.format_shortcut(settings["hotkeys"]["cancel_operation"])

        instructions = f"""Available Hotkeys:

1. {record_shortcut} - Start/Stop Recording
   This hotkey toggles recording from your selected input device.

2. {play_shortcut} - Play Last Audio
   Play the most recently generated audio.

3. {stop_shortcut} - Stop Recording
   Immediately stops any active recording.

4. {cancel_shortcut} - Cancel Operation
   Cancels the current operation (recording or playback) without saving or processing.

These hotkeys work globally across your system, even when the app is minimized.
You can customize these hotkeys in Settings → Hotkey Settings.

If hotkeys stop working after your computer wakes from sleep or after unlocking your screen,
use Settings → Hotkey Settings → Refresh Hotkeys to restore functionality.

You can also access tone presets from Settings → Manage Tone Presets to modify how your text is spoken.
"""
        
        main_frame = ttk.Frame(instruction_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add scrolling text
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.insert(tk.END, instructions)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=text_widget.yview)
        
        # Add refresh button
        refresh_btn = ttk.Button(main_frame, text="Refresh Hotkeys", 
                               command=lambda: parent.hotkey_manager.force_hotkey_refresh(
                                   callback=lambda success: messagebox.showinfo("Hotkey Refresh", 
                                               "Hotkeys refreshed successfully" if success else "Failed to refresh hotkeys")
                               ))
        refresh_btn.pack(pady=(5, 10))
        
        # Add a close button
        ttk.Button(main_frame, text="Close", command=instruction_window.destroy).pack(pady=5) 

    def handle_ai_edit_hotkey(self):
        """Handle the hotkey for AI editing."""
        # Check if API key is available
        if not self.parent.has_api_key:
            messagebox.showinfo(
                "API Key Required",
                "AI copyediting requires an OpenAI API key.\n\n"
                "Please add your API key in Settings to use this feature."
            )
            return
        
        # Check if AI copy editing is enabled in settings
        settings = self.parent.load_settings()
        if not settings.get("chat_gpt_completion", False):
            messagebox.showinfo(
                "AI Copy Editing Disabled",
                "AI copy editing is currently disabled in settings.\n\n"
                "Please enable it in Settings → AI Copyediting before using this feature."
            )
            return
        
        # If we have an API key and AI is enabled, proceed with the AI editing
        self.parent.apply_ai_to_input() 