from src.db import conn
from psycopg2.extras import RealDictCursor
from typing import Optional

# Function to cerate a new user
def create_user(username:str, voice_id: str) -> int:
    # Creates a new cursor and uses context manager to close it once the block finishes
    with conn.cursor() as cur:
        # Executes the custom sql command
        cur.execute(
            "INSERT INTO users (username, voice_id) VALUES (%s, %s) RETURNING id;",
            (username, voice_id)
        )
        # fetchone() returns the first row of the result set as a tuple
        # Since RETURNING id returns only one column, we use [0] to extract just the id value
        user_id = cur.fetchone()[0]
        # finalize a transaction and make the changes permanent in the database
        conn.commit()
        return user_id

# Function to retrieve all users
def get_all_users() -> list[dict]:
    with conn.cursor(cursor_factory=RealDictCursor)as cur:
        cur.execute("SELECT * FROM users")
        return cur.fetchall()

# Function to retrieve an user by it's id
def get_user(user_id: int) -> Optional[dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
        # Returns a dictionary or None if not found 
        return cur.fetchone()

# Function to update the user's voice id
def update_voice_id(user_id: int, new_voice_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET voice_id = %s WHERE id = %s",
            (new_voice_id, user_id)
        )
        conn.commit()
        return cur.rowcount > 0 #True if a row was affected

# Function to delete an user
def delete_user(user_id: int) -> bool:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        return cur.rowcount > 0
