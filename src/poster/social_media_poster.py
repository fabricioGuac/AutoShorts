from src.poster.tiktok_poster import post_to_tiktok
from src.poster.youtube_poster import post_to_youtube


# Post video to social media platforms
def post_video(user_id: int, final_video_path: str, description: str, title: str):
    post_to_youtube(user_id, final_video_path, description, title)
    post_to_tiktok(user_id, final_video_path, description)
    # Consider adding the instagram logic
