"""Layer 4a: diff and condition alerts. Surfaces facts; never says buy or sell.

New strike / expiry detection: compares today's chain snapshot with the prior run for each underlying
you hold options on. Lists new expiries, and new strikes within +/-30% (configurable) of strikes you hold,
so fresh LEAPS expiries and nearby strikes show up without scanning the whole chain.

Condition alerts (thresholds in config.py):
  target_hit  (high)  mark crossed your target_price, e.g. "NOK calls hit your target level"
  stop_hit    (high)  mark crossed your stop_price
  target_near (info)  80% or more of the way from entry to target
  iv_change   (warn)  a held contract's IV moved 20% or more vs the prior snapshot
  new_strikes (info) / new_expiry (info)  from the diff above
  news_flag   (warn)  Claude flagged something affecting a position, with the one-line driver attached *
  news_negative (warn) Claude read negative sentiment on a held name, with the one-line driver attached *
  macro_shift (warn)  macro score moved 15+ points or its label changed vs the prior run *
Layer 2 flags (concentration, IV rich/cheap, expiry watch) are included too.
* Inferred: this part of the original prompt was missing from the source; it was built to match the
  surviving "(warn), with the one-line driver attached" text and Layer 3's outputs.
"""
import json

from . import config, plan, storage

SEVERITY_ORDER = {"high": 0, "warn": 1, "info": 2}
SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    asof TEXT, kind TEXT, severity TEXT, ticker TEXT, position_id TEXT, message TEXT, is_new INTEGER,
    detail TEXT, action TEXT);
CREATE TABLE IF NOT EXISTS chain_diff (
    asof TEXT, ticker TEXT, prior_asof TEXT, new_expiries TEXT, new_strikes TEXT,
    PRIMARY KEY (asof, ticker));
"""


def plural(option_type):
    return "calls" if option_type == "call" else "puts"


def label(r):
    if r["asset_type"] == "option":
        return f"{r['ticker']} {r['strike']:g} {plural(r['option_type'])} ({r['expiry']})"
    return f"{r['ticker']} shares"


def chain_diff(con, ticker, asof, held_strikes):
    prior = storage.prior_asof(con, ticker, asof)
    if not prior:
        return {"ticker": ticker, "prior_asof": None, "new_expiries": [], "new_strikes": []}
    today, before = storage.chain_rows(con, ticker, asof), storage.chain_rows(con, ticker, prior)
    old_exp = {r["expiry"] for r in before}
    new_exp = sorted({r["expiry"] for r in today} - old_exp)
    old_keys = {(r["expiry"], r["option_type"], r["strike"]) for r in before}
    band = config.NEW_STRIKE_BAND_PCT / 100
    new_strikes = sorted(
        {(r["expiry"], r["option_type"], r["strike"]) for r in today
         if r["expiry"] not in new_exp and (r["expiry"], r["option_type"], r["strike"]) not in old_keys
         and any(k * (1 - band) <= r["strike"] <= k * (1 + band) for k in held_strikes)})
    return {"ticker": ticker, "prior_asof": prior, "new_expiries": new_exp,
            "new_strikes": [{"expiry": e, "option_type": t, "strike": k} for e, t, k in new_strikes]}


def prior_valuations(con, asof):
    row = con.execute("SELECT MAX(asof) FROM valuations WHERE asof<?", (asof,)).fetchone()
    if not row or not row[0]:
        return {}
    cur = con.execute("SELECT position_id, mark, iv, target_price, stop_price FROM valuations WHERE asof=?", (row[0],))
    return {r[0]: {"mark": r[1], "iv": r[2], "target": r[3], "stop": r[4]} for r in cur.fetchall()}


def hit(mark, level, entry, direction):
    """True when mark is at/through level on the side away from entry ('target' or 'stop')."""
    if mark is None or level is None:
        return False
    if direction == "target":
        return mark >= level if level >= entry else mark <= level
    return mark <= level if level <= entry else mark >= level


def build(con, asof, rows, analytics_summary=None, macro_result=None, news_result=None, extra=None):
    con.executescript(SCHEMA)
    storage.add_missing_columns(con, "alerts", [("action", "TEXT")])
    out = []
    prev = prior_valuations(con, asof)

    seen = {(k, tk, pid) for k, tk, pid in con.execute(
        "SELECT kind, ticker, position_id FROM alerts WHERE asof=(SELECT MAX(asof) FROM alerts WHERE asof<?)",
        (asof,)).fetchall()}

    def add(kind, severity, message, r=None, ticker=None, is_new=None, detail=None):
        tk, pid = ticker or (r or {}).get("ticker"), (r or {}).get("position_id")
        if is_new is None:  # new = this alert wasn't raised at the prior run
            is_new = (kind, tk, pid) not in seen
        out.append({"kind": kind, "severity": severity, "message": message,
                    "action": plan.ALERT_ACTION.get(kind),
                    "ticker": tk, "position_id": pid,
                    "is_new": bool(is_new), "detail": detail})

    for r in rows:
        mark, entry, p = r.get("mark"), r["entry_price"], prev.get(r["position_id"], {})
        if hit(mark, r.get("target_price"), entry, "target"):
            add("target_hit", "high", f"{label(r)} hit your target level (mark {mark:,.2f} vs target "
                f"{r['target_price']:,.2f}).", r, is_new=not hit(p.get("mark"), r.get("target_price"), entry, "target"))
        elif r.get("progress_target") is not None and r["progress_target"] >= config.TARGET_NEAR_PCT:
            add("target_near", "info", f"{label(r)} is {r['progress_target']:.0f}% of the way to your target "
                f"(mark {mark:,.2f}, target {r['target_price']:,.2f}).", r)
        if hit(mark, r.get("stop_price"), entry, "stop"):
            add("stop_hit", "high", f"{label(r)} crossed your stop level (mark {mark:,.2f} vs stop "
                f"{r['stop_price']:,.2f}).", r, is_new=not hit(p.get("mark"), r.get("stop_price"), entry, "stop"))
        iv, iv_prev = r.get("iv"), p.get("iv")
        if iv and iv_prev and abs(iv / iv_prev - 1) * 100 >= config.IV_CHANGE_PCT:
            add("iv_change", "warn", f"{label(r)}: IV moved from {iv_prev * 100:.0f}% to {iv * 100:.0f}% "
                f"({(iv / iv_prev - 1) * 100:+.0f}%) since the prior run.", r)

    diffs = []
    for ticker in sorted({r["ticker"] for r in rows if r["asset_type"] == "option"}):
        held = [r["strike"] for r in rows if r["ticker"] == ticker and r["asset_type"] == "option"]
        d = chain_diff(con, ticker, asof, held)
        diffs.append(d)
        con.execute("INSERT OR REPLACE INTO chain_diff VALUES (?,?,?,?,?)",
                    (asof, ticker, d["prior_asof"], json.dumps(d["new_expiries"]), json.dumps(d["new_strikes"])))
        if d["new_expiries"]:
            add("new_expiry", "info", f"{ticker}: new expir{'y' if len(d['new_expiries']) == 1 else 'ies'} listed: "
                f"{', '.join(d['new_expiries'])}.", ticker=ticker, detail=d["new_expiries"])
        if d["new_strikes"]:
            ks = sorted({s["strike"] for s in d["new_strikes"]})
            add("new_strikes", "info", f"{ticker}: {len(d['new_strikes'])} new contract(s) near your strike(s) "
                f"{', '.join(f'{k:g}' for k in held)}: strikes {', '.join(f'{k:g}' for k in ks[:8])}"
                f"{'...' if len(ks) > 8 else ''}.", ticker=ticker, detail=d["new_strikes"])

    for n in news_result or []:
        if n.get("status") != "ok":
            continue
        driver = (n.get("drivers") or [""])[0]
        for f in n.get("position_flags") or []:
            add("news_flag", "warn", f"{n['ticker']} news: {f['flag']}" + (f" (driver: {driver})" if driver else ""),
                ticker=n["ticker"], detail=f.get("position_id"))
        if n.get("sentiment") == "negative":
            add("news_negative", "warn", f"{n['ticker']}: news read negative" + (f" (driver: {driver})" if driver else "")
                + ".", ticker=n["ticker"])

    if macro_result and macro_result.get("score") is not None:
        row = con.execute("SELECT score, label FROM macro WHERE asof<? AND score IS NOT NULL ORDER BY asof DESC LIMIT 1",
                          (asof,)).fetchone()
        if row and (abs(macro_result["score"] - row[0]) >= config.MACRO_SHIFT_POINTS or row[1] != macro_result["label"]):
            add("macro_shift", "warn", f"Market environment moved from {row[1]} ({row[0]:.0f}) to "
                f"{macro_result['label']} ({macro_result['score']:.0f}).")

    for x in extra or []:  # watchlist alerts from the scanner
        add(x["kind"], x["severity"], x["message"], ticker=x.get("ticker"))

    for f in (analytics_summary or {}).get("flags", []):
        add(f["kind"], f["severity"], f["message"], ticker=None, detail=f.get("position_id"))

    out.sort(key=lambda a: (SEVERITY_ORDER.get(a["severity"], 9), not a["is_new"], a["kind"]))
    con.execute("DELETE FROM alerts WHERE asof=?", (asof,))
    con.executemany("INSERT INTO alerts (asof, kind, severity, ticker, position_id, message, is_new, detail, action) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    [(asof, a["kind"], a["severity"], a["ticker"], a["position_id"], a["message"], int(a["is_new"]),
                      json.dumps(a["detail"]), a.get("action")) for a in out])
    con.commit()
    return out, diffs
