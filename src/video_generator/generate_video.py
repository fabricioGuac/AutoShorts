from src.crud import user_crud, prompt_crud
from src.video_generator import generate_script, generate_audio, generate_images, stitch_video
# from src.poster import social_media_poster


def generate_video(user_id: int) -> str:
    # Load user data and prompt config from DB
    user = user_crud.get_user(user_id)
    prompt_config = prompt_crud.get_prompt_config(user_id)

    # Generate the script
    script, title = generate_script.generate_script(prompt_config)

    # Generate audio using the narration from the script
    audio_path = generate_audio.generate_audio(script, user['voice_id'], title, prompt_config['id'])

    # Generate images for each scene in the script
    image_paths = generate_images.generate_images(script, title, prompt_config['id'])

    # Stitch the images and audio into the final video
    final_video_path = stitch_video.stitch_video(script,image_paths, audio_path, title, prompt_config['id'])

    # Post video to social media platforms (use the first narration from the script as the descriptionfor the post)
    # social_media_poster.post_video(user_id, final_video_path, script[0]['narration'] if script and 'narration' in script[0] else title, title)

    return final_video_path