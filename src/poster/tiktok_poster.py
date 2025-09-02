import os
import json
import time
import random
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from undetected_chromedriver import Chrome as UcChrome
from src.crud.tokens_crud import get_token_by_user_and_platform
from src.crud.tokens_crud import update_token

# If scaled consider proxy rotation
# Function to create the selenium driver
def create_driver(headless: bool) -> UcChrome:
    ua = UserAgent()
    random_user_agent = ua.random  # Generate random user agent per session

    options = Options()

    # Basic stealth flags
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    # Randomized window size for fingerprinting avoidance
    width = random.randint(1200, 1400)
    height = random.randint(700, 900)
    options.add_argument(f"--window-size={width},{height}")

    # Random user agent
    options.add_argument(f"--user-agent={random_user_agent}")
    # Headless mode if required
    if headless:
        options.add_argument("--headless=new")

    # Initialize driver
    driver = UcChrome(options=options, headless=headless)
    # Add a small randomized delay after startup
    time.sleep(random.uniform(1.5, 3.5))
    return driver


# Function to login and save the session cookies locally
def login_and_save_session(user_id:int) -> None:
    # Navigate to the login page
    driver = create_driver(False)
    driver.get("https://www.tiktok.com/login")
    input("[ACTION REQUIRED] Log in manually, then press Enter to continue.")
    cookies_json = json.dumps(driver.get_cookies())
    # Save the cookies to the database
    update_token(user_id, "tiktok", cookies=cookies_json)


# Function to load the saved session
def load_session(user_id: int, driver: UcChrome) -> bool:
    # Get the cookies from the databse
    token = get_token_by_user_and_platform(user_id, "tiktok")
    cookies = json.loads(token['cookies'])
    # Navigate to tiktok
    driver.get("https://www.tiktok.com/")
    # Load the cookies to the driver
    for cookie in cookies:
        cookie.pop("sameSite", None)
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Skipping problematic cookie: {cookie} ({e})")
    # Refresh the page once the cookies are loaded
    driver.refresh()
    return True


# Function to check if the session is still vaid
def needs_relogin(user_id: int,driver: UcChrome) -> bool:
    if not load_session(user_id ,driver, username):
        return True
    # Navigate to the upload view, if not logged in it will redirect to the login view
    driver.get("https://www.tiktok.com/upload")
    time.sleep(5)
    return "login" in driver.current_url


# Function to post the video to tiktok
def post_to_tiktok(user_id:int, final_video_path:str, description:str) -> bool:

    # Check if the user has the tokens set up for psoting in the platform (only username for now)
    tokens = get_token_by_user_and_platform(user_id, "tiktok")
    if not tokens:
        print(f"No TikTok credentials found for user {user_id}. Skipping post.")
        return False

    try:
        driver = create_driver(True)
        # Checks if the session is not valid
        if needs_relogin(user_id ,driver):
            driver.quit() # Closes old driver to start clean
            # If the session data does not work then we login manually
            login_and_save_session(user_id)
            # Starts a new driver to avoid stale context
            driver = create_driver(True)
            # Loads the session cookies to the driver
            load_session(user_id, driver)
    
        # Navigate to tiktok's upload view 
        driver.get("https://www.tiktok.com/upload")

        # Upload the video
        WebDriverWait(driver,20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        ).send_keys(final_video_path)


        # Check if a modal pops up and close it
        try:
            modal_close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".TUXModal button, .TUXModal [role='button']"))
            )
            modal_close_btn.click()
            print("Modal detected and closed.")
            time.sleep(1)
        except:
            # No modal detected — safe to continue
            pass

        # Enter video description
        caption_box = WebDriverWait(driver,20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[contenteditable='true']"))
        )
        caption_box.click()
        # Delete any autofilled description
        caption_box.send_keys(Keys.CONTROL + "a")
        caption_box.send_keys(Keys.DELETE)
        # Send the actual description
        caption_box.send_keys(description)
        time.sleep(random.uniform(1, 3))


        # Set video to public
        visibility_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".Select__content"))
        )
        visibility_dropdown.click()
        time.sleep(1)
        public_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-value="&quot;0&quot;"]'))
        )
        public_option.click()
    
        # Click the post button
        WebDriverWait(driver,20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,"[data-e2e='post_video_button']"))
        ).click()

        # Wait for success
        # If redirected to the content view the video was posted (I think I have no idea I have not had any issue so i dont know wat would happen otherwise)
        WebDriverWait(driver,45).until(
            EC.url_contains("tiktokstudio/content")
        )
        print(f"[SUCCESS] Video {final_video_path} posted to tiktok")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to confirm upload: {e}")
        return False
    finally:
        try:
            if driver:
                driver.quit()
        except Exception as close_error:
            print(f"[WARN] Failed to cleanly close driver: {close_error}")

# SIMPLE TEST TO RUN THE FILE TO SEE IF IT WILL ACTUALLY POST
# Unused id since we wont be querying from the db, url of the video to post and placeholder description for the caption
# post_to_tiktok(1,r"C:\Users\Fabricio\personalProjects\AutoShorts\output\prompt_1\ciabatta_bread\final_video.mp4","This video will be deleted, it is just a test upload to see if the selenium posting logic in a pytho app works.")