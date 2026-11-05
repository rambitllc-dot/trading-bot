"""Layer 3b: daily Claude news analysis per held name.

For each underlying in the book: pull recent headlines (default last 3 days), send them to Claude
through the API, and get back a short summary of what actually happened, a sentiment read
(positive / neutral / negative), the key drivers, and flags for anything that specifically affects a
position you hold. It is NOT a trade trigger: Claude summarizes and flags; it never says buy or sell.

Each name's analysis is cached per day in SQLite, so re-runs don't call (or bill) the API again.
This is the only paid part of the system; a call with a handful of headlines costs a small fraction
of a cent on Claude Haiku 5.5.
"""
import datetime as dt
import json
import os
import re

import requests

from . import config

API_URL = "https://api.anthropic.com/v1/messages"
SCHEMA = """
CREATE TABLE IF NOT EXISTS news_analysis (
    asof TEXT, ticker TEXT, headlines TEXT, summary TEXT, sentiment TEXT, drivers TEXT,
    position_flags TEXT, model TEXT, input_tokens INTEGER, output_tokens INTEGER, cost_usd REAL,
    status TEXT, created_at TEXT, PRIMARY KEY (asof, ticker));
"""

SYSTEM = (
    "You summarize market news for a personal portfolio monitor. Report facts only. "
    "Never recommend buying, selling, holding, adding, trimming, hedging or rolling, and never predict prices. "
    "Base everything only on the headlines given; if they don't say something, don't claim it. "
    "Reply with a single JSON object and nothing else."
)


def recent(headlines, window_days=None, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=window_days or config.NEWS_WINDOW_DAYS)
    out = []
    for h in headlines:
        try:
            when = dt.datetime.fromisoformat(str(h.get("published")).replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
        if when >= cutoff:
            out.append({**h, "published": when.strftime("%Y-%m-%d %H:%M UTC")})
    out.sort(key=lambda h: h["published"], reverse=True)
    return out[:config.NEWS_MAX_HEADLINES]


def describe_position(p):
    if p["asset_type"] == "option":
        s = (f"{p['id']}: {p['contracts']:g} {p['option_type']} contract(s), strike {p['strike']:g}, "
             f"expiring {p['expiry']}, bought at {p['entry_price']:g}/share")
    else:
        s = f"{p['id']}: {p['contracts']:g} shares bought at {p['entry_price']:g}"
    if p.get("target_price"):
        s += f", target {p['target_price']:g}"
    if p.get("stop_price"):
        s += f", stop {p['stop_price']:g}"
    return s


def build_prompt(ticker, headlines, held, macro_label=None):
    lines = [f"Ticker: {ticker}"]
    if macro_label:
        lines.append(f"General market environment today: {macro_label}")
    lines.append("Positions held in this name:")
    lines += [f"- {describe_position(p)}" for p in held]
    lines.append("")
    lines.append("Headlines (newest first):")
    for h in headlines:
        lines.append(f"- [{h['published']}] {h['title']} ({h.get('publisher') or 'unknown source'})"
                     + (f": {h['summary'][:300]}" if h.get("summary") else ""))
    lines.append("")
    lines.append(
        'Return JSON with exactly these keys: '
        '"summary" (2-3 plain sentences on what actually happened), '
        '"sentiment" ("positive", "neutral" or "negative" for this company), '
        '"drivers" (list of up to 4 short phrases naming what is behind it), '
        '"position_flags" (list of {"position_id": ..., "flag": ...} for anything in these headlines that '
        'specifically affects one of the positions above, such as an event before an option\'s expiry; '
        'empty list if nothing does). No buy/sell/hold language.')
    return "\n".join(lines)


def call_claude(prompt, api_key, model=None):
    r = requests.post(API_URL, timeout=60,
                      headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                               "content-type": "application/json"},
                      json={"model": model or config.CLAUDE_MODEL, "max_tokens": 1024, "system": SYSTEM,
                            "messages": [{"role": "user", "content": prompt}]})
    if r.status_code >= 400:
        raise RuntimeError(f"Claude API {r.status_code}: {r.text[:200]}")
    body = r.json()
    text = "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")
    return text, body.get("usage", {})


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("Claude's reply had no JSON object")
    d = json.loads(m.group(0))
    sentiment = str(d.get("sentiment", "neutral")).lower()
    return {"summary": str(d.get("summary", "")).strip(),
            "sentiment": sentiment if sentiment in ("positive", "neutral", "negative") else "neutral",
            "drivers": [str(x) for x in (d.get("drivers") or [])][:4],
            "position_flags": [f for f in (d.get("position_flags") or []) if isinstance(f, dict) and f.get("flag")]}


def cached(con, asof, ticker):
    row = con.execute("SELECT * FROM news_analysis WHERE asof=? AND ticker=? AND status='ok'", (asof, ticker)).fetchone()
    if not row:
        return None
    cols = [d[0] for d in con.execute("SELECT * FROM news_analysis LIMIT 0").description]
    d = dict(zip(cols, row))
    for k in ("headlines", "drivers", "position_flags"):
        d[k] = json.loads(d[k] or "[]")
    d["cached"] = True
    return d


def save(con, asof, ticker, rec):
    con.execute("INSERT OR REPLACE INTO news_analysis VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (asof, ticker, json.dumps(rec.get("headlines", [])), rec.get("summary"), rec.get("sentiment"),
                 json.dumps(rec.get("drivers", [])), json.dumps(rec.get("position_flags", [])), rec.get("model"),
                 rec.get("input_tokens"), rec.get("output_tokens"), rec.get("cost_usd"), rec["status"],
                 dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
    con.commit()


def analyze_name(con, asof, ticker, held, provider, api_key, macro_label=None, caller=None):
    hit = cached(con, asof, ticker)
    if hit:
        return hit
    try:
        headlines = recent(provider.news(ticker))
    except Exception as e:
        return {"ticker": ticker, "status": f"could not fetch headlines: {e}"}
    rec = {"ticker": ticker, "headlines": headlines, "model": config.CLAUDE_MODEL}
    if not headlines:
        rec.update(status="ok", summary=f"No headlines in the last {config.NEWS_WINDOW_DAYS} days.",
                   sentiment="neutral", drivers=[], position_flags=[], cost_usd=0.0)
        save(con, asof, ticker, rec)
        return rec
    if not api_key and caller is None:
        rec.update(status="off: no ANTHROPIC_API_KEY set")
        return rec
    try:
        text, usage = (caller or call_claude)(build_prompt(ticker, headlines, held, macro_label), api_key)
        rec.update(parse(text))
        ids = {p["id"] for p in held}  # only keep flags about positions actually held in this name
        rec["position_flags"] = [f for f in rec["position_flags"] if f.get("position_id") in ids]
        rec["input_tokens"], rec["output_tokens"] = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
        rec["cost_usd"] = (rec["input_tokens"] * config.CLAUDE_PRICE_IN
                           + rec["output_tokens"] * config.CLAUDE_PRICE_OUT) / 1e6
        rec["status"] = "ok"
        save(con, asof, ticker, rec)
    except Exception as e:
        rec["status"] = f"analysis failed: {e}"
    return rec


def run(con, asof, book, provider, macro_label=None, caller=None):
    con.executescript(SCHEMA)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    out = []
    for ticker in sorted({p["ticker"] for p in book}):
        held = [p for p in book if p["ticker"] == ticker]
        out.append(analyze_name(con, asof, ticker, held, provider, api_key, macro_label, caller))
    return out
