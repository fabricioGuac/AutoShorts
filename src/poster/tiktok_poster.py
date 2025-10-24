import os
import json
import time
import random
import tempfile
import platform
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import undetected_chromedriver as uc
from src.crud.tokens_crud import get_token_by_user_and_platform, update_token

# ---------- Configuration ----------
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload"
LOGIN_URL = "https://www.tiktok.com/login"
SUCCESS_URL_FRAGMENT = "tiktokstudio/content"
# CSS / XPaths we rely on (tweak if the page changes)
FILE_INPUT_CSS = "input[type='file']"
CAPTION_CSS = "[contenteditable='true']"
POST_BTN_CSS = "[data-e2e='post_video_button']"
MODAL_CONTAINER_CSS = ".TUXModal"

# ---------- Driver & stealth helpers ----------
# Creates an undetected-chromedriver Chrome instance tuned for TikTok.
def create_driver(headless: bool = False) -> uc.Chrome:

    # Creates a temporary directory to act as as Chrome's user data directory 
    # in an isolated enviroment per run. Keeps cookies, cache, and extensions
    temp_profile = Path(tempfile.mkdtemp())

    # Builds pre launch Chrome options
    options = uc.ChromeOptions()

    # Sets the browser's user ageny header to avoid flagging
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={ua}")

    # Randomizes the window size to mimic human variation
    options.add_argument(f"--window-size={random.randint(1280,1440)},{random.randint(800,900)}")
    # Tells Chrome to use the temporary folder as the profile directory
    options.add_argument(f"--user-data-dir={str(temp_profile)}")
    # Sets the preferred language
    options.add_argument("--lang=en-US,en;q=0.9")
    # Bypass the 'first run' experience  (signing in, setting up defalt browser, customize settinsg)
    options.add_argument("--no-first-run")
    # Suppresses the infobar asking you to set the browser as the default
    options.add_argument("--no-default-browser-check")
    # Forces simple password store to avoid platform specific keychains
    options.add_argument("--password-store=basic")
    # Avoids interactin with the macOS keychain 
    options.add_argument("--use-mock-keychain")

    # Linux specific flags
    if platform.system() == "Linux":
        options.add_argument("--no-sandbox") # Disables Chrome's sandbox where the kernel sandbox causes Chrome to fail to start
        options.add_argument("--disable-dev-shm-usage") # Disables /dv/shm that could crash Chrome, using diskbased temp files instead

    # Prefer old headless (many sites detect new headless)
    if headless:
        options.add_argument("--headless=old")
        options.add_argument("--disable-gpu") # can be useful for improving stability in headless mode

    # Creates an undetected chromedriver Chrome instance. (use_subprocess=True runs the browser in a separate subproces)
    driver = uc.Chrome(options=options, use_subprocess=True)

    # Post-start small Chrome DevTools Protocol stealth patches (run on every page)
    try:
        """
        * navigator.webdriver = undefined: Many automation frameworks set 'navigator.webdriver' to 
        true. Overriding it hides that obvious signal.

        * window.navigator.chrome = { runtime: {} }: Some sites check if 'window.navigator.chrome'
        presence to detect Chrom. Populating a minimal object reduces mismatch errors.

        * navigator.language and navigator.languages: Make sure JS-visible locale(s) match the
        --lang flag below ("en-US,en;q=0.9" -> primary 'en-US').


        * navigator.plugins = [1,2,3,4,5]: Headless often reports zero plugins. Returniong
        a small array gives a more realistic fingerprint 
        """
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.navigator.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'language', {get: () => 'en-US'});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            """
        })
    except Exception as e:
        print(f"[WARN] CDP stealth patch failed: {e}")

    # small startup delay
    time.sleep(random.uniform(1.0, 2.0))
    return driver

# Function to prevent onelink/intent deeplink redirects that kill the upload flow
# using CDP blocked URLs and JS overrides for window.open/location.assign
def block_onelink_and_intents(driver: uc.Chrome):


    try:
        # Enables the Network domain and blocks known deep-link redirect URLs

        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setBlockedURLs", {
            "urls": [
                "*onelink.me/*",
                "*tiktokstudio.onelink.me/*",
                "intent://*",
                "*creator_app*"
            ]
        })
    except Exception as e:
        # not fatal, continue
        print(f"[WARN] CDP block failed: {e}")

    # JS-level fallback to neutralize attempts to open deep links
    try:
        driver.execute_script("""
        (function(){
            window.__orig_open = window.open;
            window.open = function(url) {
                if(!url) return null;
                if(typeof url === 'string' && (url.includes('onelink.me') || url.startsWith('intent:') || url.includes('creator_app'))) {
                    console.log('Blocked deep link:', url);
                    return null;
                }
                return window.__orig_open.apply(this, arguments);
            };
            window.__orig_assign = window.location.assign.bind(window.location);
            window.location.assign = function(url) {
                if(typeof url === 'string' && (url.includes('onelink.me') || url.startsWith('intent:') || url.includes('creator_app'))){
                    console.log('Blocked assign:', url);
                    return;
                }
            return window.__orig_assign(url);
            };
        })();
        """)
    except Exception:
        pass

# ---------- Cookie helpers ----------
# Function to login and save the cookies to DB
def login_and_save_session(user_id: int) -> None:
    driver = None
    try:
        # Open a visible browser (non-headless) for manual login
        driver = create_driver(False)
        driver.get(LOGIN_URL)
        input("[ACTION REQUIRED] Log in manually in the opened browser, then press Enter here to continue...")
        # Serialize cookies from the active browser session
        cookies_json = json.dumps(driver.get_cookies())
        # Saves the cookies to DB
        update_token(user_id, "tiktok", cookies=cookies_json)
        print("[INFO] Cookies saved to DB.")
    finally:
        # Ensure the browser closes cleanly
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

# Function to load a saved TikTok session into the active driver
def load_session(user_id: int, driver: uc.Chrome) -> bool:

    # Retrieve the cookies from the DB
    token = get_token_by_user_and_platform(user_id, "tiktok")
    # Early return if the cookies are not found
    if not token or not token.get("cookies"):
        return False

    # Deserialize cookies from JSON
    try:
        cookies = json.loads(token["cookies"])
    except Exception:
        return False

    # Navigate to TikTok so the domain context exists before adding cookies
    driver.get("https://www.tiktok.com/")
    time.sleep(1)
    # Inject each cookie into the browser session
    for cookie in cookies:
        cookie.pop("sameSite", None) # remove unsupported attribute if present
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            # skip problematic cookies
            print(f"[DEBUG] Skipping cookie: {cookie.get('name')} ({e})")
    # Refresh the page after loading the session cookies
    driver.refresh()
    time.sleep(2)
    return True

# ---------- Helpers for UI interaction ----------
# Function to handle tiktok modals (confirmations or warnings)
def confirm_or_close_modal_if_present(driver: uc.Chrome, post_click_phase: bool = False) -> None:
    try:
        # Waits for a modal container to appear on screen
        modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, MODAL_CONTAINER_CSS))
        )
    except Exception:
        return  # no modal present

    try:
        # Extract and lowercase the modal text for easier  keyword checks
        modal_text = modal.text.lower() if modal.text else ""
    except Exception:
        modal_text = ""

    # Button labels to look for
    confirm_labels = ["confirm", "continue", "ok"]
    post_labels = ["post", "publish", "continue to post", "post now"]

    try:
        # Find all buttons in themodal
        buttons = modal.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            try:
                label = btn.text.strip().lower()
                # If post phase, look for post/publish buttons
                if post_click_phase and any(pl in label for pl in post_labels):
                    btn.click()
                    print(f"[INFO] Clicked post-confirm modal button: '{btn.text}'")
                    time.sleep(1)
                    return
                # Otherwise, check regular confirm buttons
                elif any(cl in label for cl in confirm_labels) or "copyright" in modal_text:
                    btn.click()
                    print(f"[INFO] Clicked confirm modal button: '{btn.text}'")
                    time.sleep(1)
                    return
            except Exception:
                continue

        # fallback: click first button if we are desperate (usually safe to close modal)
        if buttons:
            buttons[0].click()
            print("[INFO] Fallback clicked first modal button")
            time.sleep(0.6)
    except Exception:
        pass

# Function to open the visibility dropdown and set it public (Everyone)
def find_and_set_visibility_public(driver: uc.Chrome) -> None:
    
    # Common visible texts for the trigger button
    texts_to_try = ["Everyone", "Public"]
    trigger = None

    # Try to locate the dropdown trigger using the exact visible label
    for txt in texts_to_try:
        try:
            trigger = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[.//div[text()='{txt}']]"))
            )
            break # Stops once found
        except Exception:
            continue

    # Fallback: look for combobox buttons and check their inner div for keywords
    if not trigger:
        try:
            candidates = driver.find_elements(By.CSS_SELECTOR, "button[role='combobox']")
            for c in candidates:
                try:
                    inner = c.find_element(By.XPATH, ".//div")
                    if inner and inner.text.strip():
                        if any(k.lower() in inner.text.strip().lower() for k in ["every",  "public"]):
                            trigger = c
                            break
                except Exception:
                    continue # Skip if inner div cannot be read
        except Exception:
            pass # Ignore if no candidates are found

    # If still not found, raise an error
    if not trigger:
        raise RuntimeError("Visibility trigger not found")

    # Clicks the trigger, wait for options to render
    trigger.click()
    time.sleep(random.uniform(0.4, 1.1))

    # Finds the public option by data-value attribute (TikTok uses '"0"' for public)
    try:
        public_opt = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='option'][data-value='&quot;0&quot;'], div[role='option'][data-value='\"0\"'], div[role='option'][data-value='0']"))
        )
        # Scrolls the option into view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", public_opt)
        time.sleep(0.3)
        public_opt.click()
        time.sleep(0.6)
        return
    except Exception as e:
        # Last-resort: locate the option by visible text "Everyone" or "Public"
        try:
            public_opt = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='option']//div[contains(., 'Everyone') or contains(., 'Public')]"))
            )
            public_opt.click()
            time.sleep(0.6)
            return
        except Exception:
            raise RuntimeError(f"Could not select 'Public' option: {e}")

# ---------- Main poster ----------
# Function to post the video to tiktok
def post_to_tiktok(user_id: int, final_video_path: str, description: str, headless: bool = True) -> bool:
    driver = None
    try:
        # Check DB for saved TikTok session cookies
        tokens = get_token_by_user_and_platform(user_id, "tiktok")
        if not tokens:
            print(f"[WARN] No TikTok tokens for user {user_id}.")
            return False

        # Launch an undetected Chrome session
        driver = create_driver(headless=headless) 
        # Prevent deeplink redirects that can break the upload flow
        block_onelink_and_intents(driver)

        # Try to load session cookies; fall back to manual login if missing
        if not load_session(user_id, driver):
            print("[INFO] No cookies found: please log in interactively to seed cookies.")
            driver.quit() # Closes old driver to start clean
            login_and_save_session(user_id) # Manual login
            driver = create_driver(headless=headless) # Starts a new driver to avoid stale context
            block_onelink_and_intents(driver) # Re-apply deeplink blocker
            if not load_session(user_id, driver):
                print("[ERROR] Failed to load session after interactive login.")
                return False

        # Navigate to tiktok upload page
        driver.get(UPLOAD_URL)
        time.sleep(3)  # Give JS time to load

        # Validate video file path
        final_video_path = str(Path(final_video_path).resolve())
        if not Path(final_video_path).exists():
            print(f"[ERROR] Video file does not exist: {final_video_path}")
            return False

        # Uploads file input
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, FILE_INPUT_CSS))).send_keys(final_video_path)
        time.sleep(1.0)

        # Handles any modal that may appear (copyright / confirm)
        confirm_or_close_modal_if_present(driver)

        # Fills caption
        caption_box = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, CAPTION_CSS)))
        caption_box.click()
        caption_box.send_keys(Keys.CONTROL + "a") # Select all existing text
        caption_box.send_keys(Keys.DELETE) # Clear it
        caption_box.send_keys(description) # Enter new caption
        time.sleep(random.uniform(0.7, 1.5))

        # Sets visibility (Everyone)
        find_and_set_visibility_public(driver)

        # Ensures the post button is visible and click it (JS click as fallback)
        post_btn = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, POST_BTN_CSS)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", post_btn)
        time.sleep(random.uniform(1.4, 3.0))
        try:
            post_btn.click()
        except Exception:
            # Fallback to JS click if Selenium click fails
            driver.execute_script("arguments[0].click();", post_btn)
        
        # Handles any post-confirmation modals
        time.sleep(3.5)
        confirm_or_close_modal_if_present(driver, post_click_phase=True)

        # Wait for success: either URL fragment or a content element
        try:
            WebDriverWait(driver, 120).until(lambda d: SUCCESS_URL_FRAGMENT in (d.current_url or "") or len(d.find_elements(By.CSS_SELECTOR, "div.PostItem, [data-e2e='post-list-item']")) > 0)
            print(f"[SUCCESS] Video {final_video_path} posted to TikTok.")
            return True
        except Exception:
            # Save page screenshot for debugging
            try:
                error_dir = "output/errors"
                os.makedirs(error_dir, exist_ok=True)
                fn = os.path.join(error_dir, f"tiktok_post_error_{int(time.time())}.png")
                print(f"[DEBUG] Saved screenshot to {fn}")
            except Exception:
                pass
            print("[WARN] Upload not confirmed within timeout.")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to post to TikTok: {e}")
        return False

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass