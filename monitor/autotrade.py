"""Autopilot (practice): runs the strategy by itself in a separate Alpaca PAPER account. No real money.

Same rules as the monitor uses for your IB book:
  - 5 stocks, equal weight (20% each), bought from the top of the ranking (score 80+)
  - 4.5% trailing stop (4.5% below the highest price since bought, only moves up), 2-to-1 target (levels.py)
  - a stop or target hit -> sell right away and buy the strongest stock not owned
  - swaps when a clearly stronger stock appears (each stock every 2 business days at most); WEAK / LOSING holdings first in line (rotation.py)
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

import collections

from . import config, earnings, levels, performance, regime, rotation, sectors, storage
from .alpaca import Alpaca, AlpacaError

PLAN_FILE = os.path.join(config.AUTO_DIR, "plan.json")
STATE_FILE = os.path.join(config.AUTO_DIR, "state.json")
LOG_FILE = os.path.join(config.AUTO_DIR, "log.csv")
SWITCH_FILE = os.path.join(config.AUTO_DIR, "switch.json")
STALE_DAYS = 4  # don't trade on a plan older than this (e.g. the evening run failed for days)
LABEL = "🤖 Autopilot (practice account)"
MAX_ORDER_PCT = config.AUTO_MAX_ORDER_PCT


def configure(plan_file=None, state_file=None, log_file=None, switch_file=None, label=None, max_order_pct=None):
    """Point the engine at another account's files (used by ib_trader on the Mac)."""
    g = globals()
    for name, val in (("PLAN_FILE", plan_file), ("STATE_FILE", state_file), ("LOG_FILE", log_file),
                      ("SWITCH_FILE", switch_file), ("LABEL", label), ("MAX_ORDER_PCT", max_order_pct)):
        if val is not None:
            g[name] = val


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
        return _telegram(LABEL + "\n" + text)
    except Exception as e:  # noqa: BLE001 - a message problem must never stop trading logic
        return f"telegram failed: {e}"


def log(action, ticker, dollars, price, reason, when=None):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
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
        weather = regime.check(con, asof, bars)
        rot = rotation.run(con, asof, rows, bars, sentiment,
                           earnings.make_blocker(asof) if config.EARNINGS_GUARD else None, weather["storm"])
        rot["weather"] = weather
        equity, cash = float(acct.get("equity") or 0), float(acct.get("cash") or 0)
        p = build_plan(asof, rows, rot, con, equity, cash, state)
        totals = {"value": equity, "cost": sum(r["cost"] for r in rows) + cash, "pnl": sum(r["pnl"] for r in rows)}
        performance.run(con, asof, rows, totals, bars)
    finally:
        con.close()
    p["paused"] = paused()
    save_json(plan_file or PLAN_FILE, p)
    notify(evening_text(p))
    return {"status": f"plan saved: {len(p['sells'])} sell(s), {len(p['buys'])} buy(s), {len(p['stops'])} holding(s) kept",
            "plan": p}


def build_plan(asof, rows, rot, con, equity, cash, state=None, holdings=None):
    """The plan from valued rows (levels + rotation already applied). Same format for the autopilot and IB."""
    state = state or {"bought": {}, "sold": {}}
    holdings = holdings or config.AUTO_HOLDINGS
    safe, storm = config.SAFE_FUND, bool(rot.get("storm"))
    held_all = {r["ticker"] for r in rows}
    held = held_all - {safe}  # the parking fund isn't one of the 5 stock slots
    value = {r["ticker"]: r.get("value") or 0 for r in rows}
    sells = {r["ticker"]: r["action_reason"] for r in rows if r.get("action") == "SELL" and r["ticker"] != safe}
    if safe in held_all and not storm:
        sells[safe] = "fair weather again (S&P 500 back above its 200-day average): parked money goes back into stocks"
    swap_buys = []
    for s in rot.get("suggestions") or []:
        if s["sell"] in held:
            sells.setdefault(s["sell"], s["reason"])
            swap_buys.append({"ticker": s["buy"], "rank": s["buy_rank"], "score": s["buy_score"], "replaces": s["sell"],
                              "reason": f"replaces {s['sell']}: {s['reason']}"})
    soon = rot.get("earnings_soon") or {}
    blocked = recently_sold(state, asof, con) | held | set(sells) | set(soon)
    buys = [b for b in swap_buys if b["ticker"] not in blocked]
    slots = holdings - (len(held) - len([t for t in sells if t != safe]))
    buys = buys[:max(slots, 0)]
    taken = {b["ticker"] for b in buys}
    rows_ranked = con.execute("SELECT ticker, rank, score, uptrend, vol FROM rotation_scores WHERE asof=? ORDER BY rank",
                              (asof,)).fetchall()
    vols = sorted(v for *_, v in rows_ranked if v)
    ref = vols[len(vols) // 2] if vols else None  # the typical stock's daily move

    def size(v):  # 1.0 = an equal share; steadier stocks more, jumpy ones less
        if not config.VOL_SIZING or not v or not ref:
            return 1.0
        return round(min(config.VOL_SIZE_MAX, max(config.VOL_SIZE_MIN, ref / v)), 2)

    ranked = [(t, rk, sc, sz) for t, rk, sc, up, v in rows_ranked
              if (up or not config.UPTREND_REQUIRED) and (sz := size(v))]
    extra = [] if storm else [
        {"ticker": t, "rank": rk, "score": sc, "size": sz,
         "reason": f"rank #{rk} of {len(rows_ranked)}, score {sc:.0f}, uptrend"
                   + (f", {sz:.1f}x size ({'steadier' if sz > 1 else 'jumpier'} than most)" if sz != 1 else "")}
        for t, rk, sc, sz in ranked if sc >= config.ROTATION_MIN_SCORE and t not in blocked and t not in taken]
    # fill empty slots only with money that's really there: cash + sales that no swap buy uses
    per = equity / holdings if holdings else 0
    funded = {b["replaces"] for b in buys}
    free = cash + sum(value.get(t, 0) for t in sells if t not in funded)
    n_fill = min(max(slots - len(buys), 0), int(free // (per * 0.5)) if per > 0 else 0)
    counts = collections.Counter(sectors.sector_of(t) for t in held if t not in sells)  # stocks only
    for b in buys:
        counts[sectors.sector_of(b["ticker"])] += 1
    fill = []
    for x in extra:  # fill empty slots without going over the sector limit
        if len(fill) >= n_fill:
            break
        sec = sectors.sector_of(x["ticker"])
        if not sectors.over_limit(sec, counts[sec] + 1):
            fill.append(x)
            counts[sec] += 1
    buys += fill
    taken |= {b["ticker"] for b in fill}
    reserve = [x for x in extra if x["ticker"] not in taken][:8]
    stops = {r["ticker"]: {"stop": r.get("stop_price"), "target": r.get("target_price"), "rule": r.get("stop_rule"),
                           "weak": bool(r.get("weak"))} for r in rows if r["ticker"] not in sells}
    sold_recently = recently_sold(state, asof, con)
    deposit = [] if storm else [
        {"ticker": t, "rank": rk, "score": sc, "size": sz, "sector": sectors.sector_of(t),
         "reason": f"rank #{rk} of {len(rows_ranked)}, score {sc:.0f}"}
        for t, rk, sc, sz in ranked if sc >= config.ROTATION_MIN_SCORE and t not in sold_recently and t not in soon][:40]
    return {"id": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "asof": asof,
            "equity": equity, "cash": cash, "sells": [{"ticker": t, "reason": why} for t, why in sells.items()],
            "buys": buys, "reserve": reserve, "stops": stops, "deposit_candidates": deposit, "earnings_soon": soon,
            "storm": storm, "weather": (rot.get("weather") or {}).get("text"),
            "holdings": [{k: r.get(k) for k in ("ticker", "value", "pnl", "pnl_pct", "entry_price", "mark", "stop_price",
                                                "target_price", "stop_rule", "weak", "action", "entry_date", "prev_stop")}
                         for r in rows]}


def evening_text(p):
    first = None
    L = [f"Evening report {p['asof']} · account ${p['equity']:,.2f} (cash ${p['cash']:,.2f})"
         + (" · PAUSED" if p.get("paused") else ""), ("⛈ " if p.get("storm") else "🌤 ") + (p.get("weather") or ""), ""]
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
    counts = collections.Counter(sectors.sector_of(x["symbol"]) for x in client.positions())
    for b in queue:
        t = b["ticker"]
        if t in skip:
            continue
        if sectors.over_limit(sectors.sector_of(t), counts[sectors.sector_of(t)] + 1):
            continue  # would put more than MAX_PER_SECTOR stocks in one sector
        try:
            o = wait_filled(client, client.buy(t, dollars))
        except AlpacaError as e:
            skip.add(t)
            log("SKIP", t, dollars, None, f"buy refused: {e}")
            notify(f"⚠️ Couldn't buy {t} (${dollars:,.2f}): {str(e)[:150]}. Trying the next stock on the list.")
            continue
        state["bought"][t] = today
        state.setdefault("highs", {})[t] = _price(o) or 0  # the trailing stop starts from the purchase price
        skip.add(t)
        log("BUY", t, dollars, _price(o), f"{why_prefix}{b.get('reason', '')}")
        return t, f"🟢 BUY {t} ${dollars:,.2f}" + (f" at {_price(o):,.2f}" if _price(o) else "") + f" ({b.get('reason', '')[:120]})"
    return None, "no stock from the plan could be bought (sector limit, recent sale or refused order)"


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
            proceeds = {}
            for s in p["sells"]:
                if s["ticker"] not in positions:
                    continue
                if state["bought"].get(s["ticker"]) == today:
                    continue  # never sell the same day it was bought
                o = wait_filled(client, client.close(s["ticker"]))
                state["sold"][s["ticker"]] = today
                val = float(positions[s["ticker"]]["market_value"])
                fill = _price(o)
                if fill:
                    val = fill * abs(float(positions[s["ticker"]]["qty"]))
                proceeds[s["ticker"]] = val
                log("SELL", s["ticker"], val, fill, s["reason"])
                msgs.append(f"🔴 SELL {s['ticker']} (~${val:,.2f})" + (f" at {fill:,.2f}" if fill else "")
                            + f": {s['reason'][:160]}")
            acct = client.account()
            equity, cash = float(acct["equity"]), float(acct["cash"])
            per, max_order = equity / config.AUTO_HOLDINGS, equity * MAX_ORDER_PCT / 100
            held_now = {x["symbol"] for x in client.positions()}
            skip = held_now | recently_sold(state, today)
            paired_need = sum(proceeds[b["replaces"]] for b in p["buys"] if b.get("replaces") in proceeds)
            fill_want = sum(per * b.get("size", 1.0) for b in p["buys"] if not b.get("replaces"))
            # if the cash can't cover every new stock at full size, shrink them all alike (keeps their proportions)
            scale = min(1.0, max(cash - 1 - paired_need, 0) / fill_want) if fill_want else 1.0
            for b in p["buys"]:
                paired = b.get("replaces")
                if paired and paired not in proceeds:
                    continue  # its sale didn't happen (already sold, or bought today): don't buy without the money
                want = proceeds[paired] if paired else per * b.get("size", 1.0) * scale
                dollars = round(min(want, max_order, equity * config.MAX_POSITION_PCT / 100, cash - 1), 2)
                if dollars < config.AUTO_MIN_BUY_USD:
                    if paired:
                        msgs.append(f"Not enough cash to buy {b['ticker']} (${dollars:,.2f} available).")
                    continue
                t, m = buy_one(client, state, today, [b] + p["reserve"], dollars, "", skip)
                msgs.append(m)
                if t:
                    cash -= dollars
        state["executed"] = p["id"]

    # stop / target watch, every round while the market is open
    held = client.positions()
    names = {x["symbol"] for x in held}
    for x in held:
        t, price, avg = x["symbol"], float(x["current_price"]), float(x["avg_entry_price"])
        if state["bought"].get(t) == today or t == config.SAFE_FUND:
            continue  # bought today: no same-day sale; the parking fund has no stop
        lv = p["stops"].get(t) or {}
        highs = state.setdefault("highs", {})
        highs[t] = max(highs.get(t, 0), price, avg if state["bought"].get(t) else 0)
        trail = highs[t] * (1 - config.TRAIL_PCT / 100)   # trails during the day too; only moves up
        stop = max(lv.get("stop") or 0, avg * (1 - config.TRAIL_PCT / 100), trail)
        target = lv.get("target")
        hit = "stop" if price <= stop else "target" if target and price >= target else None
        if not hit:
            continue
        peak = highs.get(t, price)
        o = wait_filled(client, client.close(t))
        state["sold"][t] = today
        highs.pop(t, None)
        names.discard(t)
        val = float(x["market_value"])
        why = (f"price {price:,.2f} reached its {'stop' if hit == 'stop' else 'target'} "
               f"{stop if hit == 'stop' else target:,.2f}"
               + (f" ({config.TRAIL_PCT:g}% below its high of {peak:,.2f})" if hit == "stop" else ""))
        log("SELL", t, val, _price(o), why)
        acct = client.account()
        equity, cash = float(acct["equity"]), float(acct["cash"])
        dollars = round(min(val, equity * MAX_ORDER_PCT / 100, cash - 1), 2)
        skip = names | recently_sold(state, today)
        queue = ([{"ticker": config.SAFE_FUND, "reason": "market storm: parked until the S&P 500 recovers"}]
                 if p.get("storm") else p["reserve"])
        nt, m = buy_one(client, state, today, queue, dollars, f"replaces {t} ({hit} hit): ", skip - {config.SAFE_FUND}) \
            if dollars >= config.AUTO_MIN_BUY_USD else (None, "not enough cash to replace it")
        if nt:
            names.add(nt)
        msgs.append(f"{'🛑 STOP' if hit == 'stop' else '🎯 TARGET'} HIT: sold {t} (~${val:,.2f}), {why}. -> {m}")
    if (dt.date.fromisoformat(today) - dt.date.fromisoformat(p["asof"])).days <= STALE_DAYS:
        m = invest_new_cash(client, p, state, today)
        if m:
            msgs.append(m)
    save_json(STATE_FILE, state)
    if msgs:
        acct = client.account()
        notify("\n".join(msgs) + f"\n\nAccount now ${float(acct['equity']):,.2f} (cash ${float(acct['cash']):,.2f}).")
    return "; ".join(msgs) or "nothing to do"


def pick_for_cash(p, held, blocked, n):
    """Up to n stocks from the plan's ranked list: new sectors first, then any; SPY if none qualifies."""
    held_sectors = {sectors.sector_of(t) for t in held}
    cands = [c for c in p.get("deposit_candidates") or [] if c["ticker"] not in held and c["ticker"] not in blocked]
    chosen, used = [], set(held_sectors)
    for c in cands:  # 1st pass: a sector the portfolio doesn't have yet
        if len(chosen) < n and c["sector"] not in used:
            chosen.append({**c, "why": f"new sector for you: {c['sector']}"})
            used.add(c["sector"])
    for c in cands:  # 2nd pass: still room -> strongest remaining, any sector
        if len(chosen) < n and c["ticker"] not in {x["ticker"] for x in chosen}:
            chosen.append({**c, "why": f"strongest left ({c['sector']}, already owned)"})
    if not chosen:
        chosen = [{"ticker": config.DEPOSIT_FALLBACK, "sector": "Broad market", "reason": "S&P 500 fund",
                   "why": "no stock scores 80+ today, so it tracks the S&P 500 instead of sitting in cash"}]
    return chosen


def invest_new_cash(client, p, state, today):
    """New money (a deposit, or cash no planned trade used) is invested the same day, spreading across sectors."""
    acct = client.account()
    equity, cash = float(acct["equity"]), float(acct["cash"])
    if cash < config.DEPOSIT_MIN_USD:
        return None
    tries = state.setdefault("deposit_tries", {})
    if tries.get(today, 0) >= config.DEPOSIT_MAX_TRIES_PER_DAY:
        return None
    done = tries.get(today, 0)
    tries.clear()  # keep only today's count
    tries[today] = done + 1
    positions = client.positions()
    held = {x["symbol"] for x in positions}
    values = [float(x["market_value"]) for x in positions if float(x["market_value"]) > 0]
    size = sum(values) / len(values) if values else equity / config.AUTO_HOLDINGS
    n = max(1, min(config.DEPOSIT_MAX_STOCKS, round(cash / size) if size > 0 else 1))
    spend = cash - 1
    each = round(min(spend / n, equity * MAX_ORDER_PCT / 100), 2)
    if each < config.AUTO_MIN_BUY_USD:
        return None
    if p.get("storm"):
        amount = round(min(spend, equity * config.MAX_POSITION_PCT / 100 if held - {config.SAFE_FUND} else spend), 2)
        t, m = buy_one(client, state, today, [{"ticker": config.SAFE_FUND, "reason": "market storm"}], amount,
                       "new cash, market storm: ", set())
        return (f"💵 New cash ${cash:,.2f}: the market is in a storm (S&P 500 below its 200-day average), so it waits "
                f"in {config.SAFE_FUND} (Treasury bills, ~4% a year) until the market recovers.\n{m}") if t else None
    blocked = recently_sold(state, today) | {t for t, d in state["bought"].items() if d == today}
    picks = pick_for_cash(p, held, blocked, n)
    total_size = sum(c.get("size", 1.0) for c in picks) or 1.0
    lines, skip = [], set(held) | blocked
    for c in picks:
        amount = round(min(spend * c.get("size", 1.0) / total_size, equity * MAX_ORDER_PCT / 100,
                           equity * config.MAX_POSITION_PCT / 100), 2)
        if amount < config.AUTO_MIN_BUY_USD:
            continue
        queue = [c] + [x for x in p.get("deposit_candidates") or [] if x["ticker"] != c["ticker"]]
        t, m = buy_one(client, state, today, queue, amount, "new cash: ", skip)
        if t:
            lines.append(f"{m} - {c['why']}")
    if not lines:
        return f"💵 Found ${cash:,.2f} of new cash but couldn't buy anything yet; I'll retry (max {config.DEPOSIT_MAX_TRIES_PER_DAY} times a day)."
    return (f"💵 New cash found: ${cash:,.2f}. Invested in {len(lines)} stock(s), spreading across sectors "
            "(steadier stocks get more, jumpy ones less) with the goal of beating the S&P 500:\n" + "\n".join(lines))


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
