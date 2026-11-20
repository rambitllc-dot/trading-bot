"""Market weather: is the S&P 500 (SPY) above or below its 200-day average?

Storm (money in SGOV) = SPY closed at or below its 200-day average (+SWITCH_OUT_ABOVE_PCT%) SWITCH_DAYS days in a row.
Fair (money in the S&P 500) = SPY closed at least SWITCH_IN_ABOVE_PCT% above the average SWITCH_DAYS days in a row.
In between, the previous state is kept, so one stray day doesn't flip it back and forth.
"""
from . import config

SCHEMA = "CREATE TABLE IF NOT EXISTS market_weather (asof TEXT PRIMARY KEY, storm INTEGER, spy REAL, ma200 REAL);"


def check(con, asof, bars):
    out = {"storm": False, "spy": None, "ma200": None, "text": "market weather unknown (no SPY data)"}
    if not config.WEATHER_SWITCH:
        out["text"] = "market-weather switch is off"
        return out
    spy = bars.get("SPY") or []
    closes = [b[1] for b in spy]
    n = config.SWITCH_DAYS
    if len(closes) < 200 + n:
        return out
    mas = [sum(closes[len(closes) - k - 200:len(closes) - k]) / 200 for k in range(n)]  # today, yesterday, ...
    last = [closes[-1 - k] for k in range(n)]
    ma = mas[0]
    below = all(c <= m * (1 + config.SWITCH_OUT_ABOVE_PCT / 100) for c, m in zip(last, mas))
    above = all(c >= m * (1 + config.SWITCH_IN_ABOVE_PCT / 100) for c, m in zip(last, mas))
    con.executescript(SCHEMA)
    row = con.execute("SELECT storm FROM market_weather WHERE asof<? ORDER BY asof DESC LIMIT 1", (asof,)).fetchone()
    prev = bool(row[0]) if row else False
    storm = True if below else False if above else prev
    con.execute("INSERT OR REPLACE INTO market_weather VALUES (?,?,?,?)", (asof, int(storm), closes[-1], ma))
    con.commit()
    gap = (closes[-1] / ma - 1) * 100
    out.update(storm=storm, spy=closes[-1], ma200=ma, gap_pct=gap,
               text=(f"STORM: S&P 500 (SPY {closes[-1]:,.2f}) is {gap:+.1f}% vs its 200-day average ({ma:,.2f}). "
                     f"Money waits in {config.SAFE_FUND} until SPY closes {config.SWITCH_IN_ABOVE_PCT:g}%+ above "
                     f"the average ({ma * (1 + config.SWITCH_IN_ABOVE_PCT / 100):,.2f}) {n} days in a row."
                     if storm else
                     f"Fair weather: S&P 500 (SPY {closes[-1]:,.2f}) is {gap:+.1f}% vs its 200-day average "
                     f"({ma:,.2f}). Out to {config.SAFE_FUND} after {n} closes at or below it."))
    return out
