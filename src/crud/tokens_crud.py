from src.db import conn
from typing import Optional

# Function to create a new token
def create_token(
    user_id: int,
    platform:str,
    access_token:Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_expiry: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO social_tokens (
                user_id, platform, access_token, refresh_token, token_expiry, username, password
            ) VALUES (%s,%s,%s,%s,%s,%s,%s)
            RETURNING id;
            """,
            (user_id, platform, access_token, refresh_token, token_expiry, username, password)
        )
        token_id = cur.fetchone()[0]
        conn.commit()
        return token_id

# Function to fetch a token for an user and platform
def get_token_by_user_and_platform(user_id: int, platform:str) -> Optional[tuple]:
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM social_tokens WHERE user_id = %s AND platform = %s", (user_id, platform))
        return cur.fetchone()

# Function to update token information
def update_token(
    user_id: int,
    platform:str,
    access_token:Optional[str] = None,
    refresh_token: Optional[str] = None,
    token_expiry: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE social_tokens
            SET access_token = %s,
                refresh_token = %s,
                token_expiry = %s,
                username = %s,
                password = %s
            WHERE user_id = %s AND platform = %s;
            """,
            (access_token, refresh_token, token_expiry, username, password, user_id, platform)
        )
        conn.commit()
        return cur.rowcount > 0

# Function to delete a social media token
def delete_token(user_id: int, platform: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM social_tokens WHERE user_id = %s AND platform = %s;",
            (user_id, platform)
        )
        conn.commit()
        return cur.rowcount > 0