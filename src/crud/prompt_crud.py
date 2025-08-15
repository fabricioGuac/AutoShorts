from src.db import conn
from psycopg2.extras import RealDictCursor
from typing import Optional, Literal

# Function to cerate a new prompt config
def create_prompt_config(user_id:int, topic:str, scope:str, wpm:int) -> int:
    # Creates a new cursor and uses context manager to close it once the block finishes
    with conn.cursor() as cur:
        # Executes the custom sql command
        cur.execute(
            "INSERT INTO prompt_config (user_id, topic, scope,  wpm) VALUES (%s, %s,%s, %s) RETURNING id;",
            (user_id, topic, scope, wpm)
        )
        # fetchone() returns the first row of the result set as a tuple
        # Since RETURNING id returns only one column, we use [0] to extract just the id value
        prompt_config_id = cur.fetchone()[0]
        # finalize a transaction and make the changes permanent in the database
        conn.commit()
        return prompt_config_id

# Function to retrieve the prompt config by it's user id
def get_prompt_config(user_id: int) -> Optional[dict]:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM prompt_config WHERE user_id = %s;", (user_id,))
        # Returns a directory or None if not found 
        return cur.fetchone()

# Function to update a user mutable field (topic, scope, wpm) in prompt_config
def update_prompt_config_field(
    user_id:int,
    field:Literal["topic", "scope", "wpm"], # Literal to restrict the field's param
    new_value: str | int
) -> None:
    if field not in ["topic", "scope", "wpm"]:
        raise ValueError("Invalid field. Only 'topic', 'scope', or 'wpm' are allowed")
    
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE prompt_config SET {field} = %s WHERE user_id = %s", 
            (new_value, user_id)
        )
        conn.commit()

# Function to append a topic to covered_topics if not already present
def append_covered_topic_if_missing(prompt_config_id: int, new_title: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT covered_topics FROM prompt_config WHERE id = %s;",
            (prompt_config_id,)
        )
        covered_topics = cur.fetchone()
        
        if covered_topics is None:
            raise ValueError(f"No prompt config found with id {prompt_config_id}")
        
        covered_topics = covered_topics[0]

        if new_title not in covered_topics:
            cur.execute(
                "UPDATE prompt_config SET covered_topics = array_append(covered_topics, %s) WHERE id = %s;",
                (new_title, prompt_config_id)
            )
            conn.commit()