"""Per-fund trend switch for the 8-fund plan (STRATEGY = "themes").

Each fund in config.THEME_FUNDS is held from the start. Its switch is "armed" the first time the fund closes above
its own 200-day average. Once armed: out to SGOV after SWITCH_DAYS closes at/below the average (+SWITCH_OUT_ABOVE_PCT%);
back in after SWITCH_DAYS closes at least SWITCH_IN_ABOVE_PCT% above it. Until armed, the fund is simply held.
State is kept per evening in the fund_switch table.
"""
from . import config

SCHEMA = ("CREATE TABLE IF NOT EXISTS fund_switch (asof TEXT, ticker TEXT, armed INTEGER, inn INTEGER, close REAL, "
          "ma200 REAL, PRIMARY KEY (asof, ticker))")


def decide(closes, prev_armed, prev_in):
    """-> (armed, in, close, ma, gap%) from a list of closes (oldest first)."""
    n = config.SWITCH_DAYS
    if len(closes) < 200 + n:
        return prev_armed, prev_in, (closes[-1] if closes else None), None, None
    mas = [sum(closes[len(closes) - k - 200:len(closes) - k]) / 200 for k in range(n)]
    last = [closes[-1 - k] for k in range(n)]
    ma, close = mas[0], closes[-1]
    armed = prev_armed or close > ma
    inn = prev_in
    if armed:
        if all(c <= m * (1 + config.SWITCH_OUT_ABOVE_PCT / 100) for c, m in zip(last, mas)):
            inn = False
        elif all(c >= m * (1 + config.SWITCH_IN_ABOVE_PCT / 100) for c, m in zip(last, mas)):
            inn = True
    else:
        inn = True  # not protected yet: held as you asked
    return armed, inn, close, ma, (close / ma - 1) * 100


def check(con, asof, bars):
    """{ticker: {"armed", "in", "close", "ma200", "gap"}} for every theme fund, saved for tomorrow."""
    con.execute(SCHEMA)
    out = {}
    for t in config.THEME_FUNDS:
        prev = con.execute("SELECT armed, inn FROM fund_switch WHERE ticker=? AND asof<? ORDER BY asof DESC LIMIT 1",
                           (t, asof)).fetchone()
        prev_armed, prev_in = (bool(prev[0]), bool(prev[1])) if prev else (False, True)
        closes = [b[1] for b in (bars or {}).get(t) or []]
        armed, inn, close, ma, gap = decide(closes, prev_armed, prev_in)
        if not getattr(config, "FUND_SWITCH", True):
            armed, inn = False, True  # no protection: always held
        con.execute("INSERT OR REPLACE INTO fund_switch VALUES (?,?,?,?,?,?)", (asof, t, int(armed), int(inn), close, ma))
        out[t] = {"armed": armed, "in": inn, "close": close, "ma200": ma, "gap": gap}
    con.commit()
    return out


def text(state):
    parts = []
    for t, s in state.items():
        g = f"{s['gap']:+.1f}% vs 200-day" if s.get("gap") is not None else "no data"
        mode = ("IN" if s["in"] else "OUT -> SGOV") if s["armed"] else "held (switch not armed yet)"
        parts.append(f"{t} {mode}, {g}")
    return "; ".join(parts)
