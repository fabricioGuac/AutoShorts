from src.db import conn
from psycopg2.extras import RealDictCursor
from typing import Optional
from src.utils.encryption import encrypt, decrypt

# Function to create a new token
def create_token(
    user_id: int,
    platform:str,
    refresh_token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    cookies: Optional[str] = None
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO social_tokens (
                user_id, platform, refresh_token, client_id, client_secret, cookies
            ) VALUES (%s,%s,%s,%s,%s,%s)
            RETURNING id;
            """,
            (
                user_id,
                platform,
                encrypt(refresh_token) if refresh_token else None,
                encrypt(client_id) if client_id else None,
                encrypt(client_secret) if client_secret else None,
                encrypt(cookies) if cookies else None
            )
        )
        token_id = cur.fetchone()[0]
        conn.commit()
        return token_id

# Function to fetch a token for an user and platform
def get_token_by_user_and_platform(user_id: int, platform:str) -> Optional[dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM social_tokens WHERE user_id = %s AND platform = %s", (user_id, platform))
        token =  cur.fetchone()

        if not token:
            return None
        
        # Decrypt the sensitive fields if they exist
        for field in ["refresh_token", "client_id", "client_secret", "cookies"]:
            if token.get(field):
                token[field] = decrypt(token[field])
        return token

# Function to update token information
def update_token(
    user_id: int,
    platform:str,
    refresh_token: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    cookies: Optional[str] = None
) -> bool:
    # Prepare a dict of fields, encrypting values if present
    fields = {
        "refresh_token": encrypt(refresh_token) if refresh_token else None,
        "client_id": encrypt(client_id) if client_id else None,
        "client_secret": encrypt(client_secret) if client_secret else None,
        "cookies": encrypt(cookies) if cookies else None
    }

    # Keep only the fields that have a new value
    update_fields = {k: v for k, v in fields.items() if v is not None}
    # If no fields to update, return False
    if not update_fields:
        return False
    # Build SET clause dynamically
    set_clause = ", ".join(f"{k} = %s" for k in update_fields.keys())
    # Combine values for placeholders in the query
    values = list(update_fields.values()) + [user_id, platform]

    query = f"UPDATE social_tokens SET {set_clause} WHERE user_id = %s AND platform = %s;"
    with conn.cursor() as cur:
        cur.execute(query, values)
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