import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Menu
import os
import pyaudio
import wave
import webbrowser
from openai import OpenAI
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

version_number = "1.0.0"

class Application(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Scorchsoft Text to Mic")
        self.style = ttk.Style(self)
        self.style.theme_use('clam')  # Using a theme for a better look
        
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

        self.create_menu()
        self.initialize_gui()

    def create_menu(self):
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        # File or settings menu
        settings_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Change API Key", command=self.change_api_key)

        # Playback menu
        playback_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Playback", menu=playback_menu)
        playback_menu.add_command(label="Play Last Audio", command=self.play_last_audio)

    def initialize_gui(self):
        self.device_index = tk.StringVar(self)
        self.device_index_2 = tk.StringVar(self)
        self.device_index.set("Select Device")
        self.device_index_2.set("None")

        # Fetching available devices
        available_devices = self.get_audio_devices()
        device_names = list(available_devices.keys())


        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        #ttk.Label(main_frame, text="Scorchsoft Text to Mic").grid(column=0, row=0, columnspan=2, pady=(0, 10))  # Increased padding after the title
        #ttk.Label(main_frame, text="This tool uses OpenAI's text-to-speech to stream audio.").grid(column=0, row=1, columnspan=2, pady=(0, 10))


        # Voice Selection
        self.voice_var = tk.StringVar()
        voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        ttk.Label(main_frame, text="Choose a Voice").grid(column=0, row=0, sticky=tk.W, pady=(10, 10))  # Padding added
        voice_menu = ttk.OptionMenu(main_frame, self.voice_var,'fable', *voices)
        voice_menu.grid(column=1, row=0, sticky=tk.W)

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

        submit_button = ttk.Button(main_frame, text="Play Audio", command=self.submit_text)
        submit_button.grid(column=0, row=6, columnspan=2, pady=(0, 20))

        #Credits
        info_label = tk.Label(main_frame, text="This tool was created by Scorchsoft.com app development", fg="blue", cursor="hand2")
        info_label.grid(column=0, row=7, columnspan=2, pady=(0, 10))
        info_label.bind("<Button-1>", lambda e: self.open_scorchsoft())

        #Software version
        version_label = tk.Label(main_frame, text=f"Version: {version_number}")
        version_label.grid(column=0, row=8, columnspan=2, pady=(0, 10))

    def open_scorchsoft(self, event=None):
        webbrowser.open('https://www.scorchsoft.com')


    def get_api_key(self):
        api_key = os.getenv("OPENAI_API_KEY")
        

        if not api_key:  # Only ask if .env has no API key
            api_key = simpledialog.askstring("API Key", "Enter your OpenAI API Key:")

        if api_key:
                print(f"\nAPI Key: {api_key }\n")
                self.save_api_key(api_key)
        
        return api_key

    def save_api_key(self, api_key):
        with open('.env', 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
        load_dotenv()

    def get_audio_devices(self):
        p = pyaudio.PyAudio()
        devices = {}
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:  # Filter for output-capable devices
                devices[info['name']] = i
        p.terminate()
        return devices

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
            self.last_audio_file = "last_output.wav"
            response.stream_to_file(self.last_audio_file)

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
                wf = wave.open(file_path, 'rb')
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True,
                                output_device_index=int(device_index))
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


if __name__ == "__main__":
    app = Application()
    app.mainloop()