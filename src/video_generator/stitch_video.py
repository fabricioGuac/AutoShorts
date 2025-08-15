from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from src.utils.paths import get_output_dir
import os

def stitch_video(script: list[str], image_paths: list[str], audio_path: str, title: str, prompt_config_id: int) -> str:
    
    audio_clip = AudioFileClip(audio_path)

    # Convert image paths to image clips
    image_clips = []
    for i, image_path in enumerate(image_paths):
        duration = script[i].get("duration", 5)
        clip = ImageClip(image_path).with_duration(duration)
        clip = clip.resized(height=1080)
        # Ensure width and height are divisible by 2 (needed for some encoders. AI-generated images usually don't need this)
        clip = clip.resized(lambda t: (clip.w // 2 * 2, clip.h // 2 * 2))
        clip = clip.with_position("center")
        image_clips.append(clip)

    # Stitch and export
    video = concatenate_videoclips(image_clips, method="compose").with_audio(audio_clip)
    
    output_dir = get_output_dir(prompt_config_id, title)

    final_video_path = os.path.join(output_dir, "final_video.mp4")
    video.write_videofile(final_video_path, fps=24, codec="libx264", audio_codec="aac")

    print(f"✅ Final video saved to {final_video_path}")
    return final_video_path