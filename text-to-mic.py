import tkinter as tk
import platform
from tkinter import ttk, messagebox, simpledialog, Menu
import os
import threading
import pyaudio
import wave
import webbrowser
import json
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path



# Load environment variables
load_dotenv()


class Application(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Scorchsoft Text to Mic")
        self.style = ttk.Style(self)
        if self.tk.call('tk', 'windowingsystem') == 'aqua':
            self.style.theme_use('aqua')
        else:
            self.style.theme_use('clam')  # Fallback to 'clam' on non-macOS systems

        #Define stules
        self.style.configure('Recording.TButton', background='red', foreground='white')
        self.style.configure("Green.TButton", background="green", foreground="white")


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

    def show_version(self):
        instruction_window = tk.Toplevel(self)
        instruction_window.title("App Version")
        instruction_window.geometry("300x150")  # Width x Height

        instructions = """Version 1.0.5\n\n App by Scorchsoft.com"""
        
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

        # Specify the text to read
        ttk.Label(main_frame, text="Text to Read:").grid(column=0, row=4, sticky=tk.W, pady=(10, 0))
        self.text_input = tk.Text(main_frame, height=10, width=50)
        self.text_input.grid(column=0, row=5, columnspan=2, pady=(0, 20))  # Padding added before submit button

        # Button configuration

        self.recording = False  # State to check if currently recording
        self.record_button = ttk.Button(main_frame, text="Record Mic", command=self.toggle_recording)
        self.record_button.grid(column=0, row=6, sticky=tk.W + tk.E, pady=(0, 20), padx=(0, 10))  # Left padding to separate buttons

        submit_button = ttk.Button(main_frame, text="Play Audio", style="Green.TButton", command=self.submit_text )
        submit_button.grid(column=1, row=6, sticky=tk.W + tk.E, pady=(0, 20), padx=(10, 0))  # Right padding to separate buttons







        #Credits
        info_label = tk.Label(main_frame, text="Created by Scorchsoft.com App Development", fg="blue", cursor="hand2")
        info_label.grid(column=0, row=7, columnspan=2, pady=(0, 0))
        info_label.bind("<Button-1>", lambda e: self.open_scorchsoft())





    
    
    def open_scorchsoft(self, event=None):
        webbrowser.open('https://www.scorchsoft.com')






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
        instruction_window = tk.Toplevel(self)
        instruction_window.title("Terms of Use")
        instruction_window.geometry("500x700")  # Width x Height

        instructions = """Disclaimer of Warranties
Text to Mic is provided "as is" and on an "as available" basis, without any warranties of any kind, either express or implied. Scorchsoft Ltd expressly disclaims all warranties, whether express, implied, statutory, or otherwise, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, and non-infringement. We do not warrant that the software will function uninterrupted, that it is error-free, or that any errors or defects will be corrected.

Limitation of Liability
In no event will Scorchsoft Ltd be liable for any indirect, incidental, special, consequential, or punitive damages resulting from or related to your use or inability to use Text to Mic, including but not limited to damages for loss of profits, goodwill, use, data, or other intangible losses, even if Scorchsoft Ltd has been advised of the possibility of such damages.

Use at Your Own Risk
By using Text to Mic, you acknowledge and agree that you assume full responsibility for your use of the software, and that any information you send or receive during your use of the software may not be secure and may be intercepted or later acquired by unauthorized parties. Use of Text to Mic is at your sole risk.

License Agreement
Users are granted a non-exclusive, revocable license to use Text to Mic solely for personal or commercial purposes. While the software remains the intellectual property of Scorchsoft Ltd., users are permitted to share the software with others under the condition that they attribute it to Scorchsoft Ltd. explicitly. This license does not grant users any ownership rights in the software and prohibits the creation of derivative works or the sale of the software. Users must ensure that Scorchsoft Ltd. is credited appropriately when sharing or demonstrating the software in any public or private setting.

Text to Mic was made by Scorchsoft.com. If you like this tool then please help us out and give us a backlink to help others find it at:
https://www.scorchsoft.com/blog/text-to-mic-for-meetings/
"""
        
        tk.Label(instruction_window, text=instructions, justify=tk.LEFT, wraplength=480).pack(padx=10, pady=10)
        
        # Add a button to close the window
        ttk.Button(instruction_window, text="Close", command=instruction_window.destroy).pack(pady=(10, 0))



    def get_app_support_path_mac(self):
        home = Path.home()
        app_support_path = home / 'Library' / 'Application Support' / 'scorchsoft-text-to-mic'
        app_support_path.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        return app_support_path
    
    def save_api_key_mac(self, api_key):
        env_path = self.get_app_support_path_mac() / '.env'
        with open(env_path, 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        # Consider manually loading this .env file into your environment as needed

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


    def save_api_key(self, api_key):
        try:
            if platform.system() == 'Darwin':
                self.save_api_key_mac(api_key)
            else:
                with open('.env', 'w') as f:
                    f.write(f"OPENAI_API_KEY={api_key}\n")
                load_dotenv()  # Reload environment to include the new API key
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API key: {str(e)}")


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


    def submit_text(self):

        text = self.text_input.get("1.0", tk.END).strip()
        selected_voice = self.voice_var.get()

        if not text:
            messagebox.showinfo("Error", "Please enter some text to synthesize.")
            return
        
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
                    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                    channels=wf.getnchannels(),
                                    rate=wf.getframerate(),
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


    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def stop_recording_btn_change(self, btn_text):
        self.record_button.config(text=btn_text)

    def start_recording(self):


        input_device_id = self.available_input_devices.get(self.input_device_index.get(), None)

        #Record to GUI selected device ID
        #device_id = None if self.input_device_index.get() == "Default" else input_devices[self.input_device_index.get()]

        if input_device_id is None:
            messagebox.showerror("Error", "Selected audio device is not available.")
            return
        
        try:
            self.recording = True
            self.record_button.config(text="Stop and Insert", style='Recording.TButton')
            self.frames = []

            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024, input_device_index=input_device_id)


            def record():
                while self.recording:
                    data = self.stream.read(1024, exception_on_overflow=False)
                    self.frames.append(data)

            self.record_thread = threading.Thread(target=record)
            self.record_thread.start()

        except Exception as e:
            messagebox.showerror("Recording Error", f"Failed to record audio: {str(e)}")
            self.stop_recording(True)

    def stop_recording(self, cancel_save=False):
        self.recording = False
        if self.record_thread:
            self.record_thread.join()

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        if self.p:
            self.p.terminate()

        if cancel_save==False:
            self.save_recording()
        
        self.record_button.config(text="Record Mic", style='TButton')  # Revert to default style


    def save_recording(self):
        file_path = "output.wav"
        wf = wave.open(file_path, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        print("Recording saved.")

        self.after(0, self.transcribe_audio, file_path)
    



    def transcribe_audio(self, file_path):
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
                self.apply_ai(transcription.text)
            else:
                print("outputting without ai")
                #This prevents issues with trying to upload TK after thread operations
                #whcih can cause crashes with no error displayed
                self.text_input.delete("1.0", tk.END)  # Clear existing text
                self.text_input.insert("1.0", transcription.text)  # Insert new text
            
            print("Transcription Complete: The audio has been transcribed and the text has been placed in the input area.")
            #messagebox.showinfo("Transcription Complete", "The audio has been transcribed and the text has been placed in the input area.")
        
        except Exception as e:
            print(f"Transcription error: An error occurred during transcription: {str(e)}")
    
    def load_settings(self):
        # Determine file path based on the operating system
        settings_file = self.get_settings_file_path("settings.json")
        
        try:
            with open(settings_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Default settings
            return {"chat_gpt_completion": False, "model": "gpt-3.5-turbo", "prompt": "", "auto_apply": False}

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

        # Model selection
        model_var = tk.StringVar(value=settings.get("model", "gpt-3.5-turbo"))
        ttk.Label(main_frame, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.OptionMenu(main_frame, model_var, "gpt-3.5-turbo", "gpt-3.5-turbo", "gpt-4-turbo").grid(row=1, column=1, sticky=tk.W, pady=2)

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


if __name__ == "__main__":
    app = Application()
    app.mainloop()