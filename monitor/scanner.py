"""Opportunity scanner + watchlist: looks beyond the stocks you own.

Watchlist (watchlist.json): stocks you'd like to own, each with your own optional buy_below price.
  watch_buy  (high, plan says BUY)    price is at or below your buy level
  watch_near (info, plan says REVIEW) price is within 5% above your buy level
Market scan (every S&P 500 company, daily bars), facts only:
  momentum_leaders      strongest 12-month return, skipping the latest month (the standard momentum measure)
  pullback_in_uptrend   above the 200-day average, but RSI-2 under 10 after a sharp 2-day drop
  new_52w_high          closed at a new 52-week high
  unusual_volume        volume 3x+ its 20-day average with a 3%+ move
The top candidates get a short Claude news summary. Candidates are things to research, not recommendations:
only a buy level YOU set turns into a BUY label.
"""
import json

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS scan_results (
    asof TEXT, screen TEXT, rank INTEGER, ticker TEXT, price REAL, chg_1d REAL, ret_12m REAL, vs_200d REAL,
    rsi2 REAL, from_high REAL, vol_ratio REAL, reason TEXT, PRIMARY KEY (asof, screen, ticker));
CREATE TABLE IF NOT EXISTS watchlist (
    asof TEXT, ticker TEXT, price REAL, buy_below REAL, to_buy_pct REAL, chg_1d REAL, ret_12m REAL, vs_200d REAL,
    rsi2 REAL, status TEXT, action TEXT, note TEXT, PRIMARY KEY (asof, ticker));
"""
SCREENS = {"momentum_leaders": "Momentum leaders", "pullback_in_uptrend": "Pullbacks in uptrends",
           "new_52w_high": "New 52-week highs", "unusual_volume": "Unusual volume"}


def rsi2(closes):
    if len(closes) < 10:
        return None
    gains = losses = 0.0
    for i in range(1, 3):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0); losses += max(-ch, 0)
    ag, al = gains / 2, losses / 2
    for i in range(3, len(closes)):
        ch = closes[i] - closes[i - 1]
        ag = (ag + max(ch, 0)) / 2
        al = (al + max(-ch, 0)) / 2
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def metrics(bars):
    c = [b[1] for b in bars]
    if len(c) < 30:
        return None
    m = {"price": c[-1], "chg_1d": c[-1] / c[-2] - 1, "rsi2": rsi2(c[-60:])}
    m["ret_12m"] = c[-22] / c[-253] - 1 if len(c) >= 253 else None
    m["vs_200d"] = c[-1] / (sum(c[-200:]) / 200) - 1 if len(c) >= 200 else None
    highs = [b[2] for b in bars[-252:]]
    m["high_52w"] = max(highs)
    m["from_high"] = c[-1] / m["high_52w"] - 1
    m["new_high"] = len(c) >= 200 and c[-1] > max(x[1] for x in bars[-252:-1])
    vols = [b[3] for b in bars[-21:-1]]
    avg = sum(vols) / len(vols) if vols else 0
    m["vol_ratio"] = bars[-1][3] / avg if avg else None
    return m


def universe():
    import csv
    try:
        with open(config.SCAN_UNIVERSE_FILE) as f:
            return [r["Symbol"].strip() for r in csv.DictReader(f) if r.get("Symbol")]
    except OSError:
        return []


def load_watchlist(path=None):
    try:
        with open(path or config.WATCHLIST_FILE) as f:
            raw = json.load(f)
    except OSError:
        return []
    return [{"ticker": str(w["ticker"]).upper(), "buy_below": w.get("buy_below"), "note": w.get("note", "")}
            for w in raw if w.get("ticker")]


def screens(data):
    m = {t: x for t, x in ((t, metrics(b)) for t, b in data.items()) if x}
    def top(items, key, reason):
        return [{"ticker": t, **m[t], "reason": reason(m[t])} for t in sorted(items, key=key)[:config.SCAN_TOP_N]]
    pct = lambda v: f"{v * 100:+.0f}%"
    out = {
        "momentum_leaders": top([t for t in m if m[t]["ret_12m"] is not None], lambda t: -m[t]["ret_12m"],
                                lambda x: f"{pct(x['ret_12m'])} over 12 months"),
        "pullback_in_uptrend": top([t for t in m if (m[t]["vs_200d"] or 0) > 0 and m[t]["rsi2"] is not None
                                    and m[t]["rsi2"] < 10], lambda t: m[t]["rsi2"],
                                   lambda x: f"{pct(x['vs_200d'])} above its 200-day average, RSI-2 {x['rsi2']:.0f} "
                                             f"after a sharp drop"),
        "new_52w_high": top([t for t in m if m[t]["new_high"]], lambda t: -(m[t]["ret_12m"] or 0),
                            lambda x: f"new 52-week high at {x['price']:,.2f}"),
        "unusual_volume": top([t for t in m if (m[t]["vol_ratio"] or 0) >= 3 and abs(m[t]["chg_1d"]) >= 0.03],
                              lambda t: -m[t]["vol_ratio"],
                              lambda x: f"volume {x['vol_ratio']:.1f}x normal, {pct(x['chg_1d'])} on the day"),
    }
    return out, m


def watch(watchlist, m):
    out, alerts = [], []
    for w in watchlist:
        x = m.get(w["ticker"])
        row = {**w, "price": None, "to_buy_pct": None, "status": "no price data (not trading yet?)", "action": None}
        if x:
            row.update({k: x.get(k) for k in ("price", "chg_1d", "ret_12m", "vs_200d", "rsi2")})
            b = w.get("buy_below")
            if b:
                row["to_buy_pct"] = (x["price"] / b - 1) * 100
                if x["price"] <= b:
                    row.update(status=f"at or below your buy level {b:,.2f}", action="BUY")
                    alerts.append({"kind": "watch_buy", "severity": "high", "ticker": w["ticker"], "action": "BUY",
                                   "message": f"{w['ticker']} is {x['price']:,.2f}, at or below your buy level {b:,.2f}."})
                elif row["to_buy_pct"] <= config.WATCH_NEAR_PCT:
                    row.update(status=f"{row['to_buy_pct']:.1f}% above your buy level", action="REVIEW")
                    alerts.append({"kind": "watch_near", "severity": "info", "ticker": w["ticker"], "action": "REVIEW",
                                   "message": f"{w['ticker']} is {x['price']:,.2f}, within {row['to_buy_pct']:.1f}% "
                                              f"of your buy level {b:,.2f}."})
                else:
                    row.update(status=f"{row['to_buy_pct']:.1f}% above your buy level", action="WAIT")
            else:
                row.update(status="watching (no buy level set)", action="WAIT")
        out.append(row)
    return out, alerts


def run(con, asof, provider, macro_label=None, news_caller=None, extra_tickers=()):
    """Returns (result, daily bars by ticker); the bars are reused by the rotation step."""
    con.executescript(SCHEMA)
    wl = load_watchlist()
    tickers = sorted(set(universe()) | {w["ticker"] for w in wl} | set(extra_tickers) | set(config.ROTATION_EXTRA))
    try:
        data = provider.bulk(tickers)
    except Exception as e:
        return {"screens": {}, "watchlist": [], "alerts": [], "news": [], "error": f"scan data failed: {e}"}, {}
    found, m = screens(data)
    wrows, alerts = watch(wl, m)
    con.execute("DELETE FROM scan_results WHERE asof=?", (asof,))
    for screen, items in found.items():
        con.executemany("INSERT INTO scan_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        [(asof, screen, i + 1, x["ticker"], x["price"], x["chg_1d"], x["ret_12m"], x["vs_200d"],
                          x["rsi2"], x["from_high"], x["vol_ratio"], x["reason"]) for i, x in enumerate(items)])
    con.execute("DELETE FROM watchlist WHERE asof=?", (asof,))
    con.executemany("INSERT INTO watchlist VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(asof, w["ticker"], w["price"], w.get("buy_below"), w["to_buy_pct"], w.get("chg_1d"),
                      w.get("ret_12m"), w.get("vs_200d"), w.get("rsi2"), w["status"], w["action"], w["note"])
                     for w in wrows])
    con.commit()
    # Claude news for the top candidates (first appearance across screens, then watchlist names)
    from . import news
    import os
    picks = []
    for screen in SCREENS:
        for x in found.get(screen, []):
            if x["ticker"] not in picks:
                picks.append(x["ticker"])
    picks = picks[:config.SCAN_NEWS_TOP] + [w["ticker"] for w in wrows if w["price"] and w["ticker"] not in picks]
    con.executescript(news.SCHEMA)
    summaries = [news.analyze_name(con, asof, t, [], provider, os.environ.get("ANTHROPIC_API_KEY"), macro_label,
                                   news_caller) for t in picks]
    return {"screens": found, "watchlist": wrows, "alerts": alerts, "news": summaries,
            "scanned": len(m), "requested": len(tickers)}, data
