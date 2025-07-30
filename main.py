from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import save
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
from io import BytesIO
import google.generativeai as genai
import requests
import os
import re
import json

# Env set up
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")


# Helper function to format the gemini response as JSON
def extract_json_from_gemini(text: str):
    # Try to match markdown-style JSON
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    
    if match:
        json_str = match.group(1).strip()
    else:
        # If no triple backticks, assume entire response might be JSON
        json_str = text.strip()

    # Try parsing
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse Gemini response as JSON:")
        print(json_str)
        raise e


# ID of the voice that will be used
VOICE_ID = "y2Y5MeVPm6ZQXK64WUui" # Hardcoded for the time being

# Google gemini set up
genai.configure(api_key=GOOGLE_API_KEY)
text_model = genai.GenerativeModel('gemini-2.5-flash')

print("Starting program")

# Placeholder prompt 
prompt = (
    "Write a structured JSON array educational video about the history and evolution of scalpels, lasting no more than 60 seconds total. "
    "Use 5–6 scenes. The total word count across all 'narration' fields must not exceed 130 words. "
    "The text will be read aloud using a voice model that speaks at approximately 1 word per 0.48 seconds (about 125 words per minute). "
    "Base the estimated 'duration' of each scene on how long its narration would take to read aloud at this pace. "
    "Each item must include:\n"
    "- scene_id: a short label (e.g., intro, origins, modern)\n"
    "- narration: 1–2 sentences that sound natural when spoken aloud\n"
    "- image_prompt: a visual prompt for AI image generation\n"
    "- duration: estimated seconds based on narration length\n\n"
    "Format it as a valid JSON array."
)

# Prompts the model to generate the scene by scene JSON script for the short
response = text_model.generate_content(prompt)

# Short's name and directories
short_name = "scalpel" # Placeholder until we make it dynamic from the response
short_dir = os.path.join("output", short_name)
image_dir = os.path.join(short_dir,"images")

os.makedirs(image_dir, exist_ok=True)


# Retrieves the script  and image prompts from the response
scenes = extract_json_from_gemini(response.text)

with open(os.path.join(short_dir, "script.json"), "w") as f:
    json.dump(scenes, f, indent=2)

print("Script: \n", scenes)

# Combines the narration
narration = " ".join([scene["narration"] for scene in scenes])

print("Speech: \n", narration)


# Eleven labs set up
elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Generates the audio
audio = elevenlabs.text_to_speech.convert(
    text=narration,
    voice_id=VOICE_ID,
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)

# Saves the audio
audio_path = os.path.join(short_dir, "narration.mp3")
save(audio, audio_path)
print(f"✅ Audio saved to {audio_path}")

# Generates the images

image_paths = [] # Stores the paths to the generated image files

for i, scene in enumerate(scenes):
    print(f"  Scene {i+1}: {scene['scene_id']}")
    
    response = requests.post(
        "https://api.stability.ai/v2beta/stable-image/generate/core",
        headers={
            "authorization": f"Bearer {STABILITY_API_KEY}",
            "accept": "image/*"
        },
        files={"none": ''},
        data={
            "prompt": scene["image_prompt"],
            "output_format": "jpeg",
        },
    )

    if response.status_code == 200:
        image_path = os.path.join(image_dir, f"scene_{i+1}+{scene['scene_id']}.jpg")
        with open(image_path, 'wb') as f:
            f.write(response.content)
        image_paths.append(image_path)
    else:
        raise Exception(str(response.json()))

print("Images generated")

# Video stitching

audio_clip = AudioFileClip(audio_path)

# Convert image paths to image clips
image_clips = []
for i, image_path in enumerate(image_paths):
    duration = scenes[i].get("duration", 5)
    clip = ImageClip(image_path).with_duration(duration).resized(height=1080).with_position("center")
    image_clips.append(clip)

# Stitch and export
video = concatenate_videoclips(image_clips, method="compose").with_audio(audio_clip)
final_video_path = os.path.join(short_dir, "final_video.mp4")
video.write_videofile(final_video_path, fps=24, codec="libx264", audio_codec="aac")

print(f"✅ Final video saved to {final_video_path}")