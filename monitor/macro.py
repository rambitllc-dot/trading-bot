"""Layer 3a: deterministic macro gate, a 0-100 score of the market environment the book sits in.

Same data in, same score out. Higher = calmer / more supportive. Components (weights in config.py):
  vix_level       VIX: 12 or lower -> 100, 40 or higher -> 0, straight line between
  vix_percentile  100 minus where today's VIX ranks among the last 252 closes
  term_structure  VIX / VIX3M: 0.80 or lower -> 100 (calm), 1.10 or higher -> 0 (near-term fear)
  breadth         percent of the 11 S&P 500 sector ETFs above their 200-day average (a breadth proxy)
  credit          where the HYG/TLT ratio ranks among the last 252 days (high = credit markets calm)
If a component can't be computed, the remaining weights are scaled up and the gap is reported.
"""
import json

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS macro (
    asof TEXT PRIMARY KEY, score REAL, label TEXT, components TEXT, inputs TEXT, missing TEXT);
"""


def line(x, x_best, x_worst):
    """100 at x_best, 0 at x_worst, straight line between, clipped to 0-100."""
    s = (x - x_worst) / (x_best - x_worst) * 100
    return max(0.0, min(100.0, s))


def percentile_rank(values, x):
    return sum(1 for v in values if v < x) / len(values) * 100 if values else None


def check_weights(w=None):
    w = w or config.MACRO_WEIGHTS
    if abs(sum(w.values()) - 1.0) > 1e-6:
        raise ValueError(f"MACRO_WEIGHTS must add up to 1.0 (they add up to {sum(w.values()):.3f})")
    return w


def components(closes):
    """closes: {ticker: [(date, close), ...]} -> (scores dict, inputs dict)."""
    s, inp = {}, {}
    vix = [c for _, c in closes.get("^VIX", [])]
    if vix:
        inp["vix"] = vix[-1]
        s["vix_level"] = line(vix[-1], 12, 40)
        if len(vix) >= 60:
            pct = percentile_rank(vix[-252:], vix[-1])
            inp["vix_1y_percentile"] = pct
            s["vix_percentile"] = 100 - pct
    vix3m = [c for _, c in closes.get("^VIX3M", [])]
    if vix and vix3m:
        ratio = vix[-1] / vix3m[-1]
        inp["vix_vix3m_ratio"] = ratio
        s["term_structure"] = line(ratio, 0.80, 1.10)
    above, counted = 0, 0
    for t in config.BREADTH_ETFS:
        c = [x for _, x in closes.get(t, [])]
        if len(c) >= 200:
            counted += 1
            above += c[-1] > sum(c[-200:]) / 200
    if counted >= len(config.BREADTH_ETFS) // 2:
        inp["sectors_above_200d"] = f"{above} of {counted}"
        s["breadth"] = above / counted * 100
    hyg, tlt = dict(closes.get("HYG", [])), dict(closes.get("TLT", []))
    days = sorted(set(hyg) & set(tlt))
    if len(days) >= 60:
        ratio = [hyg[d] / tlt[d] for d in days][-252:]
        inp["hyg_tlt_ratio"] = ratio[-1]
        s["credit"] = percentile_rank(ratio, ratio[-1])
    return s, inp


def score(closes, weights=None):
    w = check_weights(weights)
    s, inp = components(closes)
    have = {k: v for k, v in s.items() if k in w}
    missing = [k for k in w if k not in have]
    if not have:
        return {"score": None, "label": "unavailable", "components": {}, "inputs": inp, "missing": missing}
    total_w = sum(w[k] for k in have)
    blended = sum(have[k] * w[k] for k in have) / total_w
    label = ("Calm" if blended >= config.MACRO_CALM else "Stressed" if blended < config.MACRO_STRESSED else "Mixed")
    return {"score": round(blended, 1), "label": label, "inputs": inp, "missing": missing,
            "components": {k: {"score": round(v, 1), "weight": w[k]} for k, v in have.items()}}


def run(con, asof, provider):
    con.executescript(SCHEMA)
    tickers = ["^VIX", "^VIX3M", "HYG", "TLT"] + config.BREADTH_ETFS
    closes, errors = {}, []
    for t in tickers:
        try:
            closes[t] = provider.closes(t)
        except Exception as e:
            errors.append(f"{t}: {e}")
    result = score(closes)
    result["data_errors"] = errors
    con.execute("INSERT OR REPLACE INTO macro VALUES (?,?,?,?,?,?)",
                (asof, result["score"], result["label"], json.dumps(result["components"]),
                 json.dumps(result["inputs"]), json.dumps(result["missing"])))
    con.commit()
    return result
