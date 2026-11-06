"""IB trader: runs on your always-on Mac next to IB Gateway and carries out the evening plan on Interactive Brokers.

The decisions are made every evening on GitHub (same rules as everywhere else) and saved to
monitor/output/ib_plan.json. This program, on the Mac:
  - pulls the latest plan from GitHub every few minutes
  - during market hours, once per new plan: sells what the plan sells, then buys its replacements
    (each replacement gets the money from the stock it replaces; empty slots get 20% of the account)
  - every few minutes: checks each holding against its stop and target; a hit is sold right away and
    the money moved into the next strongest stock from the plan
  - sends every action to Telegram and logs it to ~/ib-trader/log.csv

Safety:
  - PAPER account by default (port 4002). Real money only when ~/ib-trader/settings.json says "live": true
    and the port is 4001.
  - Only stocks from the plan are bought; no single buy over 50% of the account; nothing bought is sold the
    same day (avoids good-faith violations in a cash account); never trades on a plan older than 4 days.
  - Pause: "paused": true in monitor/ib_switch.json on GitHub (editable from the GitHub app), or in
    ~/ib-trader/settings.json on the Mac.

Run on the Mac:   python3 -m monitor.ib_trader            (keeps running; the setup script installs it to
                  python3 -m monitor.ib_trader --once     start automatically)
"""
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time

from . import autotrade, config
from .alpaca import AlpacaError as BrokerError

HOME = os.path.expanduser("~/ib-trader")
SETTINGS_FILE = os.path.join(HOME, "settings.json")
REPO = os.path.dirname(config.BASE_DIR)
IB_PLAN_FILE = os.path.join(config.BASE_DIR, "output", "ib_plan.json")
IB_SWITCH_FILE = os.path.join(config.BASE_DIR, "ib_switch.json")
LOOP_SECONDS = 120
DEFAULTS = {"host": "127.0.0.1", "port": 4002, "client_id": 17, "live": False, "paused": False,
            "telegram_bot_token": "", "telegram_chat_id": "", "max_order_pct": 50}


def settings():
    s = dict(DEFAULTS)
    s.update(autotrade.load_json(SETTINGS_FILE, {}))
    if s["live"] and int(s["port"]) == 4002:
        s["port"] = 4001
    if not s["live"] and int(s["port"]) == 4001:
        s["port"] = 4002  # paper mode never talks to the live port
    return s


def market_open(now=None):
    """Regular US session, weekdays 9:30-16:00 New York (holidays: orders just don't fill; nothing breaks)."""
    from zoneinfo import ZoneInfo
    now = now or dt.datetime.now(ZoneInfo("America/New_York"))
    return now.weekday() < 5 and dt.time(9, 30) <= now.time() < dt.time(16, 0), now


def last_price(symbol):
    try:
        import yfinance as yf
        p = yf.Ticker(symbol.replace(".", "-")).fast_info["last_price"]
        return float(p) if p and p == p else None
    except Exception:  # noqa: BLE001
        return None


class IBClient:
    """Speaks the same small interface as the Alpaca client, so the autopilot engine can drive IB."""

    def __init__(self, ib, price=last_price, now=None):
        self.ib, self.price, self._now = ib, price, now
        self.trades = {}

    def clock(self):
        is_open, now = market_open(self._now)
        return {"is_open": is_open, "timestamp": now.isoformat()}

    def account(self):
        vals = {v.tag: v.value for v in self.ib.accountSummary() if v.currency in ("USD", "BASE", "")}
        eq = float(vals.get("NetLiquidation") or 0)
        cash = float(vals.get("AvailableFunds") or vals.get("TotalCashValue") or 0)
        return {"equity": eq, "cash": cash}

    def positions(self):
        out = []
        for p in self.ib.positions():
            c = p.contract
            if c.secType != "STK" or not p.position:
                continue
            qty, avg = float(p.position), float(p.avgCost)
            px = self.price(c.symbol) or avg
            out.append({"symbol": c.symbol, "qty": qty, "avg_entry_price": avg, "current_price": px,
                        "market_value": qty * px, "cost_basis": qty * avg})
        return out

    def _place(self, symbol, side, qty):
        from ib_async import MarketOrder, Stock
        contract = Stock(symbol, "SMART", "USD")
        if not self.ib.qualifyContracts(contract):
            raise BrokerError(f"IB doesn't know the stock {symbol}")
        order = MarketOrder(side, qty, tif="DAY")
        trade = self.ib.placeOrder(contract, order)
        oid = str(trade.order.orderId)
        self.trades[oid] = trade
        return {"id": oid}

    def close(self, symbol):
        pos = [p for p in self.positions() if p["symbol"] == symbol]
        if not pos:
            raise BrokerError(f"no {symbol} position to sell")
        return self._place(symbol, "SELL", abs(pos[0]["qty"]))

    def buy(self, symbol, dollars):
        px = self.price(symbol)
        if not px:
            raise BrokerError(f"no price for {symbol}")
        qty = math.floor(dollars / px * 10000) / 10000  # IB fractional shares: 4 decimals
        if qty <= 0:
            raise BrokerError(f"${dollars:.2f} is too small for one 0.0001 share of {symbol}")
        return self._place(symbol, "BUY", qty)

    def order(self, oid):
        t = self.trades.get(str(oid))
        if t is None:
            return {}
        self.ib.sleep(0.5)  # let IB deliver status updates
        st = t.orderStatus.status
        status = {"Filled": "filled", "Cancelled": "canceled", "ApiCancelled": "canceled",
                  "Inactive": "rejected"}.get(st, st.lower())
        if status == "rejected" or status == "canceled":
            msg = "; ".join(e.message for e in t.log if e.message)[:200]
            raise BrokerError(f"IB {st}: {msg}") if msg else BrokerError(f"IB order {st}")
        return {"status": status, "filled_avg_price": t.orderStatus.avgFillPrice or None}


def git_pull():
    r = subprocess.run(["git", "-C", REPO, "pull", "-q", "--ff-only"], capture_output=True, text=True, timeout=120)
    return r.returncode == 0


def setup_engine(s):
    os.makedirs(HOME, exist_ok=True)
    mode = "REAL MONEY" if s["live"] else "paper account"
    autotrade.configure(plan_file=IB_PLAN_FILE, state_file=os.path.join(HOME, "state.json"),
                        log_file=os.path.join(HOME, "log.csv"), switch_file=IB_SWITCH_FILE,
                        label=f"🏦 IB trader ({mode})", max_order_pct=s["max_order_pct"])
    if s["telegram_bot_token"] and s["telegram_chat_id"]:
        os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"] = s["telegram_bot_token"], str(s["telegram_chat_id"])


def connect(s):
    from ib_async import IB
    ib = IB()
    ib.connect(s["host"], int(s["port"]), clientId=int(s["client_id"]), timeout=20)
    accts = ib.managedAccounts()
    if s["live"] == any(a.startswith("D") for a in accts):  # IB paper accounts start with "D"
        ib.disconnect()
        raise BrokerError(f"settings say live={s['live']} but IB Gateway is logged in to {accts}; "
                          "log in to the matching account")
    return ib


def once(ib, s):
    if s.get("paused"):
        return "paused (settings.json)"
    return autotrade.execute(client=IBClient(ib))


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    s = settings()
    setup_engine(s)
    ib, last_warn, last_pull = None, 0.0, 0.0
    autotrade.notify(f"Started on the Mac, watching the {'REAL' if s['live'] else 'paper'} IB account "
                     f"(port {s['port']}).")
    while True:
        s = settings()
        is_open, now = market_open()
        if time.time() - last_pull > 600 or is_open:
            git_pull()
            last_pull = time.time()
        if is_open or "--once" in argv:
            try:
                if ib is None or not ib.isConnected():
                    ib = connect(s)
                print(now.strftime("%Y-%m-%d %H:%M"), once(ib, s), flush=True)
            except Exception as e:  # noqa: BLE001 - keep running; warn at most once an hour
                print(now.strftime("%Y-%m-%d %H:%M"), "problem:", e, flush=True)
                if time.time() - last_warn > 3600:
                    autotrade.notify(f"⚠️ Can't trade right now: {str(e)[:200]}\nIf IB Gateway asks you to log in "
                                     "(weekly), approve it on your phone; I'll keep retrying.")
                    last_warn = time.time()
                try:
                    if ib is not None:
                        ib.disconnect()
                except Exception:  # noqa: BLE001
                    pass
                ib = None
        if "--once" in argv:
            break
        time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
