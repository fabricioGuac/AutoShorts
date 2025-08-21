from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from src.crud import (
    user_crud,
    prompt_crud,
    tokens_crud,
    schedule_crud,
)
from src.video_generator import generate_video
from src.scheduler import scheduler_manager

# Main menu and entry point for the cli logic
def cli_main():
    while True:
        action = inquirer.select(
            message="AutoShorts Main Menu",
            choices=[
                "Create new user",
                "View / edit existing user",
                "Exit",
            ],
        ).execute()

        if action == "Create new user":
            create_user_flow()
        elif action == "View / edit existing user":
            user = pick_user()
            if user:
                user_menu_flow(user)
        else:
            print("Exiting Autoshort's CLI...")
            break

# Cli logic for user creation
def create_user_flow() -> None:
    username = inquirer.text(message="Enter a username:").execute()
    voice_id = inquirer.text(message="Enter ElevenLabs voice_id:").execute()

    user_id = user_crud.create_user(username, voice_id)
    print(f"Created user {username} (id={user_id} && voice={voice_id})")

    topic = inquirer.text(message="What's the topic?").execute()
    scope = inquirer.text(message="What's the scope/style?").execute()
    wpm = inquirer.text(
        message="What's the voice_id reading speed (words per minute)?",
        validate=NumberValidator(),
    ).execute()
    prompt_crud.create_prompt_config(user_id, topic,scope, int(wpm))
    print("Prompt config saved :)")

    add_tokens_flow(user_id)
    
    if inquirer.confirm(message="Would you like to schedule this user's post right now?").execute():
        add_schedule_flow(user_id)
    print("User setup complete\n")


# Cli logic for choosing an user
def pick_user() -> dict:
    users = user_crud.get_all_users()
    if not users:
        print("No users found. Create one first...")
        return None
    choice = inquirer.select(
        message="Pick a user",
        choices=[f"{u['id']}: {u['username']}"  for u in users] + ["Cancel"]
    ).execute()
    if choice == "Cancel":
        return None
    user_id = int(choice.split(":")[0])
    return next((u for u in users if u['id'] == user_id), None)


# Cli logic for performing operations in a selected user (Edit/Deletion/triggering short creation manually)
def user_menu_flow(user:dict) -> None:
    while True:
        print(f"\n User: {user['username']} (id={user['id']})")
        choice = inquirer.select(
            message="What would you like to do?",
            choices=[
                "Update prompt config",
                "Update schedule",
                "Update voice_id",
                "Update social tokens",
                "Generate a video",
                "Delete user",
                "Go back",
            ]
        ).execute()
        
        if choice == "Update prompt config":
            update_prompt_config_flow(user['id'])
        elif choice == "Update schedule":
            schedule_management_flow(user['id'])
        elif choice == "Update voice_id":
            new_voice_id = inquirer.text(message="New voice_id:").execute()
            user_crud.update_voice_id(user['id'], new_voice_id)
            print("Voice_id updated")
        elif choice == "Update social tokens":
            tokens_management_flow(user['id'])
        elif choice == "Generate a video":
            path = generate_video.generate_video(user['id'])
            print(f"✅ Video generated at {path}")
        elif choice == "Delete user":
            if inquirer.confirm(message=f"Are you sure you want to delete the user {user['username']}?").execute():
                user_crud.delete_user(user['id'])
                print("User deleted")
                return
        else:
            return


# Cli logic to update the prompt configuration of a user
def update_prompt_config_flow(user_id:int) -> None:
    config = prompt_crud.get_prompt_config(user_id)
    print(f"current topic: {config['topic']}")
    print(f"current scope: {config['scope']}")
    print(f"current wpm:   {config['wpm']}")
    field = inquirer.select(
        message="Which field to update?",
        choices=["topic", "scope", "wpm", "cancel"]
    ).execute()
    if field == "cancel":
        return
    elif field == "wpm":
        new = int(inquirer.text(
            message=f"New {field}:",
            validate=NumberValidator()
        ).execute())
    else:
        new = inquirer.text(message=f"New {field}:").execute()
    prompt_crud.update_prompt_config_field(user_id, field, new)
    print("Prompt config updated")


# Cli logic to add an entry to an user posting schedule
def add_schedule_flow(user_id: int) -> None:
    day = inquirer.select(
        message="Day of week",
        choices=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    ).execute()
    # While loop to ensure the input time is valid
    while True:
        hour_str = inquirer.text(message="Hour (0–23):").execute()
        if hour_str.isdigit():
            hour = int(hour_str)
            # Only exits the loop if the input is valid
            if 0 <= hour <= 23:
                break
        print("Please enter a valid hour between 0 and 23.")
    # Try to create schedule
    schedule_id = schedule_crud.create_schedule(user_id, day, hour)
    if schedule_id is None:
        # Already exists so skip the rest
        return
    # Checks if we already have an user with the same schedule (meaning cron/WTS already has an scheduled run at that time)
    users_in_slot = schedule_crud.get_users_to_post_at(day, hour)
    if len(users_in_slot) == 1: # If it is just the recently added user then add to the system scheduler
        if scheduler_manager.add_schedule_task(day, hour):
            print("System task created.")
        else:
            print("System task already existed or failed.")
    print("Schedule entry added.")


# Cli logic to edit an user's posting schedule
def schedule_management_flow(user_id:int) -> None:
    print("Current schedule:")
    schedule = schedule_crud.get_user_schedule(user_id)
    for day, hour in schedule:
        print(f" • {day} at {hour:02d}:00")
    
    action = inquirer.select(
        message="What would you like to do?",
        choices=["Add Entry", "Remove Entry", "Go back"]
    ).execute()
    if action == "Add Entry":
        add_schedule_flow(user_id)
    elif action == "Remove Entry":
        if not schedule:
            print("No entries to remove")
            return
        entry = inquirer.select(
            message="What entry do you wish remove?",
            choices=[f"{d} at {h:02d}:00" for d, h in schedule]
        ).execute()
        entry_day, entry_hour_str = entry.split(" at ")
        entry_hour = int(entry_hour_str.split(":")[0])
        schedule_crud.remove_schedule(user_id, entry_day, entry_hour)
        # Check if any other users still need the cron/WTS at the specified time
        users_in_slot = schedule_crud.get_users_to_post_at(entry_day, entry_hour)
        if not users_in_slot: # None left so we can remove from system scheduler
            if scheduler_manager.remove_schedule_task(entry_day, entry_hour):
                print("System task removed.")
            else:
                print("System task did not exist or failed to remove.")
        print("Schedule entry removed")
    else:
        return

# Cli logit to add social media tokens
def add_tokens_flow(user_id: int) -> None:
    platforms = ["youtube", "instagram", "tiktok"]

    for platform in platforms:
        print(f"\n--- {platform.upper()} ---")
        access = inquirer.text(message="Access token (leave blank for now)").execute()
        refresh = inquirer.text(message="Refresh token (leave blank for now)").execute()
        expiry = inquirer.text(message="Expiry (leave blank for now)").execute()
        username = inquirer.text(message="Login username (leave blank for now)").execute()
        password = inquirer.secret(message="Login password (leave blank for now)").execute()

        tokens_crud.create_token(
            user_id,
            platform,
            access or None, refresh or None,
            expiry or None, username or None,
            password or None
        )

    print("Tokens initialized for all platforms.")


# Cli logic to manage a user's social media posting tokens
def tokens_management_flow(user_id:int) -> None:
    platform = inquirer.select(
        message="Which platform?",
        choices=["youtube","instagram","tiktok"]
    ).execute()
    current_tokens = tokens_crud.get_token_by_user_and_platform(user_id, platform)
    print("Current:", current_tokens)

    access = inquirer.text(message="New access token (leave blank to skip)").execute()
    refresh = inquirer.text(message="New refresh token (leave blank to skip)").execute()
    expiry = inquirer.text(message="New expiry (leave blank to skip)").execute()
    username = inquirer.text(message="Login username (leave blank to skip)").execute()
    password = inquirer.secret(message="Login password (leave blank to skip)").execute()
    tokens_crud.update_token(
        user_id,platform,
        access or None, refresh or None,
        expiry or None, username or None,
        password or None
        )
    print("Token updated")