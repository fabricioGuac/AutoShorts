from elevenlabs.client import ElevenLabs
from elevenlabs import save

# Eleven labs set up
elevenlabs = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])


def generate_audio(script: list[dict], voice_id:str, title: str, prompt_config_id:int) -> str:
    # Combines the narration from all scenes
    narration = " ".join([scene["narration"] for scene in script])

    # Generates the audio
    audio = elevenlabs.text_to_speech.convert(
    text=narration,
    voice_id=voice_id,
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
    )

    # Recreates output directory path
    output_dir = get_output_dir(prompt_config_id, title)

    # Saves the audio
    audio_path = os.path.join(output_dir, "narration.mp3")
    save(audio, audio_path)
    print(f"✅ Audio saved to {audio_path}")

    return audio_path