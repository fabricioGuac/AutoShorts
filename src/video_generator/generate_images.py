import requests
import os
from src.utils.paths import get_output_dir

def generate_images(script: list[dict], title: str, prompt_config_id: int) -> list[str]:
    image_paths = []  # Stores the paths to the generated image files

    # Create the directory for the images
    output_dir = get_output_dir(prompt_config_id, f"{title}/images")

    for i, scene in enumerate(script):
        print(f"Generating image for Scene {i + 1}: {scene['scene_id']}")
        
        # Request to the stability API
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/core",
            headers={
                "authorization": f"Bearer {os.environ['STABILITY_API_KEY']}",
                "accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": scene["image_prompt"],
                "output_format": "jpeg",
            },
        )

        if response.status_code == 200:
            image_path = os.path.join(output_dir, f"scene_{i + 1}_{scene['scene_id']}.jpg")
            with open(image_path, 'wb') as f:
                f.write(response.content)
            image_paths.append(image_path)
        else:
            raise Exception(f"❌ Image generation failed: {response.status_code}\n{response.json()}")

    print("✅ All images generated.")
    return image_paths
    # return [
    # r"output\placeholder_imgs\hohftp1.jpg",
    # r"output\placeholder_imgs\mamama1.jpg",
    # r"output\placeholder_imgs\minerva3.jpg",
    # r"output\placeholder_imgs\miverva2.jpg",
    # r"output\placeholder_imgs\pannello.jpg"
    # ]

