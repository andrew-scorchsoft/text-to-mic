import openai
from openai import OpenAI
import pyaudio
import wave
import threading
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


def play_saved_audio(file_path, device_index=None):
    # Open the saved audio file
    wf = wave.open(file_path, 'rb')

    print(f"Playing audio to device {device_index}")

    # Setup PyAudio
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
    except Exception as e:
        print(f"Error playing audio on device {device_index}: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()

#Plays to multiple device indexes at the same time
def play_audio_multiplexed(file_paths, device_indices):
    p = pyaudio.PyAudio()
    streams = []
    
    # Open all files and start all streams
    for file_path, device_index in zip(file_paths, device_indices):
        wf = wave.open(file_path, 'rb')
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        output_device_index=device_index)
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
                active_streams -= 1
    
    p.terminate()
    
def stream_audio_to_virtual_mic(text, voice="fable", device_index=None, device_index_2=None):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format='wav'
    )

    #This can either stream to one device index at a time, or, via multiplexing
    #it can stream to two similtaneously to prevent lag playing in sequence
    if device_index_2 is not None:
        file_path_1 = "output1.wav"
        file_path_2 = "output2.wav"
        response.stream_to_file(file_path_1)
        response.stream_to_file(file_path_2)
        play_audio_multiplexed([file_path_1, file_path_2], [device_index, device_index_2])
    else:
        file_path_1 = "output1.wav"
        response.stream_to_file(file_path_1)
        play_saved_audio(file_path_1, device_index)

    return "";

 

if __name__ == "__main__":
    import sys

    arglen = len(sys.argv)

    if arglen < 2:
        print("Usage: python script.py 'text to convert'")
        sys.exit(1)
    
    print(f"arg count {arglen}")

    if arglen == 4:
        device_index = int(sys.argv[2])
        device_index_2 = int(sys.argv[3])
    elif arglen == 3:
        device_index = int(sys.argv[2])
        device_index_2 = None
    else:
        list_audio_devices()
        device_index = int(input("Enter the device index: "))
        device_index_2 = None

    
    stream_audio_to_virtual_mic(sys.argv[1], voice="fable", device_index=device_index,device_index_2=device_index_2)
