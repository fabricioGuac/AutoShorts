import time, datetime
from src.video_generator.generate_video import generate_video
from src.crud import schedule_crud

def post_scheduled_content():
    now = datetime.datetime.now()
    current_day = now.strftime("%A")
    current_hour = now.hour

    users_due = schedule_crud.get_users_to_post_at(current_day, current_hour)

    for user_id in users_due:
        generate_video(user_id)