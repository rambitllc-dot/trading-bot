"""Market weather: is the S&P 500 (SPY) above or below its 200-day average?

Storm  = SPY closed below its 200-day average 2 days in a row. Fair = closed above it 2 days in a row.
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
    if len(closes) < 201:
        return out
    ma = sum(closes[-200:]) / 200
    ma_prev = sum(closes[-201:-1]) / 200
    below = closes[-1] < ma and closes[-2] < ma_prev
    above = closes[-1] >= ma and closes[-2] >= ma_prev
    con.executescript(SCHEMA)
    row = con.execute("SELECT storm FROM market_weather WHERE asof<? ORDER BY asof DESC LIMIT 1", (asof,)).fetchone()
    prev = bool(row[0]) if row else False
    storm = True if below else False if above else prev
    con.execute("INSERT OR REPLACE INTO market_weather VALUES (?,?,?,?)", (asof, int(storm), closes[-1], ma))
    con.commit()
    gap = (closes[-1] / ma - 1) * 100
    out.update(storm=storm, spy=closes[-1], ma200=ma, gap_pct=gap,
               text=(f"STORM: S&P 500 (SPY {closes[-1]:,.2f}) is {abs(gap):.1f}% below its 200-day average "
                     f"({ma:,.2f}). No new stock buys; new money waits in {config.SAFE_FUND}."
                     if storm else
                     f"Fair weather: S&P 500 (SPY {closes[-1]:,.2f}) is {gap:+.1f}% vs its 200-day average "
                     f"({ma:,.2f})."))
    return out
