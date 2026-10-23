# Telegram-Controlled Trading Operations Center 🤖📈

A robust, asynchronous operations center for managing trading bots remotely. This project bridges a **FastAPI** simulation and control backend with a **`python-telegram-bot`** frontend, fortified with **Machine Learning (Isolation Forest)** anomaly detection for predictive crash protection and resilient HTTP error handling.

---

## 🚀 Key Features

- **Remote Telegram Command Center:** Monitor and control your trading bots from anywhere via intuitive Telegram chat commands.
- **ML-Based Crash Guard:** Utilizes `scikit-learn`'s **Isolation Forest** to evaluate real-time system telemetry (CPU usage, memory footprint, network latency, and error rates) to calculate crash risk scores before failures happen.
- **Rate-Limit Resilience:** Features a custom request wrapper with exponential backoff and `Retry-After` header parsing to safely handle HTTP 429 ("Too Many Requests") errors.
- **Secure Configuration:** Environment-based credential and host management using `python-dotenv`.

---

## 📂 Project Structure

```text
Telegram-Controlled-Trading-Operations-Center/
├── api.py          # FastAPI backend engine, trading simulation, & ML telemetry
├── bot.py          # Telegram bot frontend & resilient command handlers
├── .env            # Environment credentials (API tokens & endpoints)
└── README.md       # Project documentation


⚙️ Installation & Setup
1. Clone or Open Your Project Directory
Ensure you are in your project root directory in your terminal.

2. Install Dependencies
Install all required libraries for FastAPI, Uvicorn, Telegram, and Machine Learning:

PowerShell
pip install fastapi uvicorn python-telegram-bot requests scikit-learn numpy python-dotenv
3. Configure Your .env File
Create a .env file in the root directory of your project and add your BotFather token:

Code snippet
TELEGRAM_TOKEN=your_telegram_bot_token_here
API_BASE_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)
🚀 Running the Application
To run the system locally, you will need two separate terminal windows:

Terminal 1: Start the FastAPI Backend Engine
PowerShell
python -m uvicorn api:app --reload
Terminal 2: Start the Telegram Bot Frontend
PowerShell
python bot.py
💬 Telegram Command Reference
Open your registered bot in Telegram and use the following commands:

/start – Initializes connection and displays the welcome menu.

/status – Checks overall operational state, active trading pairs, and total executed trades.

/performance – Pulls real-time profit/loss metrics via rate-limit resilient HTTP requests.

/predict_crash – Triggers the live Machine Learning anomaly check on system metrics and returns a risk score recommendation.

🗺️ Roadmap & Future Enhancements
[x] FastAPI trading control & telemetry routes

[x] Modern python-telegram-bot asynchronous command handlers

[x] HTTP 429 rate-limit backoff wrapper

[x] Scikit-Learn Isolation Forest predictive crash guard

[ ] Automated background alerting for critical risk thresholds
