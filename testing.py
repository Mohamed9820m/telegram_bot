import requests
import time
from playwright.sync_api import sync_playwright, TimeoutError

# 🔹 Telegram Bot Setup
BOT_TOKEN = "7837741793:AAHlD2m2260cFqaDNlBlDGxHM1AIF_tUbZ4"
CHAT_ID = "7328850919"

# Global variables
browser = None
page = None
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
    """Start the bot using Playwright."""
    global browser, page, is_running
    is_running = True

    with sync_playwright() as p:
        # Launch Chromium in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Open the website with retry logic
        retries = 3
        for attempt in range(retries):
            try:
                send_telegram_message(f"🌍 Attempt {attempt + 1}: Accessing the booking portal...")
                page.goto("https://inforyou.teamsystem.com/ssdunime/", timeout=60000)
                break  # Exit the loop if successful
            except TimeoutError:
                if attempt == retries - 1:
                    send_telegram_message("❌ Failed to load the website. Please try again later.")
                    reset_bot()
                    return
                time.sleep(5)  # Wait before retrying

        # Click "Accedi" button
        try:
            send_telegram_message("🔍 Logging in...")
            page.click("button:has-text('Accedi')")
            time.sleep(2)
        except Exception as e:
            send_telegram_message("❌ Unable to proceed with login. Please try again later.")
            reset_bot()
            return

        # Enter login credentials
        try:
            page.fill("input[formcontrolname='username']", "mrnmmd02h20z352x@studenti.unime.it")
            page.fill("input[formcontrolname='password']", "MED9820med")
            page.click("button:has-text('Accedi')")
            time.sleep(5)
        except Exception as e:
            send_telegram_message("❌ Login failed. Please check your credentials and try again.")
            reset_bot()
            return

        # Check if login was successful
        if "dashboard" in page.url or "profile" in page.url:
            send_telegram_message("🎉 Login successful!")
        else:
            send_telegram_message("❌ Login failed. Please try again.")
            reset_bot()
            return

        # Click "Prenota" button
        try:
            send_telegram_message("🔍 Accessing the booking section...")
            page.click("a:has-text('Prenota')")
            time.sleep(3)
        except Exception as e:
            send_telegram_message("❌ Unable to access the booking section. Please try again.")
            reset_bot()
            return

        # Wait for the calendar to load
        send_telegram_message("⏳ Loading available dates...")
        page.wait_for_selector(".cal-day-badge")

        # Find and click the target date
        target_date = TARGET_DATE  # Replace with user input
        try:
            page.click(f"text={target_date}")
            send_telegram_message(f"✅ Clicked on {target_date}!")
        except Exception as e:
            send_telegram_message("❌ Unable to select the date. Please try again.")
            reset_bot()
            return

        # Check and report available sessions
        events = page.query_selector_all(".cal-event")
        found_events = {}  # Dictionary to map button text to full session text

        for event in events:
            bg_color = page.evaluate("(element) => window.getComputedStyle(element).backgroundColor", event)
            if bg_color.strip() == "rgb(8, 227, 49)":
                try:
                    span_element = event.query_selector("./following-sibling::span")
                    full_session_text = span_element.inner_text().strip()
                    
                    if TARGET_TEXT in full_session_text:
                        time_slot = full_session_text.split("|")[1].strip()
                        simplified_text = f"MARIANI STUDENTI | {time_slot}"
                        found_events[simplified_text] = full_session_text
                except Exception:
                    continue

        if found_events:
            send_inline_buttons(list(found_events.keys()))
        else:
            send_telegram_message("ℹ️ No available sessions found for the selected date.")

        # Wait for user selection
        selected_button_text = None
        while not selected_button_text:
            selected_button_text = check_telegram_callback()
            time.sleep(1)

        if selected_button_text in found_events:
            full_session_text = found_events[selected_button_text]
            send_telegram_message(f"🔍 Full session text: {full_session_text}")

            # Click the selected session on the website
            try:
                page.click(f"text='{full_session_text}'")
                send_telegram_message(f"✅ Selected session: {full_session_text}")
            except Exception as e:
                send_telegram_message("❌ Unable to select the session. Please try again.")
                reset_bot()
                return

            # Click the 'Prenota' button
            try:
                page.click("button:has-text('Prenota')")
                send_telegram_message("✅ Clicked 'Prenota' button!")
            except Exception as e:
                send_telegram_message("❌ Unable to complete the booking. Please try again.")
                reset_bot()
                return

            # Extract and send the result message
            try:
                result_message_element = page.wait_for_selector(
                    "//div[@class='col-sm-12 text-center']//p[@class='warning animated fadeInDown ng-star-inserted']",
                    timeout=10000
                )
                result_message = result_message_element.inner_text().strip()
                send_telegram_message(f"📢 Result: {result_message}")
            except Exception as e:
                send_telegram_message("❌ Unable to retrieve the result message. Please check manually.")
        else:
            send_telegram_message("❌ Invalid session selection. Please try again.")

        # Close the browser
        browser.close()
        is_running = False

def reset_bot():
    """Reset the bot and close the browser."""
    global browser, page, is_running
    if browser:
        browser.close()
        browser = None
        page = None
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