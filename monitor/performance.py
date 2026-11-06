"""Wins & losses, and whether the swap ideas actually worked.

1. Wins & losses: every trade IB reports (synced by ibkr_sync into the `trades` table). A sale that closes
   a position carries IB's realized profit/loss (FIFO); a win is a sale with a profit. Open positions add the
   profit/loss you haven't locked in yet ("unrealized").
2. Daily record (`perf_daily`): book value, cost, open P&L, realized to date, and SPY's close, so the account
   can be compared with simply holding the S&P 500 from the first tracked day.
3. Swap scorecard (`swap_scorecard`): for every swap the rotation suggested, how the stock it said to buy did
   versus the stock it said to sell, from the close on the day of the suggestion to today.
   edge = bought stock's return - sold stock's return. Positive = the swap beat keeping the old stock.
   Each idea is marked followed / not followed / open, from your IB trades (or, before IB has them, from
   what's in your book now). Ideas you skipped are scored too, so you can see if skipping was right.
"""
import datetime as dt

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    trade_id TEXT PRIMARY KEY, trade_date TEXT, ticker TEXT, asset_type TEXT, description TEXT, side TEXT,
    quantity REAL, price REAL, proceeds REAL, commission REAL, realized REAL);
CREATE TABLE IF NOT EXISTS perf_daily (
    asof TEXT PRIMARY KEY, value REAL, cost REAL, unrealized REAL, realized_to_date REAL, spy REAL);
CREATE TABLE IF NOT EXISTS swap_scorecard (
    suggested_on TEXT, sell TEXT, buy TEXT, followed TEXT, sell_then REAL, buy_then REAL, sell_now REAL,
    buy_now REAL, sell_ret REAL, buy_ret REAL, edge REAL, days INTEGER, asof TEXT, PRIMARY KEY (suggested_on, sell));
"""
FOLLOW_WINDOW_DAYS = 7  # a swap counts as followed if you traded it within a week of the idea


def setup(con):
    con.executescript(SCHEMA)


def save_trades(con, trades):
    """Insert IB trades; the same trade arriving in several reports is stored once. Returns how many were new."""
    setup(con)
    before = con.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    con.executemany("INSERT OR IGNORE INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [(t["trade_id"], t["trade_date"], t["ticker"], t["asset_type"], t.get("description"), t["side"],
                      t["quantity"], t["price"], t.get("proceeds"), t.get("commission"), t.get("realized"))
                     for t in trades])
    con.commit()
    return con.execute("SELECT COUNT(*) FROM trades").fetchone()[0] - before


def _rows(con, sql, args=()):
    cur = con.execute(sql, args)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def wins_losses(con, unrealized=None):
    setup(con)
    closed = _rows(con, "SELECT * FROM trades WHERE realized IS NOT NULL AND realized != 0 ORDER BY trade_date DESC")
    realized = sum(t["realized"] for t in closed)
    wins = [t for t in closed if t["realized"] > 0]
    losses = [t for t in closed if t["realized"] < 0]
    fees = sum(abs(t["commission"] or 0) for t in _rows(con, "SELECT commission FROM trades"))
    by = {}
    for t in closed:
        by.setdefault(t["ticker"], 0.0)
        by[t["ticker"]] += t["realized"]
    out = {"trades": con.execute("SELECT COUNT(*) FROM trades").fetchone()[0], "closed": closed,
           "realized": round(realized, 2), "wins": len(wins), "losses": len(losses),
           "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else None,
           "avg_win": round(sum(t["realized"] for t in wins) / len(wins), 2) if wins else None,
           "avg_loss": round(sum(t["realized"] for t in losses) / len(losses), 2) if losses else None,
           "fees": round(fees, 2), "by_ticker": sorted(({"ticker": k, "realized": round(v, 2)} for k, v in by.items()),
                                                    key=lambda x: -x["realized"]),
           "unrealized": round(unrealized, 2) if unrealized is not None else None}
    out["total"] = round(realized + (unrealized or 0), 2)
    return out


def close_on(bars, day):
    """Close on `day`, or the last close before it (weekends/holidays)."""
    if not bars:
        return None
    before = [b for b in bars if b[0] <= day]
    return (before[-1] if before else bars[0])[1]


def followed(con, s, held, asof):
    start = s["suggested_on"]
    end = (dt.date.fromisoformat(start) + dt.timedelta(days=FOLLOW_WINDOW_DAYS)).isoformat()
    tr = _rows(con, "SELECT ticker, side FROM trades WHERE trade_date>=? AND trade_date<=?", (start, end))
    bought = any(t["ticker"] == s["buy"] and t["side"] == "BUY" for t in tr) or \
        (s["buy"] in held and (held[s["buy"]] or "") >= start)
    sold = any(t["ticker"] == s["sell"] and t["side"] == "SELL" for t in tr) or s["sell"] not in held
    if bought and sold:
        return "yes"
    if bought or sold:
        return "partly"
    return "open" if asof <= end else "no"


def scorecard(con, asof, rows, bars):
    setup(con)
    try:
        ideas = _rows(con, "SELECT asof AS suggested_on, sell, buy FROM rotation_log ORDER BY asof")
    except Exception:  # noqa: BLE001 - no rotation yet
        return []
    held = {r["ticker"]: r.get("entry_date") for r in rows if r.get("asset_type") == "shares"}
    out = []
    for s in ideas:
        sb, bb = bars.get(s["sell"]), bars.get(s["buy"])
        st, bt = close_on(sb, s["suggested_on"]), close_on(bb, s["suggested_on"])
        sn, bn = close_on(sb, asof), close_on(bb, asof)
        sr = sn / st - 1 if st and sn else None
        br = bn / bt - 1 if bt and bn else None
        rec = {**s, "followed": followed(con, s, held, asof), "sell_then": st, "buy_then": bt, "sell_now": sn,
               "buy_now": bn, "sell_ret": sr, "buy_ret": br, "edge": br - sr if sr is not None and br is not None else None,
               "days": (dt.date.fromisoformat(asof) - dt.date.fromisoformat(s["suggested_on"])).days, "asof": asof}
        out.append(rec)
        con.execute("INSERT OR REPLACE INTO swap_scorecard VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    tuple(rec[k] for k in ("suggested_on", "sell", "buy", "followed", "sell_then", "buy_then",
                                            "sell_now", "buy_now", "sell_ret", "buy_ret", "edge", "days", "asof")))
    con.commit()
    return out


def score_summary(cards):
    def grp(items):
        scored = [c for c in items if c["edge"] is not None and c["days"] > 0]
        if not scored:
            return {"count": len(items), "scored": 0, "beat": 0, "avg_edge": None}
        return {"count": len(items), "scored": len(scored), "beat": sum(c["edge"] > 0 for c in scored),
                "avg_edge": sum(c["edge"] for c in scored) / len(scored)}
    return {"all": grp(cards), "followed": grp([c for c in cards if c["followed"] in ("yes", "partly")]),
            "skipped": grp([c for c in cards if c["followed"] == "no"])}


def tracked_tickers(con, days=120, asof=None):
    """Stocks named in recent swap ideas, so their prices keep being downloaded after you sell them."""
    since = (dt.date.fromisoformat(asof) if asof else dt.date.today()) - dt.timedelta(days=days)
    try:
        return sorted({t for r in con.execute("SELECT sell, buy FROM rotation_log WHERE asof>=?", (since.isoformat(),))
                       for t in r})
    except Exception:  # noqa: BLE001
        return []


def run(con, asof, rows, totals, bars):
    setup(con)
    wl = wins_losses(con, totals.get("pnl"))
    spy = close_on(bars.get("SPY"), asof) if bars else None
    con.execute("INSERT OR REPLACE INTO perf_daily VALUES (?,?,?,?,?,?)",
                (asof, totals.get("value"), totals.get("cost"), totals.get("pnl"), wl["realized"], spy))
    con.commit()
    cards = scorecard(con, asof, rows, bars) if bars else []
    return {"wins_losses": {k: v for k, v in wl.items() if k != "closed"}, "scorecard": cards,
            "score_summary": score_summary(cards)}


def text(p):
    w = p["wins_losses"]
    lines = ["\nWINS & LOSSES"]
    if w["trades"]:
        lines.append(f"Locked-in (realized) {w['realized']:+,.2f} from {w['wins']} win(s) / {w['losses']} loss(es)"
                     + (f", win rate {w['win_rate']:.0f}%" if w["win_rate"] is not None else "")
                     + f"; fees {w['fees']:,.2f}")
    else:
        lines.append("No IB trades synced yet (add the Trades section to the Flex Query).")
    if w["unrealized"] is not None:
        lines.append(f"Open (not locked in) {w['unrealized']:+,.2f} · total {w['total']:+,.2f}")
    lines.append("\nSWAP SCORECARD (bought stock vs sold stock since the idea; + means the swap helped)")
    for c in p["scorecard"]:
        e = f"{c['edge'] * 100:+.1f} pts" if c["edge"] is not None else "-"
        lines.append(f"- {c['suggested_on']} {c['sell']} -> {c['buy']} [{c['followed']}]: {e} after {c['days']} day(s)")
    s = p["score_summary"]["all"]
    if s["scored"]:
        lines.append(f"{s['beat']} of {s['scored']} swap ideas are ahead; average edge {s['avg_edge'] * 100:+.1f} pts")
    return "\n".join(lines)
