from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import google.generativeai as genai
import os

# Loads enviroment variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Google gemini set up
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

print("Starting program")

# Placeholder prompt 
prompt = (
    "Write a fun and informative monologue script for a 1-minute video "
    "about the history and evolution of pancakes. The tone should be energetic and friendly. "
    "Make it suitable for text-to-speech — just plain spoken narration, no scene directions or formatting. "
    "Ensure it runs at least 40 seconds but no longer than 60 seconds when read aloud."
)

# Prompts the model
response = model.generate_content(prompt)
# Retrieves the script from the response
script = response.text.strip()

print("Generated script: \n", script)

# Eleven labs set up
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
# ID of the voice that will be used
VOICE_ID = "y2Y5MeVPm6ZQXK64WUui"

# Generates the audio
audio = elevenlabs.text_to_speech.convert(
    text=script,
    voice_id=VOICE_ID,
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)

# Make sure the output folder exists
os.makedirs("output/audio", exist_ok=True)

# Open the file in binary write mode
with open("output/audio/pancakes.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("✅ Audio saved to output/audio/pancakes.mp3")