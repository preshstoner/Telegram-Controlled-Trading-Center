from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import random
import math
import numpy as np
from sklearn.ensemble import IsolationForest

app = FastAPI(title="Trading Bot Control API with Crash Guard")


# --- Initialize Synthetic Machine Learning Model ---
# We train an Isolation Forest on normal operating parameters:
# Features: [CPU_Usage_%, Memory_Usage_MB, API_Latency_ms, Error_Rate_%]
normal_operating_data = np.array([
    [15, 200, 45, 0],
    [22, 220, 50, 0],
    [18, 210, 40, 1],
    [30, 250, 60, 2],
    [25, 230, 55, 0],
    [12, 190, 35, 0]
])

ml_guard_model = IsolationForest(contamination=0.1, random_state=42)
ml_guard_model.fit(normal_operating_data)

# Simulated trading bot state
bot_state = {
    "is_running": True,
    "active_pair": "BTC/USDT",
    "profit_loss_pct": 2.45,
    "total_trades": 42,
    "loss_floor": 98000.0,
    "historical_breach_recorded": False # Permanently tarcks if floor was ever crossed
}


class ControlCommand(BaseModel):
    action: str

def inspect_snapshot(equity, observed_at, now, floor, max_age):
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in (equity, floor)):
        return {"recorded": "unknown", "freshness": "invalid value"}
    if (not isinstance(observed_at, datetime) or not isinstance(now, datetime) or observed_at.utcoffset() is None or now.utcoffset() is None or max_age < timedelta(0)):
        return {"recorded": "unknown", "freshness": "invalid time"}
    age = now - observed_at
    if age < timedelta(0):
        return {"recorded": "unknown", "freshness": "future timestamp"}
    recorded = "crossing recorded" if equity <= floor else "above floor recorded"
    return {
        "recorded": recorded,
        "freshness": "fresh observation" if age <= max_age else "unknown now (stale)"
    }

@app.get("/challenge/audit")
def audit_challenge():
    """Audit challenge readiness enforcing crossing permanence and strict freshness."""
    now_utc = datetime.now(timezone.utc)

    # Simulated account state (In production, pull this from your broker/exchange API)
    simulated_equity = 99100.0 # Currently above floor
    loss_floor = bot_state["loss_floor"]

    # Simulate a fresh observation (e.g., recorded 15 seconds ago)
    observed_time = now_utc - timedelta(seconds=15)

    # Run the strict inspection logic
    result = inspect_snapshot(simulated_equity, observed_time, now_utc, loss_floor, timedelta(seconds=30))

    # Enforce Crossing Permanence: If it ever crossed, lock the historical breach flag
    if result["recorded"] == "crossing recorded":
        bot_state["historical_breach_recorded"] = True

    return {
        "equity": simulated_equity,
        "floor": loss_floor,
        "headroom": round(simulated_equity - loss_floor, 2),
        "observed_at": observed_time.isoformat(),
        "audit": result,
        "historical_breach_recorded": bot_state["historical_breach_recorded"]
    }

@app.post("/challenge/reset-breach")
def reset_breach_ledger():
    """Manual override to reset historical breach state (e.g., after starting a new challenge phase)."""
    bot_state["historical_breach_recorded"] = False
    return {"message": "Historical breach ledger rest successfully."}

@app.get("/telemetry")
def get_telemetry():
    """Generate real-time system metrics and evaluates crash likelihood via ML."""
    # Simulate current system health metrics
    cpu = round(random.uniform(10, 95), 1)
    memory = round(random.uniform(180, 850), 1)
    latency = round(random.uniform(30, 450), 1)
    error_rate = round(random.uniform(0, 15), 1)

    current_metrics = np.array([[cpu, memory, latency, error_rate]])

    # ML Prediction: 1 = Normal Operating State, -1 = High Anomally / Impending Crash Risk
    prediction = ml_guard_model.predict(current_metrics)[0]
    is_anomaly = True if prediction == -1 else False

    # Calculate risk score percentage based on severe metrics
    risk_score = min(100, int((cpu / 100 * 30) + (memory / 1000 * 30) + (latency / 500 * 20) + (error_rate / 20 * 20)))

    return {
        "cpu_usage": f"{cpu}%",
        "memory_mb": f"{memory}MB",
        "api_latency": f"{latency}ms",
        "error_rate": f"{error_rate}%",
        "crash_risk_score": f"{risk_score}%",
        "anomaly_detected": is_anomaly,
        "recommended_action": "EMERGENCY_STOP" if is_anomaly or risk_score > 75 else "CONTINUE"
    }

@app.get("/status")
def get_status():
    return {
        "status": "running" if bot_state["is_running"] else "paused",
        "pair": bot_state["active_pair"],
        "trades": bot_state["total_trades"]
    }

@app.get("/performance")
def get_performance():
    # Simulate real-time profit fluctuations for testing
    profit = round(bot_state["profit_loss_pct"] + random.uniform(-0.2, 0.2), 2)
    return {
        "profit": f"{profit}%",
        "status": "profitable" if profit >= 0 else "drawdown"
    }

@app.post("/control")
def control_bot(cmd: ControlCommand):
    action = cmd.action.lower()
    if action == "start":
        bot_state["is_running"] = True
        return {"message": "Trading bot started successfully."}
    elif action == "stop":
        bot_state["is_running"] = False
        return {"message": "Trading bot paused safely."}
    else: 
        raise HTTPException(status_code=400, detail="Invalid command action.")