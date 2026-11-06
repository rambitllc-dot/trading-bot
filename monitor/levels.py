"""Automatic stop and target for positions without levels of their own.

Common trader risk management:
  Stop    a trailing "Chandelier" stop: the highest close since the monitor started tracking the position,
          minus 3 x ATR (the average true range, i.e. the stock's typical daily move, over ~22 days).
          Jumpy stocks get more room than steady funds, and the stop only ever moves UP as the price rises.
  Target  2-to-1 reward to risk: the starting price plus twice the starting distance to the stop.
Two floors are added under the trailing stop (the highest of the three wins, and it never moves down):
  Loss cap    the stop is never more than MAX_LOSS_PCT (6%) below what you paid.
  Breakeven   once the stock has closed BREAKEVEN_AFTER_PCT (10%) above what you paid, the stop rises to your
              buy price, so a winner can't turn into a loss.
A position already down more than the cap shows SELL right away: that's the cut-losses rule.
The target stays at 2-to-1 of the stock's normal swing (3 x ATR), measured from the first tracked day.
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
    """Raise the stop to the loss cap and, after a 10% gain, to breakeven. -> (stop, rule that set it)."""
    rule = "trailing stop (3 x typical daily move below the highest close)"
    if entry:
        cap = entry * (1 - config.MAX_LOSS_PCT / 100)
        if cap > stop:
            stop, rule = cap, f"{config.MAX_LOSS_PCT:g}% max-loss stop"
        if highest >= entry * (1 + config.BREAKEVEN_AFTER_PCT / 100) and entry > stop:
            stop, rule = entry, f"breakeven stop (up {config.BREAKEVEN_AFTER_PCT:g}%+ at its high, so no loss allowed)"
    return stop, rule


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
            base, highest = close, close
            stop = close - config.ATR_STOP_MULT * a
            target = close + config.REWARD_RISK * (close - stop)
            base_date = asof
        else:
            base_date, base, highest, stop, target = row
            since = [x[1] for x in b if x[0] >= base_date] or [close]
            highest = max(highest, max(since))
            stop = max(stop, highest - config.ATR_STOP_MULT * a)  # trailing: only ever moves up
        stop, rule = floors(stop, r.get("entry_price"), highest)
        con.execute("INSERT OR REPLACE INTO auto_levels VALUES (?,?,?,?,?,?,?,?)",
                    (r["ticker"], base_date, base, highest, stop, target, a, asof))
        mark = r.get("mark")
        r.update(stop_price=round(stop, 2), target_price=round(target, 2), level_ref=base, levels_auto=True)
        if mark is not None:
            r["progress_target"] = (mark - base) / (target - base) * 100 if target != base else None
            r["progress_stop"] = (highest - mark) / (highest - stop) * 100 if highest != stop else None
        r["stop_rule"], r["prev_stop"] = rule, prev_stop
        r["action"], r["action_reason"] = plan.for_position(r)
        r["action_reason"] += f" (stop: {rule})" if "stop" in r["action_reason"] else " (auto levels)"
        out.append({"ticker": r["ticker"], "stop": stop, "target": target, "atr": a, "base": base,
                    "highest": highest, "since": base_date, "rule": rule, "prev_stop": prev_stop})
    con.commit()
    return out
