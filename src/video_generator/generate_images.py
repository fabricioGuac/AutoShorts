import requests
import os
from PIL import Image
from src.utils.paths import get_output_dir

# Boolean to decide  if a local image generator will be used instead of stability
USE_LOCAL_IMG_MODEL = os.environ.get("STABILITY_API_KEY") is None

# If the local model will be use installs it
if USE_LOCAL_IMG_MODEL:
    import torch
    from diffusers import StableDiffusionPipeline

    # Load the model into a project local folder 
    # (Note: it will not install every run but only if it is not there or only corrupted sections)
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        cache_dir="models/", # Set a local folder instaed of ~/.cache default
        torch_dtype=torch.float16
    )
    # Use GPU if available, otherwise fallback to CPU
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")



def generate_images(script: list[dict], title: str, prompt_config_id: int) -> list[str]:
    image_paths = []  # Stores the paths to the generated image files

    # Create the directory for the images
    output_dir = get_output_dir(prompt_config_id, f"{title}/images")
    print(f"🧠 Using {'local model' if USE_LOCAL_IMG_MODEL else 'Stability API'} for image generation.")

    for i, scene in enumerate(script):
        print(f"Generating image for Scene {i + 1}: {scene['scene_id']}")
        
        # Check if the local model is being used
        if USE_LOCAL_IMG_MODEL:
            # Local generation (GPU friendly size while keeping 9:16 ratio for later resize)
            image = pipe(scene["image_prompt"], height=1136, width=640).images[0]
            image = image.resize((1080, 1920), resample=Image.LANCZOS)

            # Convert to YCbCr (baseline JPEG color space)
            image = image.convert("YCbCr")

            
            # Save clean JPEG (baseline, no subsampling, no metadata)
            image_path = os.path.join(output_dir, f"scene_{i + 1}_{scene['scene_id']}.jpg")
            image.save(
                image_path, 
                format="JPEG",
                quality=90, # quality=90 balance image quality along with image size
                subsampling=0, # full-resolution chroma (avoids ffmpeg subsampling bugs)
                optimize=True, # smaller but still baseline
                progressive=False  # disable progressive encoding
                )
            image_paths.append(image_path)
        else:
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
                    # to ensure 9:16 aspect ratio
                    "width": 1080,
                    "height": 1920
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

