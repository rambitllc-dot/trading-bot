"""
$100 paper-trading bot for Alpaca.

Strategy (same as the Strategy Lab's bot replay):
  - Look at Bitcoin's daily closing prices.
  - If the 5-day average is above the 20-day average -> hold Bitcoin.
  - Otherwise -> hold cash.
It only ever uses its own $100 budget, no matter how much is in the account.

Runs once per call (GitHub Actions calls it every 30 minutes) and keeps its
memory in state.json and a trade history in trades.csv.
"""
import csv
import datetime as dt
import json
import os
import sys
import time

import requests

# ---- settings you can change ----
SYMBOL = "BTC/USD"
FAST_DAYS = 5
SLOW_DAYS = 20
START_BUDGET = 100.0
# ---------------------------------

KEY = os.environ["ALPACA_KEY"]
SECRET = os.environ["ALPACA_SECRET"]
TRADE_URL = "https://paper-api.alpaca.markets"  # paper account only, never real money
DATA_URL = "https://data.alpaca.markets"
HEADERS = {"APCA-API-KEY-ID": KEY, "APCA-API-SECRET-KEY": SECRET}
STATE_FILE = "state.json"
TRADES_FILE = "trades.csv"


def api(method, url, **kw):
    r = requests.request(method, url, headers=HEADERS, timeout=30, **kw)
    if r.status_code >= 400 and r.status_code != 404:
        print(f"Alpaca error {r.status_code}: {r.text}")
        r.raise_for_status()
    return r


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def log_trade(side, qty, price, cash_after):
    new = not os.path.exists(TRADES_FILE)
    with open(TRADES_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "side", "btc_qty", "price", "bot_cash_after"])
        w.writerow([dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M"), side,
                    f"{qty:.8f}", f"{price:.2f}", f"{cash_after:.2f}"])


def daily_closes():
    start = (dt.datetime.utcnow() - dt.timedelta(days=SLOW_DAYS + 10)).strftime("%Y-%m-%dT00:00:00Z")
    r = api("GET", f"{DATA_URL}/v1beta3/crypto/us/bars",
            params={"symbols": SYMBOL, "timeframe": "1Day", "start": start, "limit": 1000})
    bars = r.json().get("bars", {}).get(SYMBOL, [])
    today = dt.datetime.utcnow().strftime("%Y-%m-%d")
    closed = [b for b in bars if not b["t"].startswith(today)]  # only finished days
    return [b["c"] for b in closed], bars[-1]["c"] if bars else None


def wait_for_fill(order_id):
    for _ in range(20):
        o = api("GET", f"{TRADE_URL}/v2/orders/{order_id}").json()
        if o["status"] == "filled":
            return float(o["filled_qty"]), float(o["filled_avg_price"])
        if o["status"] in ("canceled", "expired", "rejected"):
            sys.exit(f"Order {o['status']}: {o}")
        time.sleep(3)
    sys.exit("Order did not fill in time; will check again next run.")


def main():
    state = load_state()
    state.setdefault("cash", START_BUDGET)
    state.setdefault("btc", 0.0)

    closes, last_price = daily_closes()
    if len(closes) < SLOW_DAYS:
        sys.exit(f"Only {len(closes)} days of prices, need {SLOW_DAYS}.")
    fast = sum(closes[-FAST_DAYS:]) / FAST_DAYS
    slow = sum(closes[-SLOW_DAYS:]) / SLOW_DAYS
    want_btc = fast > slow

    action = "hold"
    if want_btc and state["btc"] == 0 and state["cash"] >= 1:
        notional = round(state["cash"] * 0.995, 2)  # leave room for the fee
        o = api("POST", f"{TRADE_URL}/v2/orders", json={
            "symbol": SYMBOL, "notional": str(notional), "side": "buy",
            "type": "market", "time_in_force": "gtc"}).json()
        qty, price = wait_for_fill(o["id"])
        state["cash"] = round(state["cash"] - qty * price, 2)
        # Alpaca takes crypto fees out of the coins received, so read what we really hold
        pos = api("GET", f"{TRADE_URL}/v2/positions/{SYMBOL.replace('/', '')}")
        state["btc"] = float(pos.json()["qty"]) if pos.status_code == 200 else qty
        log_trade("BUY", qty, price, state["cash"])
        action = f"BOUGHT {qty:.6f} BTC at ${price:,.2f}"
    elif not want_btc and state["btc"] > 0:
        # close the whole Bitcoin position (only this bot buys Bitcoin in the account)
        o = api("DELETE", f"{TRADE_URL}/v2/positions/{SYMBOL.replace('/', '')}").json()
        qty, price = wait_for_fill(o["id"])
        state["cash"] = round(state["cash"] + qty * price * 0.9975, 2)  # minus the sell fee
        state["btc"] = 0.0
        log_trade("SELL", qty, price, state["cash"])
        action = f"SOLD {qty:.6f} BTC at ${price:,.2f}"

    value = state["cash"] + state["btc"] * (last_price or 0)
    state.update({
        "last_check_utc": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        "btc_price": round(last_price or 0, 2),
        "avg_5_day": round(fast, 2),
        "avg_20_day": round(slow, 2),
        "signal": "hold bitcoin" if want_btc else "hold cash",
        "bot_value": round(value, 2),
        "profit": round(value - START_BUDGET, 2),
    })
    save_state(state)
    print(f"BTC ${last_price:,.2f} | 5d avg ${fast:,.2f} | 20d avg ${slow:,.2f} | {action} | "
          f"bot worth ${value:,.2f} ({value - START_BUDGET:+.2f})")


if __name__ == "__main__":
    main()
