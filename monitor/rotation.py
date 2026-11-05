"""Rotation: "follow the money".

Every run, score every stock in the market the same way (S&P 500 + major ETFs + what you hold):
  momentum    12-month return, skipping the latest month                (percentile vs the market)
  steadiness  that return divided by how much the price swings          (percentile vs the market)
  trend       above the 200-day average (+50) and the 50-day average (+50)
  news        Claude's sentiment where available: positive 100, neutral 50, negative 0 (50 if none)
blended with ROTATION_WEIGHTS into a 0-100 score, and rank everything.

Then compare your weakest holding with the strongest stock you don't own. Suggest a SWAP only when:
  - the candidate scores at least ROTATION_MIN_SCORE and beats your weakest holding by ROTATION_MARGIN points
  - your weakest holding was bought at least ROTATION_MIN_HOLD_DAYS ago (if the buy date is known)
  - no other swap was suggested in the last ROTATION_COOLDOWN_DAYS days (one at a time)
  - the candidate wasn't swapped out of your book in the last ROTATION_NO_REBUY_DAYS days
It's a suggestion based on these fixed rules, not a prediction; nothing is traded automatically.
"""
import datetime as dt
import math

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS rotation_scores (
    asof TEXT, ticker TEXT, rank INTEGER, score REAL, momentum REAL, steadiness REAL, trend REAL, news REAL,
    ret_12m REAL, held INTEGER, PRIMARY KEY (asof, ticker));
CREATE TABLE IF NOT EXISTS rotation_log (
    asof TEXT PRIMARY KEY, sell TEXT, buy TEXT, sell_score REAL, buy_score REAL, sell_rank INTEGER,
    buy_rank INTEGER, amount REAL, reason TEXT);
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


def run(con, asof, rows, data, sentiment=None):
    con.executescript(SCHEMA)
    held = {r["ticker"]: r for r in rows if r["asset_type"] == "shares" and r.get("value")}
    scored = score_all(data, sentiment)
    con.execute("DELETE FROM rotation_scores WHERE asof=?", (asof,))
    con.executemany("INSERT INTO rotation_scores VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [(asof, r["ticker"], r["rank"], r["score"], r["momentum"], r["steadiness"], r["trend"], r["news"],
                      r["ret_12m"], int(r["ticker"] in held)) for r in scored])
    con.execute("DELETE FROM rotation_log WHERE asof=?", (asof,))
    con.commit()
    by = {r["ticker"]: r for r in scored}
    total = len(scored)
    mine = sorted([by[t] for t in held if t in by], key=lambda r: r["score"])
    result = {"universe": total, "holdings": mine, "top": [r for r in scored if r["ticker"] not in held][:10],
              "suggestion": None, "status": ""}
    if not mine:
        result["status"] = "no scored holdings yet"
        return result

    last = con.execute("SELECT * FROM rotation_log ORDER BY asof DESC LIMIT 1").fetchone()
    if last:
        cols = [d[0] for d in con.execute("SELECT * FROM rotation_log LIMIT 0").description]
        last = dict(zip(cols, last))
        age = days_since(last["asof"], asof)
        if age is not None and age < config.ROTATION_COOLDOWN_DAYS:
            if last["sell"] in held:
                result["suggestion"] = {**last, "pending": True, "suggested_on": last["asof"]}
                result["status"] = f"swap suggested on {last['asof']} is still open"
            else:
                nxt = dt.date.fromisoformat(last["asof"]) + dt.timedelta(days=config.ROTATION_COOLDOWN_DAYS)
                result["status"] = f"last swap done; next suggestion allowed from {nxt}"
            return result

    recent_out = {r[0] for r in con.execute("SELECT sell FROM rotation_log WHERE asof>=?",
                                           ((dt.date.fromisoformat(asof)
                                             - dt.timedelta(days=config.ROTATION_NO_REBUY_DAYS)).isoformat(),))}
    eligible = []
    for r in mine:
        bought = held[r["ticker"]].get("entry_date")
        d = days_since(bought, asof) if bought else None
        if d is None or d >= config.ROTATION_MIN_HOLD_DAYS:
            eligible.append(r)
    if not eligible:
        result["status"] = f"every holding is younger than {config.ROTATION_MIN_HOLD_DAYS} days"
        return result
    weakest = eligible[0]
    best = next((r for r in scored if r["ticker"] not in held and r["ticker"] not in recent_out), None)
    if not best:
        result["status"] = "no candidates scored"
        return result
    gap = best["score"] - weakest["score"]
    if best["score"] < config.ROTATION_MIN_SCORE or gap < config.ROTATION_MARGIN:
        result["status"] = (f"no swap: best candidate {best['ticker']} ({best['score']:.0f}) isn't clearly better than "
                            f"your weakest holding {weakest['ticker']} ({weakest['score']:.0f}); needs a "
                            f"{config.ROTATION_MARGIN}-point lead and a score of {config.ROTATION_MIN_SCORE}+")
        return result
    amount = held[weakest["ticker"]]["value"]
    reason = (f"{best['ticker']} ranks #{best['rank']} of {total} ({why(best)}); "
              f"{weakest['ticker']} ranks #{weakest['rank']} ({why(weakest)}). Score {best['score']:.0f} vs "
              f"{weakest['score']:.0f}.")
    s = {"asof": asof, "sell": weakest["ticker"], "buy": best["ticker"], "sell_score": weakest["score"],
         "buy_score": best["score"], "sell_rank": weakest["rank"], "buy_rank": best["rank"], "amount": amount,
         "reason": reason, "pending": False, "suggested_on": asof}
    con.execute("INSERT OR REPLACE INTO rotation_log VALUES (?,?,?,?,?,?,?,?,?)",
                (asof, s["sell"], s["buy"], s["sell_score"], s["buy_score"], s["sell_rank"], s["buy_rank"], amount, reason))
    con.commit()
    result["suggestion"], result["status"] = s, "new swap suggested"
    return result


def alert(result):
    s = result.get("suggestion")
    if not s:
        return []
    return [{"kind": "swap", "severity": "high" if not s.get("pending") else "warn", "ticker": s["sell"],
             "message": f"SWAP idea: sell all {s['sell']} (about ${s['amount']:,.0f}, rank #{s['sell_rank']}) and buy "
                        f"{s['buy']} (rank #{s['buy_rank']}). {s['reason']}"
                        + (f" Suggested on {s['suggested_on']}." if s.get("pending") else "")}]
