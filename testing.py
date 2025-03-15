import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 🔹 Telegram Bot Setup
BOT_TOKEN = "7837741793:AAHlD2m2260cFqaDNlBlDGxHM1AIF_tUbZ4"
CHAT_ID = "7328850919"

# Global variables
driver = None
is_running = False

def send_telegram_message(message, reply_markup=None):
    """Send a message to Telegram with optional inline buttons."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup  # Add inline keyboard if provided
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def check_telegram_callback():
    """Check for button clicks on Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
        updates = response.get("result", [])
        
        if updates:
            # Process only the last update
            last_update = updates[-1]
            if "callback_query" in last_update:
                callback_data = last_update["callback_query"]["data"]
                # Acknowledge the callback
                requests.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                    json={"callback_query_id": last_update["callback_query"]["id"]}
                )
                return callback_data
    except Exception as e:
        print(f"Error fetching Telegram updates: {e}")
    return None

def send_inline_buttons(buttons):
    """Send interactive buttons for session choices."""
    inline_keyboard = {
        "inline_keyboard": [
            [{"text": button, "callback_data": button}] for button in buttons
        ]
    }
    send_telegram_message("Please choose your booking session:", reply_markup=inline_keyboard)

def check_telegram_message():
    """Check for new messages from the user."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url).json()
        messages = response.get("result", [])
        if messages:
            last_message = messages[-1].get("message", {}).get("text", "")
            return last_message.strip().lower()
    except Exception as e:
        print(f"Telegram Error: {e}")
    return None    

def start_bot():
    """Start the bot and initialize the booking process."""
    global driver, is_running
    is_running = True

    # ✅ Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode

    # ✅ Start WebDriver
    send_telegram_message("🚀 Initializing the booking system... Please wait.")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Configuration
    TARGET_TEXT = "FITNESS - SALA PESI PAL. MARIANI STUDENTI"
    URL = "https://inforyou.teamsystem.com/ssdunime/"

    # Prompt user to enter the target date
    send_telegram_message("📅 Please enter the target date (e.g., 17 for the 17th):")
    while True:
        user_input = check_telegram_message()
        if user_input and user_input.isdigit():
            TARGET_DATE = user_input
            send_telegram_message(f"✅ Target date set to: {TARGET_DATE}")
            break
        time.sleep(1)

    # ✅ Open the website
    send_telegram_message("🌍 Accessing the booking portal...")
    driver.get(URL)
    time.sleep(3)

    # ✅ Click "Accedi" button
    try:
        send_telegram_message("🔍 Logging in...")
        accedi_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accedi')]"))
        )
        accedi_button.click()
        time.sleep(2)
    except Exception as e:
        send_telegram_message("❌ Unable to proceed with login. Please try again later.")
        reset_bot()
        return

    # ✅ Enter login credentials
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='username']"))
        )
        email_field.send_keys("mrnmmd02h20z352x@studenti.unime.it")

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@formcontrolname='password']"))
        )
        password_field.send_keys("MED9820med")

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Accedi')]"))
        )
        login_button.click()
        time.sleep(5)
    except Exception as e:
        send_telegram_message("❌ Login failed. Please check your credentials and try again.")
        reset_bot()
        return

    # ✅ Check if login was successful
    current_url = driver.current_url
    if "dashboard" in current_url or "profile" in current_url:
        send_telegram_message("🎉 Login successful!")
    else:
        send_telegram_message("❌ Login failed. Please try again.")
        reset_bot()
        return

    # ✅ Click "Prenota" button after login
    try:
        send_telegram_message("🔍 Accessing the booking section...")
        prenota_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Prenota')]"))
        )
        prenota_button.click()
        time.sleep(3)
    except Exception as e:
        send_telegram_message("❌ Unable to access the booking section. Please try again.")
        reset_bot()
        return

    # ✅ Wait for the calendar to fetch data
    send_telegram_message("⏳ Loading available dates...")

    # ✅ Wait indefinitely until "cal-day-badge" appears on the calendar
    while True:
        try:
            badge_element = driver.find_element(By.CLASS_NAME, "cal-day-badge")
            break  # Exit the loop once found
        except:
            time.sleep(1)  # Keep checking every 1 second to avoid high CPU usage

    # ✅ Find and click the target date
    if find_and_click_date():
        session_mapping = None
        while True:
            session_mapping = check_and_report_events()
            if session_mapping:
                break
            time.sleep(5)

        # ✅ Wait for User Selection
        send_telegram_message("🛑 Click a button to select your session.")

        selected_button_text = None
        while not selected_button_text:
            selected_button_text = check_telegram_callback()
            time.sleep(1)

        send_telegram_message(f"🖱️ Selected session: {selected_button_text}")

        # ✅ Get the full session text from the mapping
        if selected_button_text in session_mapping:
            full_session_text = session_mapping[selected_button_text]
            send_telegram_message(f"🔍 Full session text: {full_session_text}")

            # ✅ Click the selected session on the website
            if not click_session_element(full_session_text):
                send_telegram_message("❌ Failed to select the session. Please try again.")
            else:
                # ✅ Click the 'Prenota' button after selecting the session
                if not click_prenota_button():
                    send_telegram_message("❌ Failed to click 'Prenota' button. Please try again.")
        else:
            send_telegram_message("❌ Invalid session selection. Please try again.")

    # Wait for 'done' before closing
    wait_for_done()

def reset_bot():
    """Reset the bot and close the browser."""
    global driver, is_running
    if driver:
        driver.quit()
        driver = None
    is_running = False
    send_telegram_message("🔄 Bot has been reset. You can start again with /start.")

# Handle Telegram commands
def handle_commands():
    """Listen for Telegram commands and execute corresponding actions."""
    global is_running
    send_telegram_message("🤖 Booking bot is online. Use /start to begin or /reset to reset.")
    while True:
        user_input = check_telegram_message()
        if user_input:
            if user_input == "/start" and not is_running:
                start_bot()
            elif user_input == "/reset":
                reset_bot()
        time.sleep(1)

# Main execution
if __name__ == "__main__":
    handle_commands()