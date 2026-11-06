"""Rotation: "follow the money".

Every run, score every stock in the market the same way (S&P 500 + major ETFs + what you hold):
  momentum    12-month return, skipping the latest month                (percentile vs the market)
  steadiness  that return divided by how much the price swings          (percentile vs the market)
  trend       above the 200-day average (+50) and the 50-day average (+50)
  news        Claude's sentiment where available: positive 100, neutral 50, negative 0 (50 if none)
blended with ROTATION_WEIGHTS into a 0-100 score, and rank everything.

Swap queue: holdings flagged WEAKENING (last close below the 50-day average) go first, then holdings losing money since you bought them are flagged LOSING and go first in line
(biggest loss first); the rest follow, weakest score first. A losing stock still needs a clearly stronger
replacement (the rules below); being first in line means it gets the best candidate before anything else.

Then, going down the swap queue, pair each holding with the strongest stock you don't own
(a different one for each swap) and suggest a SWAP when:
  - the candidate scores at least ROTATION_MIN_SCORE and beats that holding by ROTATION_MARGIN points
  - that holding wasn't already swapped / suggested in the last ROTATION_COOLDOWN_DAYS days
    (each stock at most once a week), and wasn't bought less than ROTATION_MIN_HOLD_DAYS ago
  - the candidate wasn't swapped out of your book in the last ROTATION_NO_REBUY_DAYS days
So every holding can be swapped once a week. It's a suggestion from fixed rules, not a prediction;
nothing is traded automatically.
"""
import datetime as dt
import math

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS rotation_scores (
    asof TEXT, ticker TEXT, rank INTEGER, score REAL, momentum REAL, steadiness REAL, trend REAL, news REAL,
    ret_12m REAL, held INTEGER, pnl_pct REAL, queue INTEGER, weak INTEGER, PRIMARY KEY (asof, ticker));
CREATE TABLE IF NOT EXISTS rotation_log (
    asof TEXT, sell TEXT, buy TEXT, sell_score REAL, buy_score REAL, sell_rank INTEGER,
    buy_rank INTEGER, amount REAL, reason TEXT, PRIMARY KEY (asof, sell));
"""
NEWS_POINTS = {"positive": 100.0, "neutral": 50.0, "negative": 0.0}


def check_weights():
    w = config.ROTATION_WEIGHTS
    if abs(sum(w.values()) - 1) > 1e-6:
        raise ValueError(f"ROTATION_WEIGHTS must add up to 1.0 (they add up to {sum(w.values()):.3f})")
    return w


def raw_factors(bars):
    c = [b[1] for b in bars]
    if len(c) < 253:
        return None
    ret = c[-22] / c[-253] - 1
    rets = [math.log(c[i] / c[i - 1]) for i in range(len(c) - 126, len(c)) if c[i - 1] > 0]
    mean = sum(rets) / len(rets)
    vol = math.sqrt(sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)) * math.sqrt(252) if len(rets) > 2 else 0
    trend = (50.0 if c[-1] > sum(c[-200:]) / 200 else 0.0) + (50.0 if c[-1] > sum(c[-50:]) / 50 else 0.0)
    return {"ret_12m": ret, "steady_raw": ret / vol if vol > 0 else 0.0, "trend": trend}


def percentiles(values):
    """{key: value} -> {key: 0-100 percentile rank}."""
    order = sorted(values, key=values.get)
    n = len(order)
    return {k: (i / (n - 1) * 100 if n > 1 else 50.0) for i, k in enumerate(order)}


def score_all(data, sentiment=None):
    w = check_weights()
    f = {t: x for t, x in ((t, raw_factors(b)) for t, b in data.items()) if x}
    if not f:
        return []
    mom = percentiles({t: x["ret_12m"] for t, x in f.items()})
    steady = percentiles({t: x["steady_raw"] for t, x in f.items()})
    out = []
    for t, x in f.items():
        news = NEWS_POINTS.get((sentiment or {}).get(t), 50.0)
        s = w["momentum"] * mom[t] + w["steadiness"] * steady[t] + w["trend"] * x["trend"] + w["news"] * news
        out.append({"ticker": t, "score": round(s, 1), "momentum": round(mom[t], 1), "steadiness": round(steady[t], 1),
                    "trend": x["trend"], "news": news, "ret_12m": x["ret_12m"]})
    out.sort(key=lambda r: -r["score"])
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def days_since(date_str, asof):
    try:
        return (dt.date.fromisoformat(asof) - dt.date.fromisoformat(date_str)).days
    except (TypeError, ValueError):
        return None


def why(r):
    parts = [f"{r['ret_12m'] * 100:+.0f}% over 12 months"]
    parts.append({100: "above its 50- and 200-day averages", 50: "above one of its 50-/200-day averages",
                  0: "below its 50- and 200-day averages"}[int(r["trend"])])
    return ", ".join(parts)


def queue(mine, held):
    """Order holdings for swapping: WEAKENING first (below the 50-day average), then losing money (biggest
    loss first), then lowest score first.
    Adds losing / pnl_pct / queue (1 = first in line) to each holding."""
    for r in mine:
        r["pnl_pct"] = held[r["ticker"]].get("pnl_pct")
        r["losing"] = r["pnl_pct"] is not None and r["pnl_pct"] < 0
        r["weak"] = bool(held[r["ticker"]].get("weak"))
    mine.sort(key=lambda r: (0 if r["weak"] else 1 if r["losing"] else 2,
                             (r["pnl_pct"] or 0) if (r["weak"] or r["losing"]) else r["score"]))
    for i, r in enumerate(mine, 1):
        r["queue"] = i
    return mine


def migrate(con):
    """Older databases keyed rotation_log by date only (one swap per day); key it by date + stock."""
    have = {r[1] for r in con.execute("PRAGMA table_info(rotation_scores)")}
    for col, typ in (("pnl_pct", "REAL"), ("queue", "INTEGER"), ("weak", "INTEGER")):
        if have and col not in have:
            con.execute(f"ALTER TABLE rotation_scores ADD COLUMN {col} {typ}")
    pk = [r[1] for r in con.execute("PRAGMA table_info(rotation_log)") if r[5]]
    if pk == ["asof"]:
        con.execute("ALTER TABLE rotation_log RENAME TO rotation_log_old")
        con.executescript(SCHEMA)
        con.execute("INSERT INTO rotation_log SELECT * FROM rotation_log_old")
        con.execute("DROP TABLE rotation_log_old")
        con.commit()


def log_rows(con, since):
    cur = con.execute("SELECT * FROM rotation_log WHERE asof>=? ORDER BY asof", (since,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def run(con, asof, rows, data, sentiment=None):
    con.executescript(SCHEMA)
    migrate(con)
    held = {r["ticker"]: r for r in rows if r["asset_type"] == "shares" and r.get("value")}
    scored = score_all(data, sentiment)
    by = {r["ticker"]: r for r in scored}
    total = len(scored)
    mine = queue([by[t] for t in held if t in by], held)
    con.execute("DELETE FROM rotation_scores WHERE asof=?", (asof,))
    con.executemany("INSERT INTO rotation_scores (asof, ticker, rank, score, momentum, steadiness, trend, news, ret_12m,"
                    " held, pnl_pct, queue, weak) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(asof, r["ticker"], r["rank"], r["score"], r["momentum"], r["steadiness"], r["trend"], r["news"],
                      r["ret_12m"], int(r["ticker"] in held), r.get("pnl_pct"), r.get("queue"), int(bool(r.get("weak")))) for r in scored])
    con.execute("DELETE FROM rotation_log WHERE asof=?", (asof,))  # re-runs on the same day start fresh
    con.commit()
    result = {"universe": total, "holdings": mine, "top": [r for r in scored if r["ticker"] not in held][:10],
              "suggestions": [], "status": ""}
    if not mine:
        result["status"] = "no scored holdings yet"
        return result

    day = dt.date.fromisoformat(asof)
    week = log_rows(con, (day - dt.timedelta(days=config.ROTATION_COOLDOWN_DAYS - 1)).isoformat())
    recent_out = {r["sell"] for r in log_rows(con, (day - dt.timedelta(days=config.ROTATION_NO_REBUY_DAYS)).isoformat())}
    # still-open ideas from earlier this week (the stock to sell is still in the book)
    pending = [{**r, "pending": True, "suggested_on": r["asof"]} for r in week if r["sell"] in held]
    swapped_this_week = {r["sell"] for r in week} | {r["buy"] for r in week}  # once a week per stock
    taken = {r["buy"] for r in pending}

    new = []
    candidates = [r for r in scored if r["ticker"] not in held and r["ticker"] not in recent_out
                  and r["ticker"] not in taken]
    for h in mine:  # swap queue: losing first, then weakest
        if h["ticker"] in swapped_this_week:
            continue
        bought = held[h["ticker"]].get("entry_date")
        d = days_since(bought, asof) if bought else None
        if d is not None and d < config.ROTATION_MIN_HOLD_DAYS:
            continue
        best = candidates[0] if candidates else None
        if not best or best["score"] < config.ROTATION_MIN_SCORE or best["score"] - h["score"] < config.ROTATION_MARGIN:
            continue
        candidates.pop(0)
        amount = held[h["ticker"]]["value"]
        reason = (("WEAKENING (below its 50-day average), first in line. " if h.get("weak") else
                   "LOSING " + f"{h['pnl_pct']:.1f}% since you bought it, first in line. " if h.get("losing") else "")
                  + f"{best['ticker']} ranks #{best['rank']} of {total} ({why(best)}); "
                  f"{h['ticker']} ranks #{h['rank']} ({why(h)}). Score {best['score']:.0f} vs {h['score']:.0f}.")
        s = {"asof": asof, "sell": h["ticker"], "buy": best["ticker"], "sell_score": h["score"],
             "buy_score": best["score"], "sell_rank": h["rank"], "buy_rank": best["rank"], "amount": amount,
             "reason": reason, "pending": False, "suggested_on": asof}
        con.execute("INSERT OR REPLACE INTO rotation_log VALUES (?,?,?,?,?,?,?,?,?)",
                    (asof, s["sell"], s["buy"], s["sell_score"], s["buy_score"], s["sell_rank"], s["buy_rank"],
                     amount, reason))
        new.append(s)
    con.commit()
    result["suggestions"] = pending + new
    if new:
        result["status"] = f"{len(new)} new swap(s) suggested"
    elif pending:
        result["status"] = "swap ideas from earlier this week are still open"
    else:
        best = candidates[0] if candidates else None
        result["status"] = (f"no swap: no stock you don't own clearly beats a holding that's free to swap "
                            f"(needs a score of {config.ROTATION_MIN_SCORE}+ and a {config.ROTATION_MARGIN}-point lead)"
                            + (f"; best candidate {best['ticker']} scores {best['score']:.0f}" if best else ""))
    return result


def alert(result):
    out = []
    for s in result.get("suggestions") or []:
        out.append({"kind": "swap", "severity": "warn" if s.get("pending") else "high", "ticker": s["sell"],
                    "message": f"SWAP idea: sell all {s['sell']} (about ${s['amount']:,.0f}, rank #{s['sell_rank']}) and "
                               f"buy {s['buy']} (rank #{s['buy_rank']}). {s['reason']}"
                               + (f" Suggested on {s['suggested_on']}." if s.get("pending") else "")})
    return out
