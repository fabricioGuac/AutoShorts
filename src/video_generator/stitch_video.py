from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx import Crop
from src.utils.paths import get_output_dir
import os

def stitch_video(script: list[dict], image_paths: list[str], audio_path: str, title: str, prompt_config_id: int) -> str:
    audio_clip = AudioFileClip(audio_path)
    image_clips = []

    # Target size for Shorts (9:16)
    target_width, target_height = 1080, 1920

    # Convert image paths to image clips
    for i, image_path in enumerate(image_paths):
        duration = script[i].get("duration", 5)
        clip = ImageClip(image_path, duration=duration)

        # Resize height to target (1920 for Shorts)
        clip = clip.resized(height=target_height)

        # Ensure width divisible by 2
        clip_width = clip.w - (clip.w % 2)

        # Target width for Shorts (1080)
        final_width = target_width - (target_width % 2)

        # Crop or pad to fit target width
        if clip_width > final_width:
            # Crop center
            cropper = Crop(width=final_width, x_center=clip.w / 2)
            clip = cropper.apply(clip)
        elif clip_width < final_width:
            # Pad with black bars
            pad_left = (final_width - clip.w) // 2
            pad_right = final_width - clip.w - pad_left
            clip = clip.margin(left=pad_left, right=pad_right, color=(0,0,0))

        # Final safety: ensure height divisible by 2
        final_height = target_height - (target_height % 2)
        clip = clip.resized(height=final_height).with_position("center")
        image_clips.append(clip)


    # Stitch and export
    video = concatenate_videoclips(image_clips, method="compose").with_audio(audio_clip)
    output_dir = get_output_dir(prompt_config_id, title)
    final_video_path = os.path.join(output_dir, "final_video.mp4")
    video.write_videofile(final_video_path, fps=24, codec="libx264", audio_codec="aac")

    print(f"✅ Final video saved to {final_video_path}")
    return final_video_path