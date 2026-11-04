"""
Paper-trading bot for Alpaca: many strategies side by side, each with its own $100.

  1. Bitcoin trend bot     hold BTC when its 5-day average is above its 20-day average
  2. Bitcoin buy & hold    buy BTC once and keep it
  3. S&P 500 buy & hold    buy SPY once and keep it
  4. S&P 500 trend         hold SPY when its price is above its 200-day average, else cash
  5. Mixed portfolio       60% SPY, 20% GLD (gold), 10% BTC, 10% cash, rebalanced monthly
  6. Momentum rotation     each month, hold whichever of SPY / QQQ (tech) / GLD (gold) / BND (bonds)
                           rose most over the past 12 months; cash if all of them fell
  7. RSI dip-buying        buy SPY after a sharp 2-day drop (RSI-2 below 10) while it is above its
                           200-day average; sell once it closes back above its 5-day average
  8. Wide momentum         same as 6, picking from 10 ETFs: US large (SPY), tech (QQQ), small
                           companies (IWM), international (VXUS), energy (XLE), healthcare (XLV),
                           banks (XLF), real estate (VNQ), gold (GLD), bonds (BND)
  9+ Stocks                Apple, Microsoft, Nvidia, Amazon, Tesla: each one twice, once
                           buy & hold and once with the 200-day trend rule

Bitcoin trades 24/7. Stocks and ETFs (SPY, QQQ, GLD, BND) only trade when the US market is open
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
CRYPTO_MIN = 10.0    # Alpaca's smallest crypto order, in dollars

STRATEGIES = {
    "btc_trend": {"name": "Bitcoin trend bot (5/20 day)", "type": "trend", "symbol": "BTC/USD", "fast": 5, "slow": 20},
    "btc_hold":  {"name": "Bitcoin buy & hold", "type": "hold", "symbol": "BTC/USD"},
    "spy_hold":  {"name": "S&P 500 buy & hold", "type": "hold", "symbol": "SPY"},
    "spy_trend": {"name": "S&P 500 trend (200 day)", "type": "trend", "symbol": "SPY", "fast": 1, "slow": 200},
    "mix":       {"name": "Mix 60% stocks / 20% gold / 10% BTC / 10% cash", "type": "mix",
                  "weights": {"SPY": 0.60, "GLD": 0.20, "BTC/USD": 0.10}},
    "momentum":  {"name": "Momentum rotation (SPY/QQQ/GLD/BND)", "type": "momentum",
                  "symbols": ["SPY", "QQQ", "GLD", "BND"], "lookback": 252},
    "rsi_dip":   {"name": "RSI dip-buying (S&P 500)", "type": "rsi", "symbol": "SPY"},
    "momentum_wide": {"name": "Wide momentum (10 ETFs)", "type": "momentum",
                      "symbols": ["SPY", "QQQ", "IWM", "VXUS", "XLE", "XLV", "XLF", "VNQ", "GLD", "BND"],
                      "lookback": 252},
}

# Hold vs trade pairs: each stock gets a buy & hold and a 200-day trend version.
# Change this list to test other companies (use their ticker symbols).
STOCKS = {"AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "AMZN": "Amazon", "TSLA": "Tesla",
          "SPCX": "SpaceX", "ANT": "Anthropic"}
# SpaceX only started trading on June 12, 2026, so it doesn't have 200 days of history yet;
# its trend rule uses a 50-day average instead.
TREND_DAYS = {"SPCX": 50, "ANT": 50}
# Companies that have filed to go public but may not be trading yet. Their strategies wait until
# Alpaca lists the stock under that exact company name (so the bot can't buy a different company
# that happens to use the same ticker).
PENDING_IPO = {"ANT": "Anthropic"}
for _sym, _name in STOCKS.items():
    _days = TREND_DAYS.get(_sym, 200)
    STRATEGIES[f"{_sym.lower()}_hold"] = {"name": f"{_name} buy & hold", "type": "hold", "symbol": _sym}
    STRATEGIES[f"{_sym.lower()}_trend"] = {"name": f"{_name} trend ({_days} day)", "type": "trend",
                                           "symbol": _sym, "fast": 1, "slow": _days}

# rows for the "hold vs trade" table: (asset, hold key, trading key)
# Whole-market strategies: scan all S&P 500 stocks with one rule, and an equal-weight yardstick.
STRATEGIES["sp500_momentum"] = {"name": "Stock momentum (top 10 of the S&P 500)", "type": "stock_momentum",
                                "top": 10}
STRATEGIES["rsp_hold"] = {"name": "S&P 500 equal weight (RSP) buy & hold", "type": "hold", "symbol": "RSP"}
STRATEGIES["spcx_gradual"] = {"name": "SpaceX gradual buy ($25 a week for 4 weeks)", "type": "gradual",
                              "symbol": "SPCX", "per_buy": 25.0, "buys": 4, "every_days": 7}
STRATEGIES["ant_gradual"] = {"name": "Anthropic gradual buy ($25 a week for 4 weeks)", "type": "gradual",
                             "symbol": "ANT", "per_buy": 25.0, "buys": 4, "every_days": 7}
SP500_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"

PAIRS = [("Bitcoin", "btc_hold", "btc_trend"), ("S&P 500", "spy_hold", "spy_trend")] + \
        [(n, f"{s.lower()}_hold", f"{s.lower()}_trend") for s, n in STOCKS.items()]

KEY = os.environ["ALPACA_KEY"]
SECRET = os.environ["ALPACA_SECRET"]
DATA_URL = "https://data.alpaca.markets"
HEADERS = {"APCA-API-KEY-ID": KEY, "APCA-API-SECRET-KEY": SECRET}  # paper keys, also used for price data
PAPER = {"live": False, "url": "https://paper-api.alpaca.markets", "headers": HEADERS,
         "trades_file": "trades.csv"}
ACCT = PAPER  # which account orders go to; switched to the live account only inside run_live()
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.strftime("%Y-%m-%d")


class TradeError(Exception):
    pass


def api(method, url, **kw):
    headers = ACCT["headers"] if url.startswith(ACCT["url"]) else HEADERS
    r = requests.request(method, url, headers=headers, timeout=30, **kw)
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
        MARKET_OPEN = bool(api("GET", f"{ACCT['url']}/v2/clock")["is_open"])
    return MARKET_OPEN


# ---------- orders ----------
def floor9(x):
    return math.floor(x * 1e9) / 1e9


def wait_for_fill(order_id):
    for _ in range(20):
        o = api("GET", f"{ACCT['url']}/v2/orders/{order_id}")
        if o["status"] == "filled":
            return float(o["filled_qty"]), float(o["filled_avg_price"])
        if o["status"] in ("canceled", "expired", "rejected"):
            raise TradeError(f"order {o['status']}")
        time.sleep(3)
    try:
        api("DELETE", f"{ACCT['url']}/v2/orders/{order_id}")
    except TradeError:
        pass
    raise TradeError("order did not fill in time; canceled, will retry next run")


def buy(key, s, sym, dollars):
    dollars = math.floor(min(dollars, s["cash"]) * 100) / 100
    if is_crypto(sym) and dollars < CRYPTO_MIN:
        if dollars < CRYPTO_MIN * 0.9 or s["cash"] < CRYPTO_MIN:
            return  # too small for a crypto order; skip
        dollars = CRYPTO_MIN  # round a near-$10 order up to the minimum
    if dollars < 1:
        return
    o = api("POST", f"{ACCT['url']}/v2/orders", json={
        "symbol": sym, "notional": f"{dollars:.2f}", "side": "buy", "type": "market",
        "time_in_force": "gtc" if is_crypto(sym) else "day"})
    qty, price = wait_for_fill(o["id"])
    s["cash"] = round(s["cash"] - qty * price, 2)
    if is_crypto(sym):
        qty *= 1 - CRYPTO_FEE  # the fee comes out of the coins received
    s["pos"][sym] = s["pos"].get(sym, 0.0) + qty
    s["trades"] += 1
    s.setdefault("bought_on", {})[sym] = TODAY
    log_trade(key, "BUY", sym, qty, price, s["cash"])


def sell(key, s, sym, qty, urgent=False):
    qty = floor9(min(qty, s["pos"].get(sym, 0.0)))
    if qty <= 0 or qty * latest(sym) < (CRYPTO_MIN if is_crypto(sym) else 1):
        return
    if ACCT["live"] and not urgent and not is_crypto(sym) and s.get("bought_on", {}).get(sym) == TODAY:
        # US "pattern day trader" rule: small accounts can't buy and sell the same stock the same day
        # more than 3 times a week, so the live bot simply waits until tomorrow.
        raise TradeError(f"bought {sym} today; will sell tomorrow (avoids the day-trading rule)")
    o = api("POST", f"{ACCT['url']}/v2/orders", json={
        "symbol": sym, "qty": f"{qty:.9f}", "side": "sell", "type": "market",
        "time_in_force": "gtc" if is_crypto(sym) else "day"})
    fq, price = wait_for_fill(o["id"])
    s["cash"] = round(s["cash"] + fq * price * ((1 - CRYPTO_FEE) if is_crypto(sym) else 1), 2)
    s["pos"][sym] = max(0.0, s["pos"].get(sym, 0.0) - fq)
    s["trades"] += 1
    log_trade(key, "SELL", sym, fq, price, s["cash"])


LIVE_TRADE_ALERTS = []


def log_trade(key, side, sym, qty, price, cash_after):
    path = ACCT["trades_file"]
    if ACCT["live"]:
        LIVE_TRADE_ALERTS.append((f"Live trade: {side} {sym} ${qty * price:,.2f}",
                                  f"{STRATEGIES[key]['name']} {side.lower()} {qty:.6f} {sym} at ${price:,.2f} "
                                  f"with real money. Strategy cash after: ${cash_after:,.2f}."))
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


def run_momentum(key, cfg, s):
    month = TODAY[:7]
    held = [sym for sym, q in s["pos"].items() if q > 0]
    if s.get("last_rebalance") == month:
        return f"holding {held[0] if held else 'cash'} until next month's check"
    if not can_trade("SPY"):
        return "waiting for market open for the monthly check"
    n = cfg["lookback"]
    returns = {}
    for sym in cfg["symbols"]:
        c = closes(sym, n + 1)
        if len(c) > n:
            returns[sym] = c[-1] / c[-n - 1] - 1
    if not returns:
        return "not enough price history"
    best = max(returns, key=returns.get)
    target = best if returns[best] > 0 else None
    for sym in held:
        if sym != target:
            sell(key, s, sym, s["pos"][sym])
    if target and s["pos"].get(target, 0) == 0:
        buy(key, s, target, s["cash"] * 0.995)
    s["last_rebalance"] = month
    ranks = ", ".join(f"{k} {v:+.0%}" for k, v in sorted(returns.items(), key=lambda kv: -kv[1]))
    return f"picked {target or 'cash'} for {month} (12-month returns: {ranks})"


def rsi(c, period=2):
    """Wilder's RSI on daily closes."""
    gains = losses = 0.0
    for i in range(1, period + 1):
        ch = c[i] - c[i - 1]
        gains += max(ch, 0); losses += max(-ch, 0)
    ag, al = gains / period, losses / period
    for i in range(period + 1, len(c)):
        ch = c[i] - c[i - 1]
        ag = (ag * (period - 1) + max(ch, 0)) / period
        al = (al * (period - 1) + max(-ch, 0)) / period
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def run_rsi(key, cfg, s):
    sym = cfg["symbol"]
    c = closes(sym, 200)
    if len(c) < 200:
        return f"not enough price history ({len(c)}/200 days)"
    r = rsi(c[-60:])
    avg200, avg5, last = sum(c[-200:]) / 200, sum(c[-5:]) / 5, c[-1]
    held = s["pos"].get(sym, 0) > 0
    if can_trade(sym):
        if not held and r < 10 and last > avg200:
            buy(key, s, sym, s["cash"] * 0.995)
        elif held and last > avg5:
            sell(key, s, sym, s["pos"][sym])
    state_txt = "holding, waiting for a bounce above the 5-day average" if s["pos"].get(sym, 0) > 0 else "in cash, waiting for a dip"
    return f"{state_txt} (RSI-2 {r:.0f}, buys below 10)"


# =====================================================================
# 15-minute Bitcoin up/down betting test (paper only, no orders placed)
# =====================================================================
# Same bet as the "AI bot doubled $100" videos: guess whether the next
# 15-minute Bitcoin candle closes higher or lower. A win pays 0.8x the
# stake, a loss costs the whole stake, so you need 55.6% wins to break even.
# Each signal gets its own $100 and bets 5% of whatever it has left.
# The first run scores the last 30 days of real candles (a backtest);
# after that every new candle is scored as it finishes (a live test).
BET_PAYOUT = 0.80
BET_FRACTION = 0.05
BREAK_EVEN = 1 / (1 + BET_PAYOUT)
BET_SIGNALS = {
    "coin":     "Coin flip (luck benchmark)",
    "momentum": "Momentum: bet the last candle repeats",
    "reversal": "Reversal: bet against unusually big moves",
    "trend":    "Trend: bet with the 1-hour trend when the last candle agrees",
    "session":  "Session momentum: follow the busiest hour's direction",
    "learning": "Learning: copies whichever method has been winning lately",
}
BET_LABELS = {k: "Static (one fixed method)" for k in BET_SIGNALS}
BET_LABELS["coin"] = "Luck benchmark"
BET_LABELS["learning"] = "Learning (switches methods)"
FIXED_METHODS = ["momentum", "reversal", "trend", "session"]
LEARN_WINDOW = 96      # look back 24 hours of candles
LEARN_MIN_BETS = 20    # a method needs at least this many recent bets to be trusted


def candles_15m(since):
    out, token = [], None
    while True:
        params = {"symbols": "BTC/USD", "timeframe": "15Min", "start": since, "limit": 10000}
        if token:
            params["page_token"] = token
        d = api("GET", f"{DATA_URL}/v1beta3/crypto/us/bars", params=params)
        out += (d.get("bars") or {}).get("BTC/USD", [])
        token = d.get("next_page_token")
        if not token:
            return out


def bet_signal(name, c, i):
    """Return +1 (up), -1 (down) or 0 (skip) for candle i, using only candles before it."""
    prev = c[i - 1]
    move = prev["c"] - prev["o"]
    if name == "coin":
        import hashlib
        return 1 if int(hashlib.md5(c[i]["t"].encode()).hexdigest(), 16) % 2 else -1
    if move == 0:
        return 0
    if name == "momentum":
        return 1 if move > 0 else -1
    if name == "reversal":
        avg = sum(abs(x["c"] - x["o"]) for x in c[i - 21:i - 1]) / 20
        return (-1 if move > 0 else 1) if avg and abs(move) > 2 * avg else 0
    if name == "trend":
        hour_avg = sum(x["c"] for x in c[i - 4:i]) / 4
        trend = 1 if prev["c"] > hour_avg else -1
        return trend if (move > 0) == (trend > 0) else 0
    if name == "session":
        # busiest 1-hour block in the last 24h (volume as a stand-in for market open)
        day = c[i - 96:i]
        blocks = [day[k:k + 4] for k in range(0, 96, 4)]
        top = max(blocks, key=lambda b: sum(x.get("v", 0) for x in b))
        d = top[-1]["c"] - top[0]["o"]
        return 0 if d == 0 else (1 if d > 0 else -1)
    return 0


def learning_pick(dec, ups, i):
    """Pick the fixed method with the best win rate over the last 24h of candles
    (only candles before i), if it beats break-even; otherwise skip."""
    best, best_rate = None, BREAK_EVEN
    for k in FIXED_METHODS:
        n = w = 0
        for j in range(max(0, i - LEARN_WINDOW), i):
            side = dec[k].get(j, 0)
            if side and ups.get(j) is not None:
                n += 1
                w += (side > 0) == ups[j]
        if n >= LEARN_MIN_BETS and w / n > best_rate:
            best, best_rate = k, w / n
    return dec[best].get(i, 0) if best else 0


def run_betting(state):
    b = state.setdefault("bets", {})
    b.setdefault("live_from", NOW.strftime("%Y-%m-%dT%H:%M:%SZ"))
    if "learning" not in b.get("signals", {}):
        # new method added: redo the whole test so every method is scored on the same candles
        b["signals"], b["last_t"] = {}, None
    sigs = b.setdefault("signals", {})
    for k in BET_SIGNALS:
        s = sigs.setdefault(k, {"bank": START_BUDGET, "peak": START_BUDGET, "mdd": 0.0,
                                "n": 0, "w": 0, "live_n": 0, "live_w": 0})
        # the live test gets its own fresh $100, separate from the 30-day backtest
        s.setdefault("live_bank", START_BUDGET)
        s.setdefault("live_peak", START_BUDGET)
        s.setdefault("live_mdd", 0.0)
    last = b.get("last_t")
    since = (NOW - dt.timedelta(days=32 if not last else 4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    c = candles_15m(since)
    done_before = NOW - dt.timedelta(minutes=15)
    # each fixed method's bet on every candle, and which candles went up (flat = no result)
    dec = {k: {} for k in FIXED_METHODS}
    ups = {}
    for i in range(97, len(c)):
        for k in FIXED_METHODS:
            dec[k][i] = bet_signal(k, c, i)
        if c[i]["c"] != c[i]["o"]:
            ups[i] = c[i]["c"] > c[i]["o"]
    scored = 0
    first = 97 + LEARN_WINDOW  # leave a day of history for the learning method
    for i in range(first, len(c)):
        t = c[i]["t"]
        if last and t <= last:
            continue
        if dt.datetime.fromisoformat(t.replace("Z", "+00:00")) > done_before:
            break  # candle still open
        up = c[i]["c"] > c[i]["o"]
        live = t >= b["live_from"]
        for k, s in sigs.items():
            side = learning_pick(dec, ups, i) if k == "learning" else bet_signal(k, c, i)
            bank, peak, mdd, n, w = (("live_bank", "live_peak", "live_mdd", "live_n", "live_w") if live
                                     else ("bank", "peak", "mdd", "n", "w"))
            if side == 0 or s[bank] < 1:
                continue
            stake = s[bank] * BET_FRACTION
            won = (side > 0) == up and c[i]["c"] != c[i]["o"]
            s[bank] = round(s[bank] + (stake * BET_PAYOUT if won else -stake), 4)
            s[n] += 1; s[w] += won
            s[peak] = max(s[peak], s[bank])
            s[mdd] = min(s[mdd], s[bank] / s[peak] - 1)
        b["last_t"] = t
        scored += 1
    return scored


def betting_report(state):
    b = state.get("bets")
    if not b:
        return []
    lines = ["", "## 15-minute Bitcoin betting test (paper)", "",
             f"Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so "
             f"**{BREAK_EVEN:.1%} wins are needed just to break even**. Each method started with $100 "
             f"and bets 5% of what it has left.", "",
             "**Labels:** *Static* = always uses the same one method, never changes. "
             "*Learning* = every 15 minutes, checks which static method won the most over the last "
             "24 hours and copies it, or sits out if none is beating 55.6%. "
             "*Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.", "",
             f"### Live, since {b['live_from'][:10]} (fresh $100 each)", "",
             "| Method | Type | Bets | Win rate | $100 is now | Worst drop |", "|---|---|---:|---:|---:|---:|"]
    def table(prefix):
        out = []
        bank, n, w, mdd = (f"{prefix}bank", f"{prefix}n", f"{prefix}w", f"{prefix}mdd")
        for k, s in sorted(b["signals"].items(), key=lambda kv: -kv[1].get(bank, 0)):
            wr = f"{s[w] / s[n]:.1%}" if s[n] else "-"
            out.append(f"| {BET_SIGNALS[k]} | {BET_LABELS[k]} | {s[n]} | {wr} | ${s[bank]:,.2f}"
                       f"{' (ran out)' if s[bank] < 1 else ''} | {s[mdd]:.0%} |")
        return out
    lines += table("live_")
    lines += ["", "### Backtest: the 30 days before that", "",
              "| Method | Type | Bets | Win rate | $100 became | Worst drop |", "|---|---|---:|---:|---:|---:|"]
    lines += table("")
    lines += ["", "If a method can't beat the coin flip by a clear margin over hundreds of bets, it has no real edge."]
    return lines


def sp500_symbols():
    """Current S&P 500 list; refreshed from the web, with the copy in the repo as a fallback."""
    text = None
    try:
        r = requests.get(SP500_URL, timeout=30)
        if r.ok and r.text.startswith("Symbol"):
            text = r.text
            with open("sp500.csv", "w") as f:
                f.write(text)
    except requests.RequestException:
        pass
    if text is None:
        with open("sp500.csv") as f:
            text = f.read()
    rows = list(csv.reader(text.splitlines()))[1:]
    return [r[0].strip() for r in rows if r and r[0].strip()]


def twelve_month_returns(symbols):
    """Return over the 12 months ending last month (skipping the latest month, the standard way)."""
    start = (NOW - dt.timedelta(days=430)).strftime("%Y-%m-01T00:00:00Z")
    this_month = TODAY[:7]
    monthly = {}
    for k in range(0, len(symbols), 100):
        chunk, token = symbols[k:k + 100], None
        while True:
            params = {"symbols": ",".join(chunk), "timeframe": "1Month", "start": start,
                      "limit": 10000, "feed": "iex", "adjustment": "all"}
            if token:
                params["page_token"] = token
            d = api("GET", f"{DATA_URL}/v2/stocks/bars", params=params)
            for sym, bars in (d.get("bars") or {}).items():
                monthly.setdefault(sym, []).extend(b["c"] for b in bars if not b["t"].startswith(this_month))
            token = d.get("next_page_token")
            if not token:
                break
    return {sym: c[-1] / c[-13] - 1 for sym, c in monthly.items() if len(c) >= 13 and c[-13] > 0}


def fractionable(sym):
    try:
        a = api("GET", f"{ACCT['url']}/v2/assets/{sym}")
        return a.get("tradable") and a.get("fractionable")
    except TradeError:
        return False


def run_stock_momentum(key, cfg, s):
    month = TODAY[:7]
    held = sorted(sym for sym, q in s["pos"].items() if q > 0)
    if s.get("last_rebalance") == month:
        return f"holding {', '.join(held) or 'cash'} until next month's scan"
    if not can_trade("SPY"):
        return "waiting for market open for the monthly scan"
    rets = twelve_month_returns(sp500_symbols())
    if len(rets) < 100:
        return f"only got price history for {len(rets)} stocks; will retry next run"
    picks = []
    for sym in sorted(rets, key=rets.get, reverse=True):
        if sym in held or fractionable(sym):
            picks.append(sym)
        if len(picks) == cfg["top"]:
            break
    for sym in held:  # sell the ones that dropped out of the top 10
        if sym not in picks:
            sell(key, s, sym, s["pos"][sym])
    new = [sym for sym in picks if s["pos"].get(sym, 0) == 0]
    if new:
        each = s["cash"] / len(new)
        for sym in new:
            buy(key, s, sym, each * 0.995)
    s["last_rebalance"] = month
    best = ", ".join(f"{sym} {rets[sym]:+.0%}" for sym in picks)
    return f"scanned {len(rets)} stocks; top {len(picks)} for {month}: {best}"


def run_gradual(key, cfg, s):
    sym, done = cfg["symbol"], s.get("buys_done", 0)
    if done >= cfg["buys"]:
        return f"finished buying ({done} buys), now holding"
    last = s.get("last_buy")
    if last and (dt.date.fromisoformat(TODAY) - dt.date.fromisoformat(last)).days < cfg["every_days"]:
        return f"bought {done} of {cfg['buys']} times; next buy on or after " \
               f"{dt.date.fromisoformat(last) + dt.timedelta(days=cfg['every_days'])}"
    if not can_trade(sym):
        return f"bought {done} of {cfg['buys']} times; next buy when the market opens"
    per_buy = cfg["per_buy"] * s.get("budget", START_BUDGET) / START_BUDGET
    amount = s["cash"] * 0.995 if done == cfg["buys"] - 1 else per_buy
    buy(key, s, sym, amount)
    s["buys_done"], s["last_buy"] = done + 1, TODAY
    return f"bought {done + 1} of {cfg['buys']} times"


# ---------- SpaceX watch ----------
SPACEX_IPO_PRICE = 135.0
SPACEX_IPO_DATE = "2026-06-12"
# Dates when more pre-IPO shares become allowed to be sold (public reporting; "eligible" doesn't mean sold).
SPACEX_UNLOCKS = [
    ("2026-12-08", "end of the 180-day lockup, ~342 million shares"),
    ("2027-03-18", "~176 million shares"),
    ("2027-05-17", "~176 million shares"),
    ("2027-06-12", "Elon Musk's own lockup ends (6.4 billion shares)"),
]
SPACEX_EARNINGS_NOTE = ("More shares also unlock 2 trading days after each quarterly earnings report "
                        "(next: Q4 2026 results, early 2027).")
SPACEX_LINES = []
SPACEX_SERIES = {}
IPO_LINES = []
_ipo_ready = {}


def ipo_ready(sym):
    """True once a pending-IPO stock is listed and tradable under the expected company name."""
    if sym not in PENDING_IPO:
        return True
    if sym not in _ipo_ready:
        try:
            a = api("GET", f"{PAPER['url']}/v2/assets/{sym}")
            _ipo_ready[sym] = bool(a.get("tradable")) and PENDING_IPO[sym].lower() in (a.get("name") or "").lower()
        except TradeError:
            _ipo_ready[sym] = False
    return _ipo_ready[sym]


def run_strategy(key, cfg, s):
    syms = [cfg["symbol"]] if cfg.get("symbol") else []
    for sym in syms:
        if not ipo_ready(sym):
            return f"waiting for {PENDING_IPO[sym]}'s IPO; buys automatically once {sym} starts trading"
    return RUNNERS[cfg["type"]](key, cfg, s)


def ipo_watch(state):
    """Short report section for pending IPOs, plus a one-time alert when trading starts."""
    global IPO_LINES
    alerts, w = [], state.setdefault("ipo_watch", {})
    L = []
    for sym, company in PENDING_IPO.items():
        info = w.setdefault(sym, {})
        if not ipo_ready(sym):
            L += [f"## {company} watch ({sym})", "",
                  f"Not trading yet. {company} filed to go public on the Nasdaq as **{sym}** (Oct 26, 2026); "
                  f"the date and price aren't set. The bot checks every 30 minutes and will buy for the "
                  f"{company} strategies as soon as it lists, and send you a notification.", ""]
            continue
        price = latest(sym)
        if not info.get("first_seen"):
            info["first_seen"], info["first_price"] = TODAY, price
            alerts.append((f"{company} ({sym}) is now trading at ${price:,.2f}",
                           f"{company} started trading. The bot is buying for the {company} buy & hold and "
                           f"gradual-buy strategies. The trend strategy waits for 50 days of prices."))
        c = closes(sym, 60)
        since = price / info["first_price"] - 1
        L += [f"## {company} watch ({sym})", "",
              f"**${price:,.2f}** · {since:+.1%} since the bot first saw it trading on {info['first_seen']} "
              f"(${info['first_price']:,.2f})" + (f" · {len(c)} days of price history" if c else ""), ""]
        if c:
            prev = c[-1]
            move = price / prev - 1
            if abs(move) >= 0.05 and info.get("move_alert") != TODAY:
                info["move_alert"] = TODAY
                alerts.append((f"{company} {'up' if move > 0 else 'down'} {abs(move):.1%} today (${price:,.2f})",
                               f"Moved {move:+.1%} since yesterday's close of ${prev:,.2f}."))
    IPO_LINES = L
    return alerts


def spacex_watch(state):
    """Build the SpaceX section of the report and return alerts worth a phone notification."""
    global SPACEX_LINES
    d = api("GET", f"{DATA_URL}/v2/stocks/bars",
            params={"symbols": "SPCX", "timeframe": "1Day", "start": SPACEX_IPO_DATE + "T00:00:00Z",
                    "limit": 10000, "feed": "iex", "adjustment": "all"})
    bars = [b for b in (d.get("bars") or {}).get("SPCX", []) if not b["t"].startswith(TODAY)]
    if len(bars) < 5:
        SPACEX_LINES = ["## SpaceX watch", "", "Not enough SpaceX price history yet."]
        return []
    closes_ = [b["c"] for b in bars]
    price = latest("SPCX")
    prev = closes_[-1]
    high = max(max(b["h"] for b in bars), price)
    low = min(min(b["l"] for b in bars), price)
    avg50 = sum(closes_[-50:]) / min(50, len(closes_))
    def chg(n):
        return price / closes_[-n] - 1 if len(closes_) >= n else None
    daily = [abs(closes_[i] / closes_[i - 1] - 1) for i in range(max(1, len(closes_) - 20), len(closes_))]
    typical = sum(daily) / len(daily)
    spy = closes("SPY", 200)
    w = state.setdefault("spacex_watch", {})
    w.setdefault("spy_at_ipo", None)
    if w["spy_at_ipo"] is None:
        sb = api("GET", f"{DATA_URL}/v2/stocks/bars",
                 params={"symbols": "SPY", "timeframe": "1Day", "start": SPACEX_IPO_DATE + "T00:00:00Z",
                         "limit": 1, "feed": "iex", "adjustment": "all"})
        first = (sb.get("bars") or {}).get("SPY", [])
        w["spy_at_ipo"] = first[0]["o"] if first else spy[-1]
    spy_since = latest("SPY") / w["spy_at_ipo"] - 1
    today = dt.date.fromisoformat(TODAY)
    upcoming = [(dt.date.fromisoformat(dd), what) for dd, what in SPACEX_UNLOCKS if dt.date.fromisoformat(dd) >= today]

    def pct(x):
        return "-" if x is None else f"{x:+.1%}"
    L = ["## SpaceX watch (SPCX)", "",
         f"**${price:,.2f}** · today {pct(price / prev - 1)} · 1 week {pct(chg(5))} · 1 month {pct(chg(21))}", "",
         "| | |", "|---|---|",
         f"| Since the IPO at ${SPACEX_IPO_PRICE:.0f} (Jun 12) | {pct(price / SPACEX_IPO_PRICE - 1)} "
         f"(S&P 500 in the same time: {pct(spy_since)}) |",
         f"| Highest / lowest since IPO | ${high:,.2f} / ${low:,.2f} · now {pct(price / high - 1)} from the high |",
         f"| 50-day average | ${avg50:,.2f} · price is **{'above' if price > avg50 else 'below'}** it "
         f"({'uptrend' if price > avg50 else 'downtrend'}) |",
         f"| Typical daily move (last 20 days) | ±{typical:.1%} (the S&P 500 is usually under ±1%) |"]
    if upcoming:
        L += ["", "**Upcoming share unlocks** (more pre-IPO shares become sellable, which can push the price down):", ""]
        L += [f"- {dd.strftime('%b %d, %Y')} ({(dd - today).days} days): {what}" for dd, what in upcoming]
        L += [f"- {SPACEX_EARNINGS_NOTE}"]
    L += ["", "You'll get a GitHub notification for: a move of 5% or more in a day, crossing the 50-day average, "
          "a new high since the IPO, a 20% drop from the high, and 3 days before each unlock."]
    SPACEX_LINES = L
    SPACEX_SERIES.update({"dates": [b["t"][:10] for b in bars], "closes": [round(x, 2) for x in closes_],
                          "price": round(price, 2), "high": round(high, 2), "low": round(low, 2),
                          "avg50": round(avg50, 2), "typical_move": round(typical, 4),
                          "since_ipo": round(price / SPACEX_IPO_PRICE - 1, 4), "spy_since_ipo": round(spy_since, 4),
                          "unlocks": [{"date": dd.isoformat(), "what": what, "days": (dd - today).days}
                                      for dd, what in upcoming]})

    # alerts, each kind at most once per day (unlock alerts once each)
    alerts, sent = [], w.setdefault("sent", {})
    def alert(kind, title, body, once_ever=False):
        tag = kind if once_ever else f"{kind}:{TODAY}"
        if tag not in sent:
            sent[tag] = NOW.strftime("%Y-%m-%d %H:%M")
            alerts.append((title, body))
    move = price / prev - 1
    if abs(move) >= 0.05:
        alert("move", f"SpaceX {'up' if move > 0 else 'down'} {abs(move):.1%} today (${price:,.2f})",
              f"SpaceX moved {move:+.1%} since yesterday's close of ${prev:,.2f}.")
    above = price > avg50
    if w.get("above_avg") is not None and w["above_avg"] != above:
        alert("cross", f"SpaceX crossed {'above' if above else 'below'} its 50-day average",
              f"Price ${price:,.2f} vs 50-day average ${avg50:,.2f}. "
              f"The SpaceX trend strategy will now {'buy' if above else 'move to cash'}.")
    w["above_avg"] = above
    if w.get("high") and price > w["high"]:
        alert("high", f"SpaceX new high since IPO: ${price:,.2f}", f"Previous high was ${w['high']:,.2f}.")
    w["high"] = max(w.get("high") or 0, high)
    if price <= high * 0.8:
        alert("drawdown", f"SpaceX is {1 - price / high:.0%} below its high", f"High ${high:,.2f}, now ${price:,.2f}.")
    for dd, what in upcoming:
        if 0 <= (dd - today).days <= 3:
            alert(f"unlock:{dd}", f"SpaceX share unlock on {dd.strftime('%b %d')}", what, once_ever=True)
    return alerts


def send_alerts(alerts):
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    for title, body in alerts:
        print(f"ALERT: {title}")
        if not (token and repo):
            continue
        try:
            requests.post(f"https://api.github.com/repos/{repo}/issues", timeout=30,
                          headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                          json={"title": title, "body": body + "\n\nSee REPORT.md for the full SpaceX watch. "
                                "Close this issue once you've read it."})
        except requests.RequestException as e:
            print(f"Could not send alert: {e}")


RUNNERS = {"hold": run_hold, "trend": run_trend, "mix": run_mix, "momentum": run_momentum, "rsi": run_rsi,
           "stock_momentum": run_stock_momentum, "gradual": run_gradual}


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


def strategy_label(cfg):
    """(type, market) labels shown in the scoreboard."""
    kind = {"hold": "Hold", "trend": "Static rule", "mix": "Static rule (rebalance)",
            "momentum": "Monthly pick", "rsi": "Static rule", "stock_momentum": "Monthly pick",
            "gradual": "Gradual buy"}[cfg["type"]]
    if cfg["type"] == "stock_momentum":
        return kind, "Stock"
    syms = cfg.get("symbols") or list(cfg.get("weights", {})) or [cfg.get("symbol")]
    if all(is_crypto(s) for s in syms):
        market = "Bitcoin"
    elif cfg["type"] == "mix":
        market = "Mixed"
    elif all(s in STOCKS for s in syms):
        market = "Stock"
    else:
        market = "ETF"
    return kind, market


def write_reports(state, notes):
    rows, values = [], {}
    for key, cfg in STRATEGIES.items():
        s = state["strategies"][key]
        v = value(s)
        values[key] = v
        holding = ", ".join(f"{sym} ${q * latest(sym):,.2f}" for sym, q in s["pos"].items() if q * latest(sym) >= 0.01)
        holding = (holding + ", " if holding else "") + f"cash ${s['cash']:,.2f}"
        rows.append((cfg["name"], v, s["trades"], holding, notes[key], strategy_label(cfg)))
    rows.sort(key=lambda r: -r[1])
    lines = [
        "# Paper trading scoreboard",
        "",
        f"Each strategy started with **${START_BUDGET:.0f}** of paper money on {state['started']}.",
        f"Last update: {NOW.strftime('%b %d, %Y %H:%M')} UTC · Bitcoin ${latest('BTC/USD'):,.2f} · "
        f"US stock market {'open' if can_trade('SPY') else 'closed'}",
        "",
        *SPACEX_LINES,
        "",
        *IPO_LINES,
        "",
        "## All strategies",
        "",
        "**Labels:** *Hold* = buys once and never sells (the yardstick). "
        "*Static rule* = trades by one fixed rule that never changes. "
        "*Monthly pick* = once a month, switches to whichever investment rose most over the past year. "
        "*Gradual buy* = spreads the purchase over several weeks instead of buying all at once.",
        "",
        "| Rank | Strategy | Type | Market | Worth now | Profit | Trades |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for i, (name, v, t, _, _, (kind, market)) in enumerate(rows, 1):
        p = v - START_BUDGET
        lines.append(f"| {i} | {name} | {kind} | {market} | ${v:,.2f} | {'+' if p >= 0 else '-'}${abs(p):,.2f} ({p / START_BUDGET:+.1%}) | {t} |")
    total = sum(values.values())
    lines += ["", "## Holding vs trading, same asset", "",
              "| Asset | Buy & hold | With trading rule | Better so far |", "|---|---:|---:|---|"]
    for asset, hk, tk in PAIRS:
        h, tr = values[hk], values[tk]
        better = "about even" if abs(h - tr) < 0.5 else ("holding" if h > tr else "trading")
        lines.append(f"| {asset} | ${h:,.2f} | ${tr:,.2f} | {better} |")
    lines += ["", f"**All together:** ${total:,.2f} from ${START_BUDGET * len(STRATEGIES):,.0f} "
                  f"({total - START_BUDGET * len(STRATEGIES):+,.2f})", "", "## What each one is doing", ""]
    for name, _, _, holding, note, _ in rows:
        lines.append(f"- **{name}:** {holding}. {note[:1].upper() + note[1:]}.")
    lines += betting_report(state)
    lines += ["", "Paper money only. Past or paper results do not predict real results.", ""]
    with open("REPORT.md", "w") as f:
        f.write("\n".join(lines))

    # one row per day in history.csv
    keys = list(STRATEGIES)
    exists = os.path.exists("history.csv")
    if exists:
        with open("history.csv") as f:
            lines_ = f.read().strip().splitlines()
        if lines_[0] != ",".join(["date"] + keys):  # strategies changed: start a fresh file
            os.replace("history.csv", f"history_until_{TODAY}.csv")
            exists = False
        elif lines_[-1].startswith(TODAY):
            return values
    with open("history.csv", "a", newline="") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["date"] + keys)
        w.writerow([TODAY] + [f"{values[k]:.2f}" for k in keys])
    return values


# ---------- dashboard data (docs/data.json, shown by docs/index.html on GitHub Pages) ----------
def record_timeline(values):
    """Append this run's value of every strategy to timeline.csv (one row per run)."""
    keys = list(STRATEGIES)
    header = ["time"] + keys
    rows = []
    if os.path.exists("timeline.csv"):
        with open("timeline.csv") as f:
            rows = list(csv.reader(f))
    if not rows:
        rows = [header]
    elif rows[0] != header:  # strategies were added: keep old columns' data, fill new ones as blank
        old = rows[0]
        rows = [header] + [[r[0]] + [r[old.index(k)] if k in old and old.index(k) < len(r) else "" for k in keys]
                           for r in rows[1:]]
    stamp = NOW.strftime("%Y-%m-%dT%H:%MZ")
    if rows[-1][0] != stamp:
        rows.append([stamp] + [f"{values[k]:.2f}" for k in keys])
    with open("timeline.csv", "w", newline="") as f:
        csv.writer(f).writerows(rows)
    return rows


def max_drop(series):
    peak, worst = None, 0.0
    for v in series:
        if v is None:
            continue
        peak = v if peak is None else max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst


def analysis(strats, pairs, bets, days):
    out = []
    up = [s for s in strats if s["profit"] > 0.005]
    best, worst = strats[0], strats[-1]
    out.append(f"After {days:.1f} days, {len(up)} of {len(strats)} strategies are up. Leader: {best['name']} "
               f"({best['profit']:+.2f}). Last: {worst['name']} ({worst['profit']:+.2f}).")
    for group in ("type", "market"):
        avg = {}
        for s in strats:
            avg.setdefault(s[group], []).append(s["profit"])
        ranked = sorted(((sum(v) / len(v), k, len(v)) for k, v in avg.items()), reverse=True)
        out.append(("By type: " if group == "type" else "By market: ") +
                   ", ".join(f"{k} {a:+.2f} avg ({n})" for a, k, n in ranked) + ".")
    tw = sum(1 for p in pairs if p["trade"] - p["hold"] > 0.5)
    hw = sum(1 for p in pairs if p["hold"] - p["trade"] > 0.5)
    out.append(f"Holding vs trading the same asset: trading ahead on {tw}, holding ahead on {hw}, "
               f"about even on {len(pairs) - tw - hw}.")
    risky = min(strats, key=lambda s: s["max_drop"])
    if risky["max_drop"] < -0.001:
        out.append(f"Biggest drop from a peak so far: {risky['name']} ({risky['max_drop']:.1%}).")
    live = [m for m in bets["methods"] if m["live"]["n"] >= 20]
    if live:
        top = max(live, key=lambda m: m["live"]["w"] / m["live"]["n"])
        rate = top["live"]["w"] / top["live"]["n"]
        out.append(f"15-minute betting: best live win rate is {top['name'].split(':')[0]} at {rate:.1%} over "
                   f"{top['live']['n']} bets, {'above' if rate > BREAK_EVEN else 'below'} the "
                   f"{BREAK_EVEN:.1%} needed to profit.")
    if days < 30:
        out.append("Under a month of data: most of these differences are still day-to-day noise, not skill.")
    return out


def write_dashboard(state, notes, values):
    rows = record_timeline(values)
    keys = rows[0][1:]
    times = [r[0] for r in rows[1:]]
    series = {k: [float(r[i + 1]) if i + 1 < len(r) and r[i + 1] else None for r in rows[1:]]
              for i, k in enumerate(keys)}
    strats = []
    for k, cfg in STRATEGIES.items():
        s = state["strategies"][k]
        kind, market = strategy_label(cfg)
        holds = [{"sym": sym, "value": round(q * latest(sym), 2)} for sym, q in s["pos"].items()
                 if q > 0 and q * latest(sym) >= 0.01]
        strats.append({"key": k, "name": cfg["name"], "type": kind, "market": market,
                       "value": round(values[k], 2), "profit": round(values[k] - START_BUDGET, 2),
                       "trades": s["trades"], "cash": round(s["cash"], 2), "holdings": holds,
                       "note": notes.get(k, ""), "max_drop": round(max_drop(series.get(k, [])), 4)})
    strats.sort(key=lambda x: -x["value"])
    pairs = [{"asset": a, "hold": round(values[h], 2), "trade": round(values[tr], 2)} for a, h, tr in PAIRS]
    b = state.get("bets", {})
    methods = []
    for k, s in b.get("signals", {}).items():
        methods.append({"key": k, "name": BET_SIGNALS[k], "label": BET_LABELS[k],
                        "live": {"n": s["live_n"], "w": s["live_w"], "bank": round(s["live_bank"], 2),
                                 "mdd": round(s["live_mdd"], 4)},
                        "backtest": {"n": s["n"], "w": s["w"], "bank": round(s["bank"], 2), "mdd": round(s["mdd"], 4)}})
    bets = {"break_even": round(BREAK_EVEN, 4), "live_from": b.get("live_from"), "methods": methods}
    started = dt.datetime.fromisoformat(times[0].replace("Z", "+00:00")) if times else NOW
    days = max((NOW - started).total_seconds() / 86400, 0.01)
    ipo = {}
    for sym, company in PENDING_IPO.items():
        info = state.get("ipo_watch", {}).get(sym, {})
        ipo[sym] = {"company": company, "trading": ipo_ready(sym),
                    "price": round(latest(sym), 2) if ipo_ready(sym) else None,
                    "first_seen": info.get("first_seen"), "first_price": info.get("first_price")}
    try:
        with open("LIVE_REPORT.md") as f:
            live_status = next((ln for ln in f.read().splitlines() if ln.startswith("**")), "")
    except OSError:
        live_status = ""
    data = {"updated": NOW.strftime("%Y-%m-%dT%H:%MZ"), "started": state.get("started"),
            "budget": START_BUDGET, "btc": round(latest("BTC/USD"), 2), "market_open": can_trade("SPY"),
            "total": round(sum(values.values()), 2), "count": len(values),
            "strategies": strats, "timeline": {"times": times, "series": series},
            "pairs": pairs, "betting": bets, "spacex": SPACEX_SERIES, "ipo": ipo,
            "live_status": live_status.replace("**", ""),
            "analysis": analysis(strats, pairs, bets, days)}
    os.makedirs("docs", exist_ok=True)
    with open("docs/data.json", "w") as f:
        json.dump(data, f, separators=(",", ":"))


# =====================================================================
# LIVE TRADING WITH REAL MONEY  (off unless live_config.json says "enabled": true)
# =====================================================================
LIVE_URL = "https://api.alpaca.markets"


def live_report(lines):
    with open("LIVE_REPORT.md", "w") as f:
        f.write("\n".join(["# Live trading (real money)", "",
                           f"Last check: {NOW.strftime('%b %d, %Y %H:%M')} UTC", ""] + lines + [""]))


def run_live():
    """Run the strategies chosen in live_config.json with real money, inside strict limits."""
    global ACCT
    try:
        with open("live_config.json") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        live_report([f"**OFF.** Could not read live_config.json ({e})."])
        return []
    if not cfg.get("enabled"):
        live_report(["**OFF.** Live trading is switched off in live_config.json. Nothing is bought or sold "
                     "with real money. See LIVE.md for how to switch it on."])
        return []
    key, secret = os.environ.get("ALPACA_LIVE_KEY"), os.environ.get("ALPACA_LIVE_SECRET")
    if not key or not secret:
        live_report(["**WAITING.** live_config.json is on, but the ALPACA_LIVE_KEY and ALPACA_LIVE_SECRET "
                     "secrets are not set in GitHub yet."])
        return []
    budgets = {k: float(v) for k, v in cfg.get("strategies", {}).items()}
    unknown = [k for k in budgets if k not in STRATEGIES]
    if unknown:
        live_report([f"**STOPPED.** Unknown strategy names in live_config.json: {', '.join(unknown)}. "
                     "Use the names listed in LIVE.md."])
        return []
    cap = float(cfg.get("max_total_dollars", 0))
    if sum(budgets.values()) > cap:
        live_report([f"**STOPPED.** The strategy budgets add up to ${sum(budgets.values()):,.2f}, more than "
                     f"max_total_dollars (${cap:,.2f}). Lower a budget or raise the limit."])
        return []

    ACCT = {"live": True, "url": LIVE_URL, "trades_file": "trades_live.csv",
            "headers": {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}}
    alerts = []
    try:
        acct = api("GET", f"{LIVE_URL}/v2/account")
        if acct.get("status") != "ACTIVE" or acct.get("trading_blocked") or acct.get("account_blocked"):
            live_report([f"**STOPPED.** Alpaca says the live account isn't ready to trade "
                         f"(status: {acct.get('status')})."])
            return []
        state = {"strategies": {}, "halted": False}
        if os.path.exists("live_state.json"):
            with open("live_state.json") as f:
                state = json.load(f)
        strat = state["strategies"]
        for k, budget in budgets.items():
            if k not in strat:  # newly added: needs real cash available in the account
                if float(acct.get("cash", 0)) < budget:
                    alerts.append(("Live: not enough cash", f"Need ${budget:,.2f} to start {STRATEGIES[k]['name']}, "
                                   f"but the account has ${float(acct.get('cash', 0)):,.2f}."))
                    continue
                strat[k] = {"cash": budget, "budget": budget, "pos": {}, "trades": 0, "started": TODAY}
                acct["cash"] = str(float(acct.get("cash", 0)) - budget)
        invested = sum(s["budget"] for s in strat.values())
        total = sum(value(s) for s in strat.values())
        stop_pct = float(cfg.get("stop_if_down_percent", 20))
        notes = {}

        if cfg.get("sell_everything_now") or (invested and total <= invested * (1 - stop_pct / 100) and not state["halted"]):
            reason = ("sell_everything_now is set in live_config.json" if cfg.get("sell_everything_now")
                      else f"total value fell {stop_pct:.0f}% below what was put in")
            for k, s in strat.items():
                for sym, q in list(s["pos"].items()):
                    if q > 0:
                        try:
                            if can_trade(sym):
                                sell(k, s, sym, q, urgent=True)
                        except TradeError as e:
                            notes[k] = f"could not sell {sym}: {e}"
            if not cfg.get("sell_everything_now"):
                state["halted"] = True
                alerts.append(("Live trading STOPPED: loss limit reached",
                               f"The live strategies are worth ${total:,.2f} from ${invested:,.2f} put in. "
                               f"The bot sold what it could and stopped. To restart, see LIVE.md."))
            notes = {k: notes.get(k, f"selling everything ({reason})") for k in strat}
        elif state["halted"]:
            for k, s in strat.items():  # keep selling anything left (e.g. stocks while the market was closed)
                notes[k] = "halted after hitting the loss limit (see LIVE.md to restart)"
                for sym, q in list(s["pos"].items()):
                    if q > 0 and can_trade(sym):
                        try:
                            sell(k, s, sym, q, urgent=True)
                        except TradeError as e:
                            notes[k] = f"halted; could not sell {sym} yet: {e}"
        else:
            for k, s in strat.items():
                if k not in budgets:
                    notes[k] = "removed from live_config.json; holding what it has, no new trades"
                    continue
                try:
                    notes[k] = run_strategy(k, STRATEGIES[k], s)
                except TradeError as e:
                    notes[k] = f"problem this run: {e}"

        with open("live_state.json", "w") as f:
            json.dump(state, f, indent=2)
            f.write("\n")
        total = sum(value(s) for s in strat.values())
        lines = [f"**ON.** Real money. Stops and sells everything if the total falls below "
                 f"${invested * (1 - stop_pct / 100):,.2f} ({stop_pct:.0f}% loss)." if not state["halted"]
                 else "**HALTED** after hitting the loss limit. No new trades.", "",
                 f"**Total: ${total:,.2f}** from ${invested:,.2f} put in ({total - invested:+,.2f}, "
                 f"{(total / invested - 1) if invested else 0:+.1%})", "",
                 "| Strategy | Put in | Worth now | Profit | Trades | Doing |", "|---|---:|---:|---:|---:|---|"]
        for k, s in strat.items():
            v = value(s)
            lines.append(f"| {STRATEGIES[k]['name']} | ${s['budget']:,.2f} | ${v:,.2f} | {v - s['budget']:+,.2f} | "
                         f"{s['trades']} | {notes.get(k, '')} |")
        live_report(lines)
        print(f"\nLIVE: total ${total:,.2f} from ${invested:,.2f}")
    except (TradeError, requests.RequestException, KeyError, ValueError) as e:
        live_report([f"**PROBLEM this run:** {e}. The bot will try again in 30 minutes."])
        alerts.append(("Live trading problem", str(e)))
    finally:
        ACCT = PAPER
    return alerts + LIVE_TRADE_ALERTS


def main():
    state = load_state()
    notes = {}
    for key, cfg in STRATEGIES.items():
        try:
            notes[key] = run_strategy(key, cfg, state["strategies"][key])
        except TradeError as e:
            notes[key] = f"problem this run: {e}"
        print(f"{cfg['name']}: {notes[key]}")
    try:
        n = run_betting(state)
        print(f"\n15-minute betting test: scored {n} new candles")
    except (TradeError, requests.RequestException) as e:
        print(f"\n15-minute betting test: problem this run: {e}")
    try:
        send_alerts(spacex_watch(state))
    except (TradeError, requests.RequestException, KeyError, ValueError) as e:
        print(f"SpaceX watch: problem this run: {e}")
    try:
        send_alerts(ipo_watch(state))
    except (TradeError, requests.RequestException, KeyError, ValueError) as e:
        print(f"IPO watch: problem this run: {e}")
    state["last_check_utc"] = NOW.strftime("%Y-%m-%d %H:%M")
    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    values = write_reports(state, notes)
    try:
        send_alerts(run_live())
    except Exception as e:  # never let a live-trading error stop the paper test
        print(f"LIVE: unexpected problem: {e}")
    try:
        write_dashboard(state, notes, values)
    except Exception as e:  # the dashboard is a nice-to-have; never let it break trading
        print(f"Dashboard: problem this run: {e}")
    print("\n" + "\n".join(f"{STRATEGIES[k]['name']}: ${v:,.2f} ({v - START_BUDGET:+.2f})" for k, v in values.items()))


if __name__ == "__main__":
    main()
