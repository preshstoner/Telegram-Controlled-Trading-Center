from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
import random
import math
import numpy as np
from sklearn.ensemble import IsolationForest
from abc import ABC, abstractmethod

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



# --- Abstract Base Class (The contract) ---
class AbstractTradingAccount(ABC):
    def __init__(self, account_id, balance):
        self.account_id = account_id
        self.__balance = balance # Encapsulation combined with abstraction!

    def get_balance(self):
        """Shared concrete method available to all accounts."""
        return self.__balance

    def update_balance(self, amount):
        """Shared helper to modify provate balance safely"""
        self.__balance += amount

    @abstractmethod
    def execute_trade(self, symbol, volume, price): 
        """Mandatory: Every account type must define it's own compliance rules."""
        pass

    @abstractmethod
    def audit_risk(self):
        """Mandatory: Every account type must define it's own compliance rules."""
        pass


class TradingAccount:
    def __init__(self, account_id, initial_balance, asset_pair="BTC/USDT"):
        # Instance attributes unique to this account
        self.account_id = account_id
        self.balance = initial_balance
        self.asset_pair = asset_pair
        self.active_trades = []

    def execute_trade(self, side, amount, price):
        """Simulates executing a buy or sell trade."""
        cost = amount * price

        if side.lower() == "buy":
            if self.balance >= cost:
                self.balance -= cost
                self.active_trades.append({"side": "BUY", "amount": amount, "price": price})
                print(f"[{self.account_id}] SUCCESS: Bought {amount} {self.asset_pair} at ${price:.2f}. Remaining Balance: ${self.balance:.2f}")
            else:
                print(f"[{self.account_id}] FAILED: Insufficient funds for this buy order.")

        elif side.lower() == "sell":
            self.balance += cost
            self.active_trades.append({"side": "SELL", "amount": amount, "price": price})
            print(f"[{self.account_id}] SUCCESS: Sold {amount} {self.asset_pair} at ${price:.2f}. New Balance: ${self.balance:.2f}")


    def check_portfolio(self):
        """Displays current account state."""
        print(f"--- Account Status [{self.account_id}] ---")
        print(f"Asset Pair: {self.asset_pair}")
        print(f"Cash Balance: ${self.balance:.2f}")
        print(f"Total Executed Trades: {len(self.active_trades)}")

        
# Initializing a live trading account instance
bot_account = TradingAccount("ACC-9921", 10000.0, "BTC/USDT")

# Performing actions using class methods
bot_account.check_portfolio()
bot_account.execute_trade("buy", 0.5, 64000.0)
bot_account.check_portfolio()


@app.get("/account/status")
def get_account_status():
    return {
        "account_id": bot_account.account_id,
        "balance": bot_account.balance,
        "asset_pair": bot_account.asset_pair,
        "trades_count": len(bot_account.active_trades)
    }


class SecuredTradingAccount:
    def __init__(self, account_id, initial_balance=0.0):
        self.account_id = account_id
        self.__balance = initial_balance # Private attribute protected from direct external tampering
        self.active_trades = []

    def deposit(self, amount):
        if amount <= 0:
            return {"status": "error", "message": "Deposit amount must be greater than zero."}

        self.__balance += amount
        return {"status": "success", "new_balance": self.__balance}

    def execute_trade(self, amount, price):
        total_cost = amount * price

        # Encapsulated logic protects the balance from dropping below zero
        if total_cost > self.__balance:
            return {"status": "error", "message": "Insufficient capital for this trade size."}

        self.__balance -= total_cost
        self.active_trades.append({"amount": amount, "price": price})
        return {"status": "success", "remaining_balance": self.__balance}

    def get_balance(self):
        # Controlled access to this private balance via a getter method
        return self.__balance


# --- Parent Class (Base) ---
class BaseTradingAccount:
    def __init__(self, account_id, initial_balance, asset_pair="BTC/USDT"):
        self.account_id = account_id
        self.__balance = initial_balance # Encapsulated balance
        self.asset_pair = asset_pair
        self.active_trades = []

    def evaluate_risk(self):
        """Base method to be overridden by subclasses."""
        return f"Account {self.account_id}: Standard risk evaluation."

    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            print(f"[{self.account_id}] Deposited ${amount:.2f}. Balance: ${self.__balance:.2f}")
        return self.__balance

    def get_balance(self):
        return self.__balance

    def account_summary(self):
        return f"Account ID: {self.account_id} | Asset: {self.asset_pair} | Balance: ${self.__balance:.2f}"

# --- Child Class 1: Retail Account ---
class RetailAccount(BaseTradingAccount):
    def evaluate_risk(self):
        """Polymorphic override for retail trading."""
        return f"🟢 Retail Account [{self.account_id}]: Standard cash balance of ${self.__balance:.2f}. No strict drawdown limits."



# --- Child Class: Prop Firm Account (Single Inheritance) ---
class PropFirmAccount(BaseTradingAccount, AbstractTradingAccount):
    def __init__(self, account_id, initial_balance, challenge_phase="Phase 1", max_loss_floor=90000.0):
        # Inherit parent attributes using super()
        super().__init__(account_id, initial_balance)
        self.challenge_phase = challenge_phase
        self.max_loss_floor = max_loss_floor # Strict prop firm drawdown limit

    # Satistfying the abstract method contract for execution
    def execute_trade(self, symbol, volume, price):
        cost = volume * price
        if cost > self.get_balance():
            return f"❌ Rejected: Insufficient funds for {volume} {symbol}."
        self.update_balance(-cost)
        return f"✅ Executed buy for {volume} {symbol} at ${price}. New Balance: ${self.get_balance()}"

    # Satisfying the abstract method contract for risk auditing
    def audit_risk(self):
        balance = self.get_balance()
        if balance < self.max_loss_floor:
            return f"🚨 PROP BREACH: Account {self.account_id} balance (${balance}) is below the floor (${self.max_loss_floor})!"
        headroom = balance - self.max_loss_floor
        return f"🛡️ Prop Audit Passed: ${headroom:.2f} headroom remaining above floor."

    def evaluate_risk(self):
        """Polymorphic override with strict prop firm drawdown rules."""
        headroom = self.__balance - self.max_loss_floor
        if headroom < 0:
            return f"❌ Prop Firm [{self.account_id}]: BREACHED! Equity is below the ${self.max_loss_floor} floor."
        return f"🛡️ Prop Firm [{self.account_id}]: Safe. Headroom remaining above floor: ${headroom:.2f}"

    def audit_challenge(self, current_equity):
        """Specialized method unique to Prop Firm accounts."""
        if current_equity < self.max_loss_floor:
            return f"❌ BREACH: Account {self.account_id} dropped below floor (${self.max_loss_floor})!"
        headroom = current_equity - self.max_loss_floor
        return f"✅ PASSED AUDIT: Phase {self.challenge_phase}. Headroom remaining: ${headroom:.2f}"


    # Overriding the parent's method to include prop firm details
    def account_summary(self):
        base_info = super().account_summary()
        return f"{base_info} | Challenge: {self.challenge_phase} | Floor: ${self.max_loss_floor}"


# --- Testing Abstraction ---

# 1. Trying to instantiate the abstract base class directly throws an error:
try: 
    bad_acc = AbstractTradingAccount("FAIL-01", 1000)
except TypeError as e:
    print(f"Caught Expected Error: {e}")


    

# --- Demonstrating Polymorphism in Action ---
# Create a mixed list of different account objects
accounts = [
    RetailAccount("RET-501", 15000.0),
    PropFirmAccount("PROP-9099", 98500.0, max_loss_floor=95000.0),
    RetailAccount("RET-502", 4200.0),
]

# A single polymorphic function that loops through any account type
def audit_all_accounts(account_list):
    print("--- Running Portfolio Risk Audit ---")
    for acc in account_list:
        # We call the exact same method name (.evaluate_risk()), but Python automatically knows which class's version to run!
        print(acc.evaluate_risk())

# Run the audit 
audit_all_accounts(accounts)





# --- Testing the Classes ---
# Creating a Prop Firm account instance
prop_account = PropFirmAccount("PROP-9099", 100000.0, challenge_phase="1", max_loss_floor=95000.0)
print(prop_account.audit_risk())


# Inherited method from BaseTradingAccount
prop_account.deposit(5000.0)

# Override method from PropFirmAccount
print(prop_account.account_summary())

# Specialized method unique to Prop Firm Account
print(prop_account.audit_challenge(97500.0)) # Safe
print(prop_account.audit_challenge(94000.0)) # Breach!

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