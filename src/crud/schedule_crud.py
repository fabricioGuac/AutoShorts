from src.db import conn
import psycopg2.errors
import datetime
from typing import Optional

# Function to create a schedule entry
def create_schedule(user_id:int, schedule_day:str, schedule_hour:int) -> int:
    try:
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
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        print(f"User already has a schedule for {schedule_day} at {schedule_hour:02d}:00")
        return None

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
def get_users_to_post_at(schedule_day: str, schedule_hour: int) -> list[int]:

    with conn.cursor() as cur:
        cur.execute("SELECT user_id FROM user_schedule WHERE schedule_day = %s AND schedule_hour = %s", (schedule_day, schedule_hour))
        return [row[0] for row in cur.fetchall()]