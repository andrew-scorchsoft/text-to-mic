# Readme

This script uses OpenAI to convert text to speech, and then speak that speech over a virtual microphone.

## 1) Install VB-Cable:
https://vb-audio.com/Cable/

## 2) ensure the OpenAI API key is specified in the .env file
This sets up a virtual microphone that we can use to sent text to speech audio to. Then, when you join a meeting, such as a google meeting, you can select this virtual cable to hear the audio being sent on the channel.

## 3) Run the script:
python text-to-mic.py "Text you'd like to speak"

This will then ask you which device you want to send the audio to, and give you a list to choose from. 

Take note of them listed, and record the device ID of your headphones, and of the "Cable Input". For now get it to output to your headphones as a test that it works.

Now that you know your headphone device id, and the cable input id, you can now automatically select both with your command prompt input like this, where 8 and 5 are the respective device indexes:
python text-to-mic.py "Text you'd like to speak" 8 5






# Dependencies

To get this script working you will need to install the following on the relevant operating system

### Windows
pip install tk
pip install pyaudio
pip install python-dotenv
pip install wave
pip install pydub


### Mac

brew install portaudio
pip install python-dotenv
pip install wave
pip install pydub



