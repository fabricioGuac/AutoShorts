# import requests
# from requests.exceptions import RequestException
# from src.crud.tokens_crud import get_token_by_user_and_platform

# GRAPH_API_BASE = "https://graph.facebook.com/v23.0"


# def post_to_instagram(user_id:int, final_video_url:str, description:str) -> bool:
#     """
#     Posts a reel to Instagram using Meta Graph API.
#     NOTE: Requires:
#       - IG Business/Creator account linked to FB Page
#       - Access token with instagram_content_publish scope
#       - Video hosted on a publicly accessible URL (not a local file)
#     Disabled for MVP (Meta API complexity + hosting requirement).
#     """
#     # Query the tokens for instagram posting in the db and skip if not found
#     tokens = get_token_by_user_and_platform(user_id, "instagram")
#     if not tokens:
#         print(f"[WARNING] No Instagram credentials found for user {user_id}. Skipping post.")
#         return False
    
#     # Needed posting tokens
#     ig_user_id = tokens['user_id']
#     access_token = tokens['access_token']

#     # Upload video container
#     upload_url = f"{GRAPH_API_BASE}/{ig_user_id}/media"
#     try:
#         response = requests.post(
#             upload_url,
#             data = {
#                 "media_type": "REELS",
#                 "caption": description,
#                 "video_url": final_video_url,  # must be a public URL
#                 "access_token": access_token
#             },
#         )
#         response.raise_for_status()
#     except (RequestException, IOError) as e:
#         print(f"[ERROR] Failed during container creation: {e}")
#         return False

#     # Fetch the creation id from the response
#     creation_id = response.json().get("id")
#     # If not present there was an error
#     if not creation_id:
#         print(f"[ERROR] No creation_id returned: {response.text}")
#         return False

#     # Publish the container
#     publish_url = f"{GRAPH_API_BASE}/{ig_user_id}/media_publish"
#     try:
#         publish_response = requests.post(
#             publish_url,
#             data={"creation_id": creation_id, "access_token":access_token}
#         )
#         publish_response.raise_for_status()
#     except RequestException as e:
#         print(f"[ERROR] Failed to publish video: {e}")
#         return False
    
#     print(f"[SUCCESS] Posted reel for user {user_id}. Response {publish_response.json()}")
#     return True
