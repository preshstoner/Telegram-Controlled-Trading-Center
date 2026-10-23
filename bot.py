import time
import os 
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Load enviroment variables from the .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000") # Points to your FastAPI trading backend

def safe_api_request(method: str, endpoint: str, **kwargs):
    """
    Sends an HTTP request with built-in handling for HTTP 429 ('Too Many Requests') using backoff and Retry-After headers.
    """
    url = f"{API_BASE_URL}{endpoint}"
    max_retries = 3
    delay = 2 # Initial base delay in seconds

    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, timeout=5, **kwargs)

            # If rate-limited, back off and retry
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", delay))
                logger.warning(f"Rate limit hit (429) on {endpoint}. Retrying in {retry_after}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_after)
                delay *= 2 # Exponential increase
                continue

            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error connecting to tradding backend: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)
    return None



async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when /start is issued."""
    await update.message.reply_text(
        "🤖 *Trading Bot Manager Online*\n\n"
        "Use /performance to check profits\n"
        "Use /status to check system health\n"
        "Use /bot_start or /bot_stop to control execution.",
        parse_mode="Markdown"
    )

async def performance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches performance metrics from the trading bot API."""
    try:
        response = safe_api_request("GET", "/performance")
        if not response or response.status_code != 200:
            await update.message.reply_text("❌ Error: Unable to fetch performance data right now.")
            return

        
        data = response.json()
        profit = data.get("profit", "N/A")
        status = data.get("status", "unknown")


        await update.message.reply_text(
            f"📈 *Current Performance Report*\n"
            f"• Profit/Loss: `{profit}`\n"
            f"• Market State: `{status}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Failed to fetch performance: {e}")
        await update.message.reply_text("❌ Error: Could not connect to the trading bot backend.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks overall bot operational status"""
    try:
        response = safe_api_request("GET", "/status")
        if not response or response.status_code != 200:
            await update.message.reply_text("❌ Error: Trading backend is unresponsive.")
            return

        
        data = response.json()
        await update.message.reply_text(
            f"⚙️ *Bot System Status*\n"
            f"• State: `{data['status']}`\n"
            f"• Asset Pair: `{data['pair']}`\n"
            f"• Total Executed Trades: `{data['trades']}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text("❌ Error: Trading backend is offline.")

async def control_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends start/stop control signals to the trading backend."""
    command_text = update.message.text.lower()
    action = "start" if "start" in command_text else "stop"

    try:
        response = safe_api_request("POST", "/control", json={"action": action})
        if not response or response.status_code != 200:
            await update.message.reply_text("❌ Error: Failed to transmit control signal.")
            return

        
        result = response.json()
        await update.message.reply_text(f"🛠️ {result.get('message', 'Action executed.')}")
    except Exception as e:
        await update.message.reply_text("❌ Error: Failed to send control signal.")


async def predict_crash_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Queries the ML model for real-time anomally detection & crash risk analysis."""
    try:
        response = safe_api_request("GET", "/telemetry")
        if not response or response.status_code != 200:
            await update.message.reply_text("❌ Error: Telemetry service unavailable.")
            return

        data = response.json()
        anomaly = "⚠️ ANOMALY DETECTED!" if data["anomaly_detected"] else "✅ Healthy Operations"

        message = (
            f"🧠 *ML Health & Crash Risk Prediction*\n\n"
            f"• *Status:* `{anomaly}`\n"
            f"• *Crash Risk Score:* `{data['crash_risk_score']}`\n"
            f"• *CPU Load:* `{data['cpu_usage']}`\n"
            f"• *Memory:* `{data['memory_mb']}`\n"
            f"• *API Latency:* `{data['api_latency']}`\n"
            f"• *Recommendation:* `{data['recommended_action']}`\n"
        )
        await update.message.reply_text(message, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Predictive check failed: {e}")
        await update.message.reply_text("❌ Failed to analyze telemetry.")

def main():
    # Initialize the modern Telegram application
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("Performance", performance_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("bot_start", control_command))
    app.add_handler(CommandHandler("bot_stop", control_command))
    app.add_handler(CommandHandler("predict_crash", predict_crash_command))

    logger.info("Starting Telegram Bot polling...")
    app.run_polling()

if __name__ == "__main__":
    main()