"""
Paper-trading bot for Alpaca: five strategies side by side, each with its own $100.

  1. Bitcoin trend bot     hold BTC when its 5-day average is above its 20-day average
  2. Bitcoin buy & hold    buy BTC once and keep it
  3. S&P 500 buy & hold    buy SPY once and keep it
  4. S&P 500 trend         hold SPY when its price is above its 200-day average, else cash
  5. Mixed portfolio       60% SPY, 20% GLD (gold), 10% BTC, 10% cash, rebalanced monthly

Bitcoin trades 24/7. Stocks (SPY, GLD) only trade when the US market is open
(weekdays 6:30am-1pm Pacific), so those strategies wait until then.

Each run (GitHub Actions calls it every 30 minutes) updates:
  REPORT.md    scoreboard you can read in the GitHub app
  state.json   the bot's memory
  trades.csv   every trade
  history.csv  each strategy's value, once a day
"""
import csv
import datetime as dt
import json
import math
import os
import time

import requests

START_BUDGET = 100.0
CRYPTO_FEE = 0.0025  # Alpaca crypto fee estimate; stocks have no commission

STRATEGIES = {
    "btc_trend": {"name": "Bitcoin trend bot (5/20 day)", "type": "trend", "symbol": "BTC/USD", "fast": 5, "slow": 20},
    "btc_hold":  {"name": "Bitcoin buy & hold", "type": "hold", "symbol": "BTC/USD"},
    "spy_hold":  {"name": "S&P 500 buy & hold", "type": "hold", "symbol": "SPY"},
    "spy_trend": {"name": "S&P 500 trend (200 day)", "type": "trend", "symbol": "SPY", "fast": 1, "slow": 200},
    "mix":       {"name": "Mix 60% stocks / 20% gold / 10% BTC / 10% cash", "type": "mix",
                  "weights": {"SPY": 0.60, "GLD": 0.20, "BTC/USD": 0.10}},
}

KEY = os.environ["ALPACA_KEY"]
SECRET = os.environ["ALPACA_SECRET"]
TRADE_URL = "https://paper-api.alpaca.markets"  # paper account only, never real money
DATA_URL = "https://data.alpaca.markets"
HEADERS = {"APCA-API-KEY-ID": KEY, "APCA-API-SECRET-KEY": SECRET}
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.strftime("%Y-%m-%d")


class TradeError(Exception):
    pass


def api(method, url, **kw):
    r = requests.request(method, url, headers=HEADERS, timeout=30, **kw)
    if r.status_code >= 400:
        raise TradeError(f"Alpaca {r.status_code}: {r.text[:300]}")
    return r.json()


def is_crypto(sym):
    return "/" in sym


# ---------- prices ----------
_closes, _latest = {}, {}


def closes(sym, days):
    """Finished daily closing prices, oldest first."""
    if sym in _closes and len(_closes[sym]) >= days:
        return _closes[sym]
    back = int(days * (1.0 if is_crypto(sym) else 1.6)) + 15
    start = (NOW - dt.timedelta(days=back)).strftime("%Y-%m-%dT00:00:00Z")
    if is_crypto(sym):
        data = api("GET", f"{DATA_URL}/v1beta3/crypto/us/bars",
                   params={"symbols": sym, "timeframe": "1Day", "start": start, "limit": 10000})
    else:
        data = api("GET", f"{DATA_URL}/v2/stocks/bars",
                   params={"symbols": sym, "timeframe": "1Day", "start": start, "limit": 10000,
                           "feed": "iex", "adjustment": "all"})
    bars = (data.get("bars") or {}).get(sym, [])
    _closes[sym] = [b["c"] for b in bars if not b["t"].startswith(TODAY)]
    return _closes[sym]


def latest(sym):
    if sym not in _latest:
        if is_crypto(sym):
            d = api("GET", f"{DATA_URL}/v1beta3/crypto/us/latest/trades", params={"symbols": sym})
        else:
            d = api("GET", f"{DATA_URL}/v2/stocks/trades/latest", params={"symbols": sym, "feed": "iex"})
        _latest[sym] = float(d["trades"][sym]["p"])
    return _latest[sym]


MARKET_OPEN = None


def can_trade(sym):
    global MARKET_OPEN
    if is_crypto(sym):
        return True
    if MARKET_OPEN is None:
        MARKET_OPEN = bool(api("GET", f"{TRADE_URL}/v2/clock")["is_open"])
    return MARKET_OPEN


# ---------- orders ----------
def floor9(x):
    return math.floor(x * 1e9) / 1e9


def wait_for_fill(order_id):
    for _ in range(20):
        o = api("GET", f"{TRADE_URL}/v2/orders/{order_id}")
        if o["status"] == "filled":
            return float(o["filled_qty"]), float(o["filled_avg_price"])
        if o["status"] in ("canceled", "expired", "rejected"):
            raise TradeError(f"order {o['status']}")
        time.sleep(3)
    try:
        api("DELETE", f"{TRADE_URL}/v2/orders/{order_id}")
    except TradeError:
        pass
    raise TradeError("order did not fill in time; canceled, will retry next run")


def buy(key, s, sym, dollars):
    dollars = math.floor(min(dollars, s["cash"]) * 100) / 100
    if dollars < 1:
        return
    o = api("POST", f"{TRADE_URL}/v2/orders", json={
        "symbol": sym, "notional": f"{dollars:.2f}", "side": "buy", "type": "market",
        "time_in_force": "gtc" if is_crypto(sym) else "day"})
    qty, price = wait_for_fill(o["id"])
    s["cash"] = round(s["cash"] - qty * price, 2)
    if is_crypto(sym):
        qty *= 1 - CRYPTO_FEE  # the fee comes out of the coins received
    s["pos"][sym] = s["pos"].get(sym, 0.0) + qty
    s["trades"] += 1
    log_trade(key, "BUY", sym, qty, price, s["cash"])


def sell(key, s, sym, qty):
    qty = floor9(min(qty, s["pos"].get(sym, 0.0)))
    if qty <= 0 or qty * latest(sym) < 1:
        return
    o = api("POST", f"{TRADE_URL}/v2/orders", json={
        "symbol": sym, "qty": f"{qty:.9f}", "side": "sell", "type": "market",
        "time_in_force": "gtc" if is_crypto(sym) else "day"})
    fq, price = wait_for_fill(o["id"])
    s["cash"] = round(s["cash"] + fq * price * ((1 - CRYPTO_FEE) if is_crypto(sym) else 1), 2)
    s["pos"][sym] = max(0.0, s["pos"].get(sym, 0.0) - fq)
    s["trades"] += 1
    log_trade(key, "SELL", sym, fq, price, s["cash"])


def log_trade(key, side, sym, qty, price, cash_after):
    path = "trades.csv"
    if os.path.exists(path):
        with open(path) as f:
            if "strategy" not in f.readline():
                os.replace(path, "trades_old.csv")  # file from the first version of the bot
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "strategy", "side", "symbol", "qty", "price", "strategy_cash_after"])
        w.writerow([NOW.strftime("%Y-%m-%d %H:%M"), STRATEGIES[key]["name"], side, sym,
                    f"{qty:.8f}", f"{price:.2f}", f"{cash_after:.2f}"])


# ---------- strategies ----------
def value(s):
    return s["cash"] + sum(q * latest(sym) for sym, q in s["pos"].items() if q > 0)


def run_hold(key, cfg, s):
    sym = cfg["symbol"]
    if s["pos"].get(sym, 0) == 0 and can_trade(sym):
        buy(key, s, sym, s["cash"] * 0.995)
    return "holding" if s["pos"].get(sym, 0) > 0 else "waiting for market open"


def run_trend(key, cfg, s):
    sym, fast, slow = cfg["symbol"], cfg["fast"], cfg["slow"]
    c = closes(sym, slow)
    if len(c) < slow:
        return f"not enough price history ({len(c)}/{slow} days)"
    fast_avg = sum(c[-fast:]) / fast
    slow_avg = sum(c[-slow:]) / slow
    want = fast_avg > slow_avg
    held = s["pos"].get(sym, 0) > 0
    if can_trade(sym):
        if want and not held:
            buy(key, s, sym, s["cash"] * 0.995)
        elif not want and held:
            sell(key, s, sym, s["pos"][sym])
    signal = "in the market" if want else "in cash"
    return f"signal: {signal} ({'price' if fast == 1 else f'{fast}d avg'} ${fast_avg:,.2f} vs {slow}d avg ${slow_avg:,.2f})"


def run_mix(key, cfg, s):
    month = TODAY[:7]
    if s.get("last_rebalance") == month:
        return f"rebalanced {s['last_rebalance']}, next rebalance next month"
    if not can_trade("SPY"):
        return "waiting for market open to rebalance"
    total = value(s)
    targets = {sym: total * w for sym, w in cfg["weights"].items()}
    current = {sym: s["pos"].get(sym, 0.0) * latest(sym) for sym in targets}
    for sym in targets:  # sells first, to free up cash
        if current[sym] - targets[sym] >= 1:
            sell(key, s, sym, (current[sym] - targets[sym]) / latest(sym))
    for sym in targets:
        if targets[sym] - current[sym] >= 1:
            buy(key, s, sym, (targets[sym] - current[sym]) * 0.995)
    s["last_rebalance"] = month
    return f"rebalanced {month}"


RUNNERS = {"hold": run_hold, "trend": run_trend, "mix": run_mix}


# ---------- state & reports ----------
def load_state():
    state = {}
    if os.path.exists("state.json"):
        with open("state.json") as f:
            state = json.load(f)
    if "strategies" not in state:  # upgrade from the first, Bitcoin-only version
        old = state
        state = {"started": old.get("last_check_utc", NOW.strftime("%Y-%m-%d %H:%M"))[:10], "strategies": {}}
        if "cash" in old:
            state["strategies"]["btc_trend"] = {
                "cash": old["cash"], "pos": {"BTC/USD": old.get("btc", 0.0)},
                "trades": 1 if old.get("btc", 0) else 0}
    for key in STRATEGIES:
        state["strategies"].setdefault(key, {"cash": START_BUDGET, "pos": {}, "trades": 0})
    return state


def write_reports(state, notes):
    rows, values = [], {}
    for key, cfg in STRATEGIES.items():
        s = state["strategies"][key]
        v = value(s)
        values[key] = v
        holding = ", ".join(f"{sym} ${q * latest(sym):,.2f}" for sym, q in s["pos"].items() if q * latest(sym) >= 0.01)
        holding = (holding + ", " if holding else "") + f"cash ${s['cash']:,.2f}"
        rows.append((cfg["name"], v, s["trades"], holding, notes[key]))
    rows.sort(key=lambda r: -r[1])
    lines = [
        "# Paper trading scoreboard",
        "",
        f"Each strategy started with **${START_BUDGET:.0f}** of paper money on {state['started']}.",
        f"Last update: {NOW.strftime('%b %d, %Y %H:%M')} UTC · Bitcoin ${latest('BTC/USD'):,.2f} · "
        f"US stock market {'open' if can_trade('SPY') else 'closed'}",
        "",
        "| Rank | Strategy | Worth now | Profit | Trades |",
        "|---|---|---:|---:|---:|",
    ]
    for i, (name, v, t, _, _) in enumerate(rows, 1):
        p = v - START_BUDGET
        lines.append(f"| {i} | {name} | ${v:,.2f} | {'+' if p >= 0 else '-'}${abs(p):,.2f} ({p / START_BUDGET:+.1%}) | {t} |")
    total = sum(values.values())
    lines += ["", f"**All five together:** ${total:,.2f} from ${START_BUDGET * len(STRATEGIES):,.0f} "
                  f"({total - START_BUDGET * len(STRATEGIES):+,.2f})", "", "## What each one is doing", ""]
    for name, _, _, holding, note in rows:
        lines.append(f"- **{name}:** {holding}. {note[:1].upper() + note[1:]}.")
    lines += ["", "Paper money only. Past or paper results do not predict real results.", ""]
    with open("REPORT.md", "w") as f:
        f.write("\n".join(lines))

    # one row per day in history.csv
    keys = list(STRATEGIES)
    exists = os.path.exists("history.csv")
    if exists:
        with open("history.csv") as f:
            last = f.read().strip().splitlines()[-1]
        if last.startswith(TODAY):
            return values
    with open("history.csv", "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["date"] + keys)
        w.writerow([TODAY] + [f"{values[k]:.2f}" for k in keys])
    return values


def main():
    state = load_state()
    notes = {}
    for key, cfg in STRATEGIES.items():
        try:
            notes[key] = RUNNERS[cfg["type"]](key, cfg, state["strategies"][key])
        except TradeError as e:
            notes[key] = f"problem this run: {e}"
        print(f"{cfg['name']}: {notes[key]}")
    state["last_check_utc"] = NOW.strftime("%Y-%m-%d %H:%M")
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    values = write_reports(state, notes)
    print("\n" + "\n".join(f"{STRATEGIES[k]['name']}: ${v:,.2f} ({v - START_BUDGET:+.2f})" for k, v in values.items()))


if __name__ == "__main__":
    main()
