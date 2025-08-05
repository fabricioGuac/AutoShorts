import os

# Util to generate the output dir for each video
def get_output_dir(prompt_config_id: int, title:str) -> str:
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    OUTPUT_ROOT = os.path.join(ROOT_DIR, "output")
    output_dir = os.path.join(
        OUTPUT_ROOT,
        f"prompt_{prompt_config_id}",
        title.lower().replace(" ", "_")
    )
    os.makedirs(output_dir, exist_ok=True)
    return output_dir