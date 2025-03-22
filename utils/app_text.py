class AppText:
    """
    Class for storing long text strings used throughout the application.
    This helps keep the main codebase cleaner by separating UI text content.
    """
    
    # Instructions text displayed in the "How to Use" modal
    INSTRUCTIONS = """How to Use Scorchsoft Text to Mic:

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

    # Default license text as a fallback when the LICENSE.md file cannot be found
    DEFAULT_LICENSE = """
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