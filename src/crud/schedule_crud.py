from src.db import conn
import datetime
from typing import Optional

# Function to create a schedule entry
def create_schedule(user_id:int, schedule_day:str, schedule_hour:int) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO user_schedule (user_id, schedule_day, schedule_hour) 
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (user_id, schedule_day, schedule_hour)
        )
        schedule_id = cur.fetchone()[0]
        conn.commit()
        return schedule_id

# Function to remove a specific schedule
def remove_schedule(user_id: int, schedule_day: str, schedule_hour: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM user_schedule WHERE user_id = %s AND schedule_day = %s AND schedule_hour = %s",(user_id, schedule_day, schedule_hour))
        conn.commit()
        return cur.rowcount > 0

# Function to get all schedules for a specific user
def get_user_schedule(user_id:int) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
        """
        SELECT schedule_day, schedule_hour FROM
        user_schedule WHERE user_id = %s
        ORDER BY 
            CASE schedule_day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END,
            schedule_hour;
        """,
        (user_id,))
        return cur.fetchall()

# Function to fetch all users that have post schedules at the current time
def get_users_to_post_now() -> list[int]:
    # Gets the current weekday and the current hour (e.g, "Friday") and (0-23)
    now = datetime.datetime.now()
    current_day = now.strftime("%A")
    current_hour = now.hour

    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM user_schedule WHERE schedule_day = %s AND schedule_hour = %s", (current_day, current_hour))
        return [row[0] for row in cur.fetchall()]