import requests
import time
from playwright.sync_api import sync_playwright

# 🔹 Telegram Bot Setup
BOT_TOKEN = "7837741793:AAHlD2m2260cFqaDNlBlDGxHM1AIF_tUbZ4"
CHAT_ID = "7328850919"

# Global variables
browser = None
page = None
is_running = False

def send_telegram_message(message):
    """Send a message to Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

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

        # Open the website
        send_telegram_message("🌍 Accessing the booking portal...")
        page.goto("https://inforyou.teamsystem.com/ssdunime/")
        time.sleep(3)

        # Click "Accedi" button
        send_telegram_message("🔍 Logging in...")
        page.click("button:has-text('Accedi')")
        time.sleep(2)

        # Enter login credentials
        page.fill("input[formcontrolname='username']", "mrnmmd02h20z352x@studenti.unime.it")
        page.fill("input[formcontrolname='password']", "MED9820med")
        page.click("button:has-text('Accedi')")
        time.sleep(5)

        # Check if login was successful
        if "dashboard" in page.url or "profile" in page.url:
            send_telegram_message("🎉 Login successful!")
        else:
            send_telegram_message("❌ Login failed. Please check your credentials.")
            reset_bot()
            return

        # Click "Prenota" button
        send_telegram_message("🔍 Accessing the booking section...")
        page.click("a:has-text('Prenota')")
        time.sleep(3)

        # Wait for the calendar to load
        send_telegram_message("⏳ Loading available dates...")
        page.wait_for_selector(".cal-day-badge")

        # Find and click the target date
        target_date = "17"  # Replace with user input
        page.click(f"text={target_date}")
        send_telegram_message(f"✅ Clicked on {target_date}!")

        # Check and report available sessions
        events = page.query_selector_all(".cal-event")
        for event in events:
            if "FITNESS - SALA PESI PAL. MARIANI STUDENTI" in event.inner_text():
                send_telegram_message(f"✅ Found session: {event.inner_text()}")

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