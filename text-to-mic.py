import openai
from openai import OpenAI
import pyaudio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set up your OpenAI API key from the environment variable
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def list_audio_devices():
    p = pyaudio.PyAudio()
    print("Available audio devices:")
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')
    # List all available devices, and mark output devices
    for i in range(0, num_devices):
        if p.get_device_info_by_index(i).get('maxOutputChannels') > 0:
            print(f"Device index {i}: {p.get_device_info_by_index(i).get('name')}")
    p.terminate()

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


    # Set up PyAudio
    p = pyaudio.PyAudio()
    if device_index is None:
        device_index = int(input("Enter the device index: "))
        
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=22050,  # Adjust the rate to match the audio format
                    output=True,
                    output_device_index=device_index)

        # Stream audio chunks to virtual microphone
    try:
        for chunk in response.iter_lines():
            stream.write(chunk)

        ##write to text file for testing
        with open("test_output.wav", "wb") as f:
            f.write(response.content)

    finally:
        # Ensure resources are cleaned up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
    """
    # Stream audio chunks to virtual microphone
    try:
        # Ensure you are handling the response's binary content correctly
        # Adjust the method to access binary data as per the latest library version or response object
        audio_data = response.content  # This might need adjustment based on actual response object methods
        stream.write(audio_data)

        ##write to text file for testing
        with open("test_output.wav", "wb") as f:
            f.write(response.content)

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
    """

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python script.py 'text to convert'")
        sys.exit(1)
    
    list_audio_devices()
    device_index = int(input("Enter the device index: "))
    stream_audio_to_virtual_mic(sys.argv[1], voice="fable", device_index=device_index)
