import json
import re
import os
from typing import Tuple
from src.db import get_db_connection
import google.generativeai as genai
from src.crud import prompt_crud
from src.utils.paths import get_output_dir

# Google gemini set up
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
text_model = genai.GenerativeModel('gemini-2.5-flash')

# Helper function to format the gemini response as JSON
def extract_json_from_gemini(text: str):
    # Try to match markdown-style JSON
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    
    if match:
        json_str = match.group(1).strip()
    else:
        # If no triple backticks, assume entire response might be JSON
        json_str = text.strip()

    # Try parsing
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse Gemini response as JSON:")
        print(json_str)
        raise e

# Helper function to generate the prompt
def build_prompt(topic: str,scope: str,covered_topics: list[str],wpm:int) -> str:
    words_per_sec = round(60 / wpm, 2)
    topics_str = ', '.join(covered_topics) if covered_topics else "none"
    
    return (
        f"Write a structured JSON array educational video about the  the {scope} of a {topic} "
        f"that has not been covered already in: {topics_str}. "
        "The video must last no more than 60 seconds total. "
        "Use 5–6 scenes. The total word count across all 'narration' fields must not exceed "
        f"{int(wpm)} words. "
        f"The text will be read aloud using a voice model that speaks at approximately 1 word per {words_per_sec} seconds. "
        "Base the estimated 'duration' of each scene on how long its narration would take to read aloud at this pace. "
        "Each item must include:\n"
        "- scene_id: a short label \n"
        "- narration: 1–2 sentences that sound natural when spoken aloud\n"
        "- image_prompt: a visual prompt for AI image generation\n"
        "- duration: estimated seconds based on narration length\n\n"
        "Return a JSON object with two keys:\n"
        "- 'title': a **very short** identifier for the subtopic (e.g., 'scalpel', 'falafel', or 'espresso'), ideally 1–2 words\n"
        "- 'scenes': an array of the scenes described above"
    )


def generate_script(prompt_config) -> tuple[list[dict], str]:
    db = get_db_connection()

    prompt = build_prompt(
        topic=prompt_config.topic,
        scope=prompt_config.scope,
        covered_topics=prompt_config.covered_topics,
        wpm=prompt_config.wpm
    )

    # Generate script from Gemini
    response = text_model.generate_content(prompt)
    response_data = extract_json_from_gemini(response.text)

    # Updates the covered topics
    new_title = response_data["title"]
    prompt_crud.append_covered_topic_if_missing(db, prompt_config.id, new_title)

    # Writes the script to the output folder for the current topic
    output_dir = get_output_dir(prompt_config.id, new_title)

    script_path = os.path.join(output_dir, "script.json")
    with open(script_path, "w") as f:
        json.dump(response_data["scenes"],f,indent=2)

    return response_data["scenes"], new_title