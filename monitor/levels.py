"""Automatic stop and target for positions without levels of their own.

Common trader risk management:
  Stop    a trailing "Chandelier" stop: the highest close since the monitor started tracking the position,
          minus 3 x ATR (the average true range, i.e. the stock's typical daily move, over ~22 days).
          Jumpy stocks get more room than steady funds, and the stop only ever moves UP as the price rises.
  Target  2-to-1 reward to risk: the starting price plus twice the starting distance to the stop.
Levels start from the price on the first tracked day, not the purchase price, because a loss already
taken can't be undone; the stop limits further losses from here. Set stop_price / target_price in
positions.json to override these with your own numbers.
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


def apply(con, asof, rows, bars):
    """Fill in automatic levels for shares without their own, then refresh each row's plan label."""
    con.executescript(SCHEMA)
    out = []
    for r in rows:
        own = r.get("stop_price") is not None or r.get("target_price") is not None
        b = bars.get(r["ticker"])
        if not config.AUTO_LEVELS or own or r["asset_type"] != "shares" or not b:
            continue
        a = atr(b)
        if not a:
            continue
        close = b[-1][1]
        row = con.execute("SELECT baseline_date, baseline_price, highest_close, stop, target FROM auto_levels "
                          "WHERE ticker=?", (r["ticker"],)).fetchone()
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
        con.execute("INSERT OR REPLACE INTO auto_levels VALUES (?,?,?,?,?,?,?,?)",
                    (r["ticker"], base_date, base, highest, stop, target, a, asof))
        mark = r.get("mark")
        r.update(stop_price=round(stop, 2), target_price=round(target, 2), level_ref=base, levels_auto=True)
        if mark is not None:
            r["progress_target"] = (mark - base) / (target - base) * 100 if target != base else None
            r["progress_stop"] = (highest - mark) / (highest - stop) * 100 if highest != stop else None
        r["action"], r["action_reason"] = plan.for_position(r)
        r["action_reason"] += " (auto levels)"
        out.append({"ticker": r["ticker"], "stop": stop, "target": target, "atr": a, "base": base,
                    "highest": highest, "since": base_date})
    con.commit()
    return out
