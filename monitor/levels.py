"""Automatic stop and target for positions without levels of their own.

  Stop    a 4.5% TRAILING STOP (config.TRAIL_PCT): it starts 4.5% below the price you paid and always sits 4.5%
          below the highest close since you bought, so it only ever moves UP. Example: bought at 147.71 ->
          stop 141.06; the stock closes at 155.10 -> stop 148.12, above what you paid. The Mac also trails it
          during the day from the prices it checks every 2 minutes. A hit = sell and swap into the strongest stock.
  Breakeven  once a stock has been 10% above what you paid, the stop is at least your buy price (with a 4.5%
          trail it's already above that).
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


def floors(stop, entry, highest):
    """The stop: TRAIL_PCT below the highest price since you bought (never below TRAIL_PCT under your buy price),
    and never lower than it already was. -> (stop, rule that set it)."""
    peak = max(highest or 0, entry or 0)
    trail = peak * (1 - config.TRAIL_PCT / 100)
    stop = max(stop or 0, trail)
    if entry and highest >= entry * (1 + config.BREAKEVEN_AFTER_PCT / 100):
        stop = max(stop, entry)
    if peak and abs(stop - trail) < 0.005:
        where = "your buy price" if entry and peak == entry else f"the highest close since you bought, {peak:,.2f}"
        return stop, f"{config.TRAIL_PCT:g}% trailing stop ({config.TRAIL_PCT:g}% below {where})"
    if entry and abs(stop - entry) < 0.005:
        return stop, f"breakeven stop (was up {config.BREAKEVEN_AFTER_PCT:g}%+, so no loss allowed)"
    return stop, f"{config.TRAIL_PCT:g}% trailing stop (kept from an earlier high; stops never move down)"


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


def apply(con, asof, rows, bars):
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
        if row is None:
            base_date = r.get("entry_date") if r.get("entry_date") and r["entry_date"] <= asof else asof
            since = [x[1] for x in b if x[0] >= base_date] or [close]
            base, highest = close, max(since)
            stop = 0.0
            target = close + config.REWARD_RISK * config.ATR_STOP_MULT * a
        else:
            base_date, base, highest, stop, target = row
            since = [x[1] for x in b if x[0] >= base_date] or [close]
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
