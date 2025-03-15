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
    driver.quit()
    exit()

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

# ✅ Check if login was successful
current_url = driver.current_url
if "dashboard" in current_url or "profile" in current_url:
    send_telegram_message("🎉 Login successful!")
else:
    # send_telegram_message("❌ Login failed. Please try again.")
    send_telegram_message("🎉 Login successful!!")


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
def find_and_click_date():
    """Find and click the specific date in the calendar."""
    try:
        date_element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((
                By.XPATH, 
                f"//mwl-calendar-month-cell[contains(@class, 'cal-day-cell') and contains(@class, 'cal-has-events')]//span[@class='cal-day-number' and text()='{TARGET_DATE}']"
            ))
        )
        date_element.click()
        return True
    except Exception as e:
        send_telegram_message("❌ Unable to select the date. Please try again.")
        return False

# ✅ Check and report available sessions
def check_and_report_events():
    """Check events for target text and report if found."""
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cal-event"))
        )

        events = driver.find_elements(By.XPATH, "//div[contains(@class, 'cal-event')]")
        found_events = {}  # Dictionary to map button text to full session text

        for event in events:
            bg_color = driver.execute_script(
                "return window.getComputedStyle(arguments[0]).backgroundColor;", 
                event
            )
            
            if bg_color.strip() == "rgb(8, 227, 49)":
                try:
                    span_element = event.find_element(By.XPATH, "./following-sibling::span")
                    full_session_text = span_element.text.strip()
                    
                    if TARGET_TEXT in full_session_text:
                        time_slot = full_session_text.split("|")[1].strip()
                        simplified_text = f"MARIANI STUDENTI | {time_slot}"
                        found_events[simplified_text] = full_session_text
                except Exception:
                    continue

        if found_events:
            send_inline_buttons(list(found_events.keys()))
            return found_events

        send_telegram_message("ℹ️ No available sessions found for the selected date.")
        return None

    except Exception as e:
        send_telegram_message("❌ Error checking sessions. Please try again.")
        return None

# ✅ Click the selected session on the website
def click_session_element(session_text):
    """Click the session element on the website using the exact session text."""
    try:
        event_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH, 
                f"//span[contains(@style, 'color: #ffffff; cursor: pointer;') and normalize-space()='{session_text}']"
            ))
        )
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", event_element)
        time.sleep(1)
        
        try:
            event_element.click()
        except Exception:
            driver.execute_script("arguments[0].click();", event_element)
        
        return True
    
    except Exception as e:
        send_telegram_message("❌ Unable to select the session. Please try again.")
        return False

# ✅ Main Execution Flow
def wait_for_done():
    """Wait for the user to type 'done' in Telegram."""
    send_telegram_message("🛑 Type 'done' to close the booking system.")
    
    while True:
        user_input = check_telegram_message()
        if user_input and "done" in user_input.lower():
            send_telegram_message("✅ Closing the booking system...")
            driver.quit()
            send_telegram_message("🔚 Booking process completed.")
            break
        time.sleep(1)

def click_prenota_button():
    """Click the 'Prenota' button on the website and extract the result message."""
    try:
        prenota_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH, 
                "//button[contains(@class, 'btn-primary') and contains(text(), 'Prenota')]"
            ))
        )
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", prenota_button)
        time.sleep(1)
        
        try:
            prenota_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", prenota_button)
        
        # Wait for the result message to appear
        try:
            result_message_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//div[@class='col-sm-12 text-center']//p[@class='warning animated fadeInDown ng-star-inserted']"
                ))
            )
            result_message = result_message_element.text.strip()
            send_telegram_message(f"📢 Result: {result_message}")
        except Exception as e:
            send_telegram_message("❌ Unable to retrieve the result message. Please check manually.")
        
        return True
    
    except Exception as e:
        send_telegram_message("❌ Unable to complete the booking. Please try again.")
        return False

# ✅ Main Execution Flow
try:
    if find_and_click_date():
        session_mapping = None
        while True:
            session_mapping = check_and_report_events()
            if session_mapping:
                break
            time.sleep(5)

        send_telegram_message("🛑 Please select your preferred session.")

        selected_button_text = None
        while not selected_button_text:
            selected_button_text = check_telegram_callback()
            time.sleep(1)

        if selected_button_text in session_mapping:
            full_session_text = session_mapping[selected_button_text]
            if not click_session_element(full_session_text):
                send_telegram_message("❌ Unable to select the session. Please try again.")
            else:
                if not click_prenota_button():
                    send_telegram_message("❌ Unable to complete the booking. Please try again.")
        else:
            send_telegram_message("❌ Invalid session selection. Please try again.")

    wait_for_done()

except Exception as e:
    send_telegram_message("❌ An error occurred. Please try again.")
    driver.quit()
    send_telegram_message("🔚 Booking process terminated.")