import requests
import json
from src.crud.tokens_crud import get_token_by_user_and_platform

def get_access_token(client_id:str, client_secret:str, refresh_token:int) -> str:    
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        },
    )   
    # Google returns invalid_grant if token expired or revoked 
    if response.status_code == 400:
        raise Exception("Refresh token expired :( Add a new one.")
    response.raise_for_status()
    token_data = response.json()
    return token_data["access_token"]

def post_to_youtube(user_id:int, final_video_path:str, description:str, title:str) -> bool:
    # Query the tokens for youtube posting in the db and skip if not found
    tokens = get_token_by_user_and_platform(user_id, "youtube")
    if not tokens:
        print(f"No Youtube credentials found for user {user_id}. Skipping post.")
        return False

    client_id = tokens['client_id']
    client_secret = tokens['client_secret']
    refresh_token = tokens['refresh_token']

    try:
        access_token = get_access_token(client_id,client_secret,refresh_token)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept":"application/json"
        }

        metadata ={ 
            "snippet": {
                "title": title,
                "description": description,
                "tags":[title, "shorts"],
                "categoryId":"22"
            },
            "status":{
                "privacyStatus":"public"
            }
        }

        # Initiates a resumable upload session
        initiate_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        init_resp = requests.post(initiate_url, headers=headers, json=metadata)
        init_resp.raise_for_status()

        upload_url = init_resp.headers["Location"]

        # Upload the video bytes
        final_video_data = None
        with open(final_video_path, "rb") as f:
            final_video_data = f.read()

        upload_headers = {
            "Authorization":f"Bearer {access_token}",
            "Content-Length":str(len(final_video_data)),
            "Content-Type":"video/*"
        }   

        upload_resp = requests.put(upload_url, headers=upload_headers, data = final_video_data)
        upload_resp.raise_for_status()
        video_result = upload_resp.json()

        video_id = video_result.get("id")
        print(f"[SUCCESS] Video posted! Watch: https://www.youtube.com/watch?v={video_id}")
        print(f"[INFO] Short URL: https://www.youtube.com/shorts/{video_id}")
    except Exception as e:
        print(f"[ERROR] Could not post video to youtube. Error: {e}")
        return False