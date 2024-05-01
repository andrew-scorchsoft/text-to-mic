import openai
from openai import OpenAI
import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up your OpenAI API key from the environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def list_audio_devices():
    print("Available audio devices:")
    devices = sd.query_devices()
    for index, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            print(f"Device index {index}: {device['name']}")

def stream_audio_to_virtual_mic(text, voice="fable", device_index=None):

    # Check if device_index is provided, if not, prompt for it
    if device_index is None:
        device_index = int(input("Enter the device index: "))

    # Create audio stream from text input

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )


    if device_index is None:
        device_index = int(input("Enter the device index: "))
        
    # Load the binary audio content into a numpy array
    audio_data = np.frombuffer(response.content, dtype=np.int16)

    # Set the samplerate assumed from OpenAI's API (check documentation for exact rate)
    sample_rate = 22050  # or 44100, depending on the API's output format

    # Play audio
    sd.play(audio_data, sample_rate, device=device_index)
    sd.wait()  # Wait until the audio has finished playing

    sf.write('captured_audio.wav', audio_data, sample_rate)
        


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py 'text to convert'")
        sys.exit(1)
    
    list_audio_devices()
    device_index = int(input("Enter the device index: "))
    stream_audio_to_virtual_mic(sys.argv[1], voice="fable", device_index=device_index)
