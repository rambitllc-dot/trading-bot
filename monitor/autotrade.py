"""Autopilot (practice): runs the strategy by itself in a separate Alpaca PAPER account. No real money.

Same rules as the monitor uses for your IB book:
  - 5 stocks, equal weight (20% each), bought from the top of the ranking (score 80+)
  - 6% max-loss stop, breakeven after +10%, trailing stop, 2-to-1 target (levels.py)
  - a stop or target hit -> sell right away and buy the strongest stock not owned
  - weekly swaps when a clearly stronger stock appears; WEAK / LOSING holdings first in line (rotation.py)
  - nothing bought back within 30 days of selling it

Two steps:
  plan     every evening, inside the monitor run: reads the paper account, applies the rules, and writes
           autotrade/plan.json (what to sell, what to buy, each holding's stop and target, backups).
  execute  every 30 minutes from the always-on bot loop, but only while the market is open:
           - once per new plan: sells, then buys (market orders, dollar amounts, fractional shares)
           - every round: a holding at its stop or target is sold and replaced right away
Safety: paper account only (AUTO_LIVE False); buys only stocks from the plan; no single buy over 25% of the
account; never sells a stock the same day it was bought; pause switch in autotrade/switch.json; every trade
is logged to autotrade/log.csv and sent to Telegram.
"""
import csv
import datetime as dt
import json
import os
import sys
import time

from . import config, levels, performance, rotation, storage
from .alpaca import Alpaca, AlpacaError

PLAN_FILE = os.path.join(config.AUTO_DIR, "plan.json")
STATE_FILE = os.path.join(config.AUTO_DIR, "state.json")
LOG_FILE = os.path.join(config.AUTO_DIR, "log.csv")
SWITCH_FILE = os.path.join(config.AUTO_DIR, "switch.json")
STALE_DAYS = 4  # don't trade on a plan older than this (e.g. the evening run failed for days)


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(json.dumps(obj, indent=1) + "\n")


def load_state():
    s = load_json(STATE_FILE, {})
    for k in ("bought", "sold"):
        s.setdefault(k, {})
    s.setdefault("executed", None)
    return s


def paused():
    return bool(load_json(SWITCH_FILE, {}).get("paused"))


def client_from_env():
    k, s = os.environ.get("ALPACA_AUTO_KEY"), os.environ.get("ALPACA_AUTO_SECRET")
    return Alpaca(k, s, live=config.AUTO_LIVE) if k and s else None


def notify(text):
    try:
        from .notifier import _telegram
        return _telegram("🤖 Autopilot (practice account)\n" + text)
    except Exception as e:  # noqa: BLE001 - a message problem must never stop trading logic
        return f"telegram failed: {e}"


def log(action, ticker, dollars, price, reason, when=None):
    os.makedirs(config.AUTO_DIR, exist_ok=True)
    new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "action", "ticker", "dollars", "price", "reason"])
        w.writerow([when or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), action, ticker,
                    f"{dollars:.2f}" if dollars is not None else "", f"{price:.2f}" if price else "", reason])


def recently_sold(state, today, con=None):
    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=config.ROTATION_NO_REBUY_DAYS)).isoformat()
    out = {t for t, d in state["sold"].items() if d >= cutoff}
    if con is not None:
        try:
            out |= {r[0] for r in con.execute("SELECT sell FROM rotation_log WHERE asof>=?", (cutoff,))}
        except Exception:  # noqa: BLE001 - no rotation yet
            pass
    return out


def book_rows(positions, state):
    rows = []
    for p in positions:
        sym, mv, cost = p["symbol"], float(p["market_value"]), float(p["cost_basis"])
        rows.append({"position_id": f"{sym}-shares", "ticker": sym, "asset_type": "shares", "contracts": float(p["qty"]),
                     "entry_price": float(p["avg_entry_price"]), "mark": float(p["current_price"]), "value": mv,
                     "cost": cost, "pnl": mv - cost, "pnl_pct": (mv - cost) / cost * 100 if cost else None,
                     "status": "ok", "stop_price": None, "target_price": None, "dte": None,
                     "entry_date": state["bought"].get(sym), "action": "HOLD", "action_reason": ""})
    return rows


# ---------------------------------------------------------------- evening: plan
def plan(asof, bars, sentiment=None, client=None, db=None, plan_file=None):
    client = client or client_from_env()
    if client is None:
        return {"status": "off (add ALPACA_AUTO_KEY / ALPACA_AUTO_SECRET to turn on the practice autopilot)"}
    try:
        acct, positions = client.account(), client.positions()
    except Exception as e:  # noqa: BLE001
        return {"status": f"skipped: couldn't read the practice account ({e})"}
    state = load_state()
    rows = book_rows(positions, state)
    os.makedirs(config.AUTO_DIR, exist_ok=True)
    con = storage.connect(db or config.AUTO_DB)
    try:
        levels.apply(con, asof, rows, bars)
        rot = rotation.run(con, asof, rows, bars, sentiment)
        held = {r["ticker"] for r in rows}
        sells = {r["ticker"]: r["action_reason"] for r in rows if r["action"] == "SELL"}
        swap_buys = []
        for s in rot.get("suggestions") or []:
            if s["sell"] in held:
                sells.setdefault(s["sell"], s["reason"])
                swap_buys.append({"ticker": s["buy"], "rank": s["buy_rank"], "score": s["buy_score"],
                                  "reason": f"replaces {s['sell']}: {s['reason']}"})
        blocked = recently_sold(state, asof, con) | held | set(sells)
        buys = [b for b in swap_buys if b["ticker"] not in blocked]
        slots = config.AUTO_HOLDINGS - (len(held) - len(sells))
        buys = buys[:max(slots, 0)]
        taken = {b["ticker"] for b in buys}
        ranked = con.execute("SELECT ticker, rank, score FROM rotation_scores WHERE asof=? ORDER BY rank", (asof,)).fetchall()
        extra = [{"ticker": t, "rank": rk, "score": sc, "reason": f"rank #{rk} of {len(ranked)}, score {sc:.0f}"}
                 for t, rk, sc in ranked if sc >= config.ROTATION_MIN_SCORE and t not in blocked and t not in taken]
        fill = extra[:max(slots - len(buys), 0)]
        buys += fill
        taken |= {b["ticker"] for b in fill}
        reserve = [x for x in extra if x["ticker"] not in taken][:8]
        stops = {r["ticker"]: {"stop": r.get("stop_price"), "target": r.get("target_price"), "rule": r.get("stop_rule"),
                               "weak": bool(r.get("weak"))} for r in rows if r["ticker"] not in sells}
        equity, cash = float(acct.get("equity") or 0), float(acct.get("cash") or 0)
        totals = {"value": equity, "cost": sum(r["cost"] for r in rows) + cash, "pnl": sum(r["pnl"] for r in rows)}
        performance.run(con, asof, rows, totals, bars)
    finally:
        con.close()
    p = {"id": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "asof": asof,
         "equity": equity, "cash": cash, "paused": paused(),
         "sells": [{"ticker": t, "reason": why} for t, why in sells.items()], "buys": buys, "reserve": reserve,
         "stops": stops, "holdings": [{k: r.get(k) for k in ("ticker", "value", "pnl", "pnl_pct", "entry_price", "mark",
                                                              "stop_price", "target_price", "stop_rule", "weak", "action",
                                                              "entry_date", "prev_stop")} for r in rows]}
    save_json(plan_file or PLAN_FILE, p)
    notify(evening_text(p))
    return {"status": f"plan saved: {len(p['sells'])} sell(s), {len(p['buys'])} buy(s), {len(stops)} holding(s) kept",
            "plan": p}


def evening_text(p):
    first = None
    L = [f"Evening report {p['asof']} · account ${p['equity']:,.2f} (cash ${p['cash']:,.2f})"
         + (" · PAUSED" if p.get("paused") else ""), ""]
    for h in p["holdings"]:
        if h["ticker"] in {s["ticker"] for s in p["sells"]}:
            continue
        line = f"{'🟠' if h.get('weak') else '⚪'} {h['ticker']} {h['mark']:,.2f} ({(h.get('pnl_pct') or 0):+.1f}%)"
        if h.get("stop_price"):
            line += f" · stop {h['stop_price']:,.2f}"
            if h.get("prev_stop") and h["stop_price"] > h["prev_stop"] + 0.005:
                line += f" (raised from {h['prev_stop']:,.2f})"
        if h.get("target_price"):
            line += f" · target {h['target_price']:,.2f}"
        L.append(line + (" · WEAK" if h.get("weak") else ""))
    if not p["holdings"]:
        L.append("No holdings yet.")
    L.append("")
    if p["sells"] or p["buys"]:
        L.append("At the next market open I will:")
        L += [f"🔴 SELL {s['ticker']}: {s['reason'][:180]}" for s in p["sells"]]
        L += [f"🟢 BUY {b['ticker']} (20% of the account): {b['reason'][:180]}" for b in p["buys"]]
    else:
        L.append("No trades planned. I'll watch the stops and targets every 30 minutes while the market is open.")
    if p.get("reserve"):
        first = ", ".join(x["ticker"] for x in p["reserve"][:3])
        L.append(f"If a stock hits its stop, it's replaced by the next strongest: {first}.")
    return "\n".join(L)


# ---------------------------------------------------------------- market hours: execute
def wait_filled(client, order, seconds=45):
    oid = (order or {}).get("id")
    end = time.time() + seconds
    while oid and time.time() < end:
        o = client.order(oid)
        if o.get("status") == "filled":
            return o
        if o.get("status") in ("canceled", "rejected", "expired"):
            return o
        time.sleep(3)
    return client.order(oid) if oid else {}


def _price(o):
    try:
        return float(o.get("filled_avg_price") or 0) or None
    except (TypeError, ValueError):
        return None


def buy_one(client, state, today, queue, dollars, why_prefix, skip):
    """Buy the first stock in `queue` that works; returns (ticker, message) or (None, message)."""
    for b in queue:
        t = b["ticker"]
        if t in skip:
            continue
        try:
            o = wait_filled(client, client.buy(t, dollars))
        except AlpacaError as e:
            skip.add(t)
            log("SKIP", t, dollars, None, f"buy refused: {e}")
            notify(f"⚠️ Couldn't buy {t} (${dollars:,.2f}): {str(e)[:150]}. Trying the next stock on the list.")
            continue
        state["bought"][t] = today
        skip.add(t)
        log("BUY", t, dollars, _price(o), f"{why_prefix}{b.get('reason', '')}")
        return t, f"🟢 BUY {t} ${dollars:,.2f}" + (f" at {_price(o):,.2f}" if _price(o) else "") + f" ({b.get('reason', '')[:120]})"
    return None, "no stock from the plan could be bought"


def execute(client=None):
    if paused():
        return "paused (monitor/autotrade/switch.json)"
    client = client or client_from_env()
    if client is None:
        return "off (no ALPACA_AUTO_KEY / ALPACA_AUTO_SECRET)"
    clock = client.clock()
    if not clock.get("is_open"):
        return "market closed"
    p = load_json(PLAN_FILE, None)
    if not p:
        return "no plan yet (made by the evening monitor run)"
    state = load_state()
    today = (clock.get("timestamp") or "")[:10] or dt.date.today().isoformat()
    msgs = []
    max_order = None

    if state.get("executed") != p["id"]:
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(p["asof"])).days
        if age > STALE_DAYS:
            msgs.append(f"Plan from {p['asof']} is too old to trade on; waiting for a fresh one.")
        else:
            positions = {x["symbol"]: x for x in client.positions()}
            for s in p["sells"]:
                if s["ticker"] not in positions:
                    continue
                if state["bought"].get(s["ticker"]) == today:
                    continue  # never sell the same day it was bought
                o = wait_filled(client, client.close(s["ticker"]))
                state["sold"][s["ticker"]] = today
                val = float(positions[s["ticker"]]["market_value"])
                log("SELL", s["ticker"], val, _price(o), s["reason"])
                msgs.append(f"🔴 SELL {s['ticker']} (~${val:,.2f})" + (f" at {_price(o):,.2f}" if _price(o) else "")
                            + f": {s['reason'][:160]}")
            acct = client.account()
            equity, cash = float(acct["equity"]), float(acct["cash"])
            per, max_order = equity / config.AUTO_HOLDINGS, equity * config.AUTO_MAX_ORDER_PCT / 100
            held_now = {x["symbol"] for x in client.positions()}
            skip = held_now | recently_sold(state, today)
            for _ in range(len(p["buys"])):
                dollars = round(min(per, max_order, cash - 1), 2)
                if dollars < 1:
                    msgs.append("Not enough cash left for another buy.")
                    break
                t, m = buy_one(client, state, today, p["buys"] + p["reserve"], dollars, "", skip)
                msgs.append(m)
                if not t:
                    break
                cash -= dollars
        state["executed"] = p["id"]

    # stop / target watch, every round while the market is open
    held = client.positions()
    names = {x["symbol"] for x in held}
    for x in held:
        t, price, avg = x["symbol"], float(x["current_price"]), float(x["avg_entry_price"])
        if state["bought"].get(t) == today:
            continue  # bought today: no same-day sale
        lv = p["stops"].get(t) or {}
        stop = lv.get("stop") or avg * (1 - config.MAX_LOSS_PCT / 100)
        target = lv.get("target")
        hit = "stop" if price <= stop else "target" if target and price >= target else None
        if not hit:
            continue
        o = wait_filled(client, client.close(t))
        state["sold"][t] = today
        names.discard(t)
        val = float(x["market_value"])
        why = (f"price {price:,.2f} reached its {'stop' if hit == 'stop' else 'target'} "
               f"{stop if hit == 'stop' else target:,.2f}" + (f" ({lv.get('rule')})" if hit == "stop" and lv.get("rule") else ""))
        log("SELL", t, val, _price(o), why)
        acct = client.account()
        equity, cash = float(acct["equity"]), float(acct["cash"])
        dollars = round(min(val, equity * config.AUTO_MAX_ORDER_PCT / 100, cash - 1), 2)
        skip = names | recently_sold(state, today)
        nt, m = buy_one(client, state, today, p["reserve"], dollars, f"replaces {t} ({hit} hit): ", skip) \
            if dollars >= 1 else (None, "not enough cash to replace it")
        if nt:
            names.add(nt)
        msgs.append(f"{'🛑 STOP' if hit == 'stop' else '🎯 TARGET'} HIT: sold {t} (~${val:,.2f}), {why}. -> {m}")
    save_json(STATE_FILE, state)
    if msgs:
        acct = client.account()
        notify("\n".join(msgs) + f"\n\nAccount now ${float(acct['equity']):,.2f} (cash ${float(acct['cash']):,.2f}).")
    return "; ".join(msgs) or "nothing to do"


def main(argv=None):
    cmd = (argv or sys.argv[1:] or ["execute"])[0]
    if cmd == "execute":
        try:
            print("Autopilot:", execute())
        except Exception as e:  # noqa: BLE001 - never break the bot loop
            print(f"Autopilot error (will retry next round): {e}")
    elif cmd == "status":
        print(json.dumps({"paused": paused(), "plan": load_json(PLAN_FILE, None), "state": load_state()}, indent=1))


if __name__ == "__main__":
    main()
