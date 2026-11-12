"""Automatic stop and target for positions without levels of their own.

  Stop    a 4.5% TRAILING STOP (config.TRAIL_PCT): it starts 4.5% below the price you paid and always sits 4.5%
          below the highest close since you bought, so it only ever moves UP. Example: bought at 147.71 ->
          stop 141.06; the stock closes at 155.10 -> stop 148.12, above what you paid. The Mac also trails it
          during the day from the prices it checks every 2 minutes. A hit = sell and swap into the strongest stock.
  Profit ladder  the further a stock has risen, the closer the stop follows: from +8% above your buy price it
          trails 3% below the high, from +15% 2% (config.PROFIT_LADDER).
  Profit lock  once a stock has been 3% above what you paid, the stop is never below your buy price
          (config.LOCK_AFTER_PCT), so a winner can't turn into a loss.
  Target  2-to-1 of the stock's normal swing: the starting price plus 2 x (3 x ATR, its typical daily move).
A position already down more than 4.5% from its high shows SELL right away: that's the cut-losses rule.
WEAKENING: any stock (also with your own levels) whose last close is below its 50-day average is flagged;
it often shows a top-ranked stock rolling over before the stop is hit. It moves to the front of the swap line.
Set stop_price / target_price in positions.json to override the automatic levels with your own numbers.
"""
from . import config, plan

SCHEMA = """
CREATE TABLE IF NOT EXISTS auto_levels (
    ticker TEXT PRIMARY KEY, baseline_date TEXT, baseline_price REAL, highest_close REAL, stop REAL,
    target REAL, atr REAL, updated TEXT);
"""


def atr(bars, n=None):
    n = n or config.ATR_PERIOD
    if len(bars) < n + 1:
        return None
    trs = []
    for i in range(len(bars) - n, len(bars)):
        c_prev, high = bars[i - 1][1], bars[i][2]
        low = bars[i][4] if len(bars[i]) > 4 else bars[i][1]
        trs.append(max(high - low, abs(high - c_prev), abs(low - c_prev)))
    return sum(trs) / n


def trail_pct(entry, peak):
    """How far below the high the stop sits: TRAIL_PCT, tighter as the gain grows (the profit ladder)."""
    gain = (peak / entry - 1) * 100 if entry and peak else 0
    for at, pct in config.PROFIT_LADDER:
        if gain >= at - 1e-9:
            return pct
    return config.TRAIL_PCT


def stop_for(entry, peak):
    """Stop from the buy price and the highest price since: trailing (laddered) and the profit lock.
    -> (stop, rule)."""
    peak = max(peak or 0, entry or 0)
    pct = trail_pct(entry, peak)
    trail = peak * (1 - pct / 100)
    gain = (peak / entry - 1) * 100 if entry else 0
    lock = entry * (1 + config.LOCK_AT_PCT / 100) if entry and gain >= config.LOCK_AFTER_PCT - 1e-9 else 0
    if lock > trail:
        return lock, (f"profit lock (was up {config.LOCK_AFTER_PCT:g}%+, so it can't turn into a loss: "
                      f"stop at your buy price)" if not config.LOCK_AT_PCT else
                      f"profit lock (was up {config.LOCK_AFTER_PCT:g}%+, stop {config.LOCK_AT_PCT:+g}%)")
    where = "your buy price" if entry and peak == entry else f"the highest price since you bought, {peak:,.2f}"
    ladder = f", tighter because it was up {gain:.0f}%" if pct < config.TRAIL_PCT else ""
    return trail, f"{pct:g}% trailing stop ({pct:g}% below {where}{ladder})"


def floors(stop, entry, highest):
    """The stop: trailing below the highest price since you bought (see stop_for), never lower than it already
    was. -> (stop, rule that set it)."""
    new, rule = stop_for(entry, highest)
    if stop and stop > new + 0.005:
        return stop, "trailing stop (kept from an earlier high; stops never move down)"
    return max(stop or 0, new), rule


def weakness(r, b):
    """Flag a close below the 50-day average."""
    n = config.WEAK_MA_DAYS
    if r["asset_type"] != "shares" or not b or len(b) < n:
        return
    ma = sum(x[1] for x in b[-n:]) / n
    r["ma50"] = round(ma, 2)
    r["weak"] = b[-1][1] < ma
    if r["weak"]:
        r["weak_text"] = f"WEAKENING: closed {b[-1][1]:,.2f}, below its {n}-day average {ma:,.2f}"


def settled(bars, asof, now=None):
    """Only daily bars whose close is final. During market hours (and shortly after), the price feed's row for
    today can be incomplete or still show yesterday's close, so it must not set a new high."""
    import datetime as dt
    from zoneinfo import ZoneInfo
    now = now or dt.datetime.now(ZoneInfo("America/New_York"))
    today = now.date().isoformat()
    if asof != today or now.time() >= dt.time(16, 15):
        return bars  # an evening run, or a run for another day: all closes are final
    return [x for x in bars if x[0] < today]


def apply(con, asof, rows, bars, now=None):
    """Fill in automatic levels for shares without their own, then refresh each row's plan label."""
    con.executescript(SCHEMA)
    out = []
    for r in rows:
        own = r.get("stop_price") is not None or r.get("target_price") is not None
        b = bars.get(r["ticker"])
        weakness(r, b)
        if not config.AUTO_LEVELS or own or r["asset_type"] != "shares" or not b:
            continue
        a = atr(b)
        if not a:
            continue
        close = b[-1][1]
        row = con.execute("SELECT baseline_date, baseline_price, highest_close, stop, target FROM auto_levels "
                          "WHERE ticker=?", (r["ticker"],)).fetchone()
        if row is not None and r.get("entry_date") and row[0] < r["entry_date"]:
            row = None  # sold and bought again later: start fresh levels for the new purchase
        prev_stop = row[3] if row is not None else None
        final = settled(b, asof, now)  # highs only from final closes
        if row is None:
            base_date = r.get("entry_date") if r.get("entry_date") and r["entry_date"] <= asof else asof
            since = ([x[1] for x in final if x[0] >= base_date]
                     or [close if final is b else min(close, r.get("entry_price") or close)])
            base, highest = close, max(since)
            stop = 0.0
            target = close + config.REWARD_RISK * config.ATR_STOP_MULT * a
        else:
            base_date, base, highest, stop, target = row
            since = [x[1] for x in final if x[0] >= base_date] or [close if final is b else highest]
            highest = max(highest, max(since))
        stop, rule = floors(stop, r.get("entry_price"), highest)
        con.execute("INSERT OR REPLACE INTO auto_levels VALUES (?,?,?,?,?,?,?,?)",
                    (r["ticker"], base_date, base, highest, stop, target, a, asof))
        mark = r.get("mark")
        r.update(stop_price=round(stop, 2), target_price=round(target, 2), level_ref=base, levels_auto=True)
        if mark is not None:
            r["progress_target"] = (mark - base) / (target - base) * 100 if target != base else None
            r["progress_stop"] = (highest - mark) / (highest - stop) * 100 if highest != stop else None
        r["stop_rule"], r["prev_stop"] = rule, prev_stop
        r["peak"] = round(max(highest, r.get("entry_price") or 0), 2)  # the high the trailing stop follows
        r["action"], r["action_reason"] = plan.for_position(r)
        r["action_reason"] += f" (stop: {rule})" if "stop" in r["action_reason"] else " (auto levels)"
        out.append({"ticker": r["ticker"], "stop": stop, "target": target, "atr": a, "base": base,
                    "highest": highest, "since": base_date, "rule": rule, "prev_stop": prev_stop})
    con.commit()
    return out
