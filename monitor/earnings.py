"""Earnings guard: don't buy a stock in the days right before its earnings report.

Earnings can make a stock jump or drop 10-20% overnight, past any stop, so the 6% stop can't protect a stock
bought just before its report. Candidates reporting within EARNINGS_BLACKOUT_DAYS business days are skipped
when choosing what to buy (swaps, stop-out replacements, new money). Stocks you already hold aren't sold for
this; you get a heads-up in the evening report instead.

Dates come from Yahoo Finance (yfinance), checked only for the strongest candidates and your holdings, and
cached for the day in monitor/output/earnings_cache.json.
"""
import datetime as dt
import json
import os

from . import config, sectors

CACHE_FILE = os.path.join(config.BASE_DIR, "output", "earnings_cache.json")


def fetch_next(ticker, asof):
    """Next earnings date on or after asof (YYYY-MM-DD), or None if unknown."""
    import yfinance as yf
    cal = yf.Ticker(ticker.replace(".", "-")).calendar
    raw = cal.get("Earnings Date") if isinstance(cal, dict) else None
    dates = raw if isinstance(raw, (list, tuple)) else [raw] if raw else []
    out = sorted(d.isoformat() if hasattr(d, "isoformat") else str(d)[:10] for d in dates if d)
    out = [d[:10] for d in out if d[:10] >= asof]
    return out[0] if out else None


def business_days(start, end):
    a, b = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        n += d.weekday() < 5
    return n


def upcoming(asof, tickers, fetch=None, cache_file=None):
    """{ticker: next earnings date or None}, using today's cache where possible."""
    fetch = fetch or fetch_next
    path = cache_file or CACHE_FILE
    try:
        cache = json.load(open(path))
    except (OSError, ValueError):
        cache = {}
    if cache.get("asof") != asof:
        cache = {"asof": asof, "dates": {}}
    out = {}
    for t in tickers:
        if t in sectors.ETF_SECTORS:
            continue  # funds don't report earnings
        if t not in cache["dates"]:
            try:
                cache["dates"][t] = fetch(t, asof)
            except Exception:  # noqa: BLE001 - unknown date: don't block on it
                cache["dates"][t] = None
        out[t] = cache["dates"][t]
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(cache, f, indent=1, sort_keys=True)
    except OSError:
        pass
    return out


def make_blocker(asof, fetch=None, cache_file=None):
    """A function the rotation calls with a list of tickers; returns {ticker: reason} for those reporting soon."""
    def blocker(tickers):
        out = {}
        for t, d in upcoming(asof, tickers, fetch, cache_file).items():
            if d and business_days(asof, d) <= config.EARNINGS_BLACKOUT_DAYS:
                out[t] = d
        return out
    return blocker
