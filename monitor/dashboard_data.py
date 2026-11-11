"""Reads the monitor database and shapes everything the dashboard shows. No Streamlit here, so it's testable."""
import datetime as dt
import json
import sqlite3

from . import config, performance, plan
from .greeks import bs_greeks


def rows(con, sql, args=()):
    cur = con.execute(sql, args)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def dates(con):
    return [r[0] for r in con.execute("SELECT DISTINCT asof FROM valuations ORDER BY asof DESC").fetchall()]


def table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def theta_projection(positions, rate=config.RISK_FREE_RATE):
    """Day-by-day option value if spot and IV stay where they are (illustrative, not predictive).
    Returns (stacked rows [{day, date, position, value}], extrinsic rows [{day, date, position, extrinsic}])."""
    opts = [p for p in positions if p["asset_type"] == "option" and p.get("iv") and p.get("spot")
            and p.get("dte") is not None and p["dte"] >= 0]
    if not opts:
        return [], []
    horizon = max(p["dte"] for p in opts)
    step = max(1, horizon // 150)
    start = dt.date.fromisoformat(opts[0]["asof"])
    stacked, extrinsic = [], []
    for d in list(range(0, horizon + 1, step)) + ([horizon] if horizon % step else []):
        day = (start + dt.timedelta(days=d)).isoformat()
        for p in opts:
            left = p["dte"] - d
            intrinsic = max(p["spot"] - p["strike"], 0) if p["option_type"] == "call" else max(p["strike"] - p["spot"], 0)
            price = bs_greeks(p["option_type"], p["spot"], p["strike"], max(left, 0) / 365, rate, p["iv"])["price"] \
                if left > 0 else intrinsic
            name = f"{p['ticker']} {p['strike']:g}{p['option_type'][0].upper()} {p['expiry']}"
            stacked.append({"day": d, "date": day, "position": name,
                            "value": round(price * p["contracts"] * config.CONTRACT_MULTIPLIER, 2)})
            if left >= 0:
                extrinsic.append({"day": d, "date": day, "position": name, "extrinsic": round(price - intrinsic, 3)})
    return stacked, extrinsic


def strike_ladder(con, asof, p, new_keys, width=6):
    chain = rows(con, "SELECT strike, bid, ask, last, iv, volume, open_interest FROM chain WHERE asof=? AND ticker=? "
                      "AND expiry=? AND option_type=? ORDER BY strike", (asof, p["ticker"], p["expiry"], p["option_type"]))
    if not chain:
        return []
    idx = min(range(len(chain)), key=lambda i: abs(chain[i]["strike"] - p["strike"]))
    out = []
    for r in chain[max(0, idx - width): idx + width + 1]:
        r["held"] = abs(r["strike"] - p["strike"]) < 1e-6
        r["new"] = (p["ticker"], p["expiry"], p["option_type"], r["strike"]) in new_keys
        out.append(r)
    return out


def autopilot():
    """Practice autopilot: tonight's plan, recent trades and the account's daily value (files only, no broker calls)."""
    import csv
    import os
    from . import autotrade
    out = {"plan": autotrade.load_json(autotrade.PLAN_FILE, None), "paused": autotrade.paused(), "log": [],
           "history": []}
    try:
        with open(autotrade.LOG_FILE) as f:
            out["log"] = list(csv.DictReader(f))[-20:][::-1]
    except OSError:
        pass
    if os.path.exists(config.AUTO_DB):
        c = sqlite3.connect(config.AUTO_DB)
        try:
            if table_exists(c, "perf_daily"):
                out["history"] = rows(c, "SELECT * FROM perf_daily ORDER BY asof")
        finally:
            c.close()
    return out


def load(db_path=None, asof=None):
    con = sqlite3.connect(db_path or config.DB_FILE)
    try:
        avail = dates(con) if table_exists(con, "valuations") else []
        if not avail:
            return {"asof": None, "dates": []}
        asof = asof if asof in avail else avail[0]
        pos = rows(con, "SELECT * FROM valuations WHERE asof=? ORDER BY value DESC", (asof,))
        for p in pos:
            p["asof"] = asof
            if not p.get("action"):  # rows saved before plan labels existed
                p["action"], p["action_reason"] = plan.for_position(p)
        a = rows(con, "SELECT * FROM analytics WHERE asof=?", (asof,)) if table_exists(con, "analytics") else []
        alloc = rows(con, "SELECT * FROM allocation WHERE asof=? ORDER BY pct DESC", (asof,)) \
            if table_exists(con, "allocation") else []
        ivenv = {r["position_id"]: r for r in rows(con, "SELECT * FROM iv_environment WHERE asof=?", (asof,))} \
            if table_exists(con, "iv_environment") else {}
        alerts = rows(con, "SELECT * FROM alerts WHERE asof=?", (asof,)) if table_exists(con, "alerts") else []
        for al in alerts:
            al["action"] = al.get("action") or plan.ALERT_ACTION.get(al["kind"])
        order = {"high": 0, "warn": 1, "info": 2}
        alerts.sort(key=lambda x: (order.get(x["severity"], 9), -x["is_new"]))
        m = rows(con, "SELECT * FROM macro WHERE asof=?", (asof,)) if table_exists(con, "macro") else []
        macro = None
        if m:
            macro = {**m[0], "components": json.loads(m[0]["components"] or "{}"),
                     "inputs": json.loads(m[0]["inputs"] or "{}"), "missing": json.loads(m[0]["missing"] or "[]")}
            macro["history"] = rows(con, "SELECT asof, score FROM macro WHERE score IS NOT NULL ORDER BY asof")
        news = []
        if table_exists(con, "news_analysis"):
            for n in rows(con, "SELECT * FROM news_analysis WHERE asof=? ORDER BY ticker", (asof,)):
                for k in ("headlines", "drivers", "position_flags"):
                    n[k] = json.loads(n[k] or "[]")
                news.append(n)
        new_keys = set()
        if table_exists(con, "chain_diff"):
            for d in rows(con, "SELECT ticker, new_strikes FROM chain_diff WHERE asof=?", (asof,)):
                for s in json.loads(d["new_strikes"] or "[]"):
                    new_keys.add((d["ticker"], s["expiry"], s["option_type"], s["strike"]))
        ladders = {p["position_id"]: strike_ladder(con, asof, p, new_keys)
                   for p in pos if p["asset_type"] == "option" and p.get("expiry")}
        stacked, extrinsic = theta_projection(pos)
        watch = rows(con, "SELECT * FROM watchlist WHERE asof=?", (asof,)) if table_exists(con, "watchlist") else []
        scan = {}
        if table_exists(con, "scan_results"):
            for r in rows(con, "SELECT * FROM scan_results WHERE asof=? ORDER BY screen, rank", (asof,)):
                scan.setdefault(r["screen"], []).append(r)
        held = {p["ticker"] for p in pos}
        rot = {"holdings": [], "top": [], "universe": 0, "suggestions": []}
        if table_exists(con, "rotation_scores"):
            sc = rows(con, "SELECT * FROM rotation_scores WHERE asof=? ORDER BY rank", (asof,))
            rot["universe"] = len(sc)
            rot["holdings"] = sorted([r for r in sc if r["held"]],
                                     key=lambda r: (r.get("queue") or 999, r["score"]))  # swap line order
            rot["top"] = [r for r in sc if not r["held"]][:10]
        if table_exists(con, "rotation_log"):
            from . import rotation
            since = rotation.cooldown_start(asof)
            rot["suggestions"] = [r for r in rows(con, "SELECT * FROM rotation_log WHERE asof<=? AND asof>=? "
                                                       "ORDER BY sell_score", (asof, since)) if r["sell"] in held]
        perf = {"wins_losses": None, "history": [], "scorecard": [], "summary": None}
        unreal = sum((p.get("value") or 0) - (p.get("cost") or 0) for p in pos if p.get("value") is not None)
        if table_exists(con, "trades"):
            perf["wins_losses"] = performance.wins_losses(con, unreal)
        if table_exists(con, "perf_daily"):
            perf["history"] = rows(con, "SELECT * FROM perf_daily WHERE asof<=? ORDER BY asof", (asof,))
        if table_exists(con, "vs_sp500"):
            last = con.execute("SELECT MAX(asof) FROM vs_sp500 WHERE asof<=?", (asof,)).fetchone()[0]
            perf["vs_sp500"] = rows(con, "SELECT day, mine, sp500, spy_shares FROM vs_sp500 WHERE asof=? ORDER BY day",
                                    (last,)) if last else []
        if table_exists(con, "swap_scorecard"):
            cards = rows(con, "SELECT * FROM swap_scorecard WHERE asof=? ORDER BY suggested_on DESC, sell", (asof,))
            perf["scorecard"], perf["summary"] = cards, performance.score_summary(cards)
        weather = None
        if table_exists(con, "market_weather"):
            w = rows(con, "SELECT * FROM market_weather WHERE asof<=? ORDER BY asof DESC LIMIT 1", (asof,))
            weather = w[0] if w else None
        return {"asof": asof, "dates": avail, "positions": pos, "performance": perf, "autopilot": autopilot(),
                "weather": weather, "analytics": a[0] if a else None,
                "allocation": alloc, "iv_env": ivenv, "alerts": alerts, "macro": macro, "news": news,
                "ladders": ladders, "theta_stacked": stacked, "extrinsic": extrinsic,
                "watchlist": watch, "scan": scan, "rotation": rot,
                "held_news": [n for n in news if n["ticker"] in held],
                "candidate_news": {n["ticker"]: n for n in news if n["ticker"] not in held}}
    finally:
        con.close()
