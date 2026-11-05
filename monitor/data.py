"""Market data pull (yfinance).

For each underlying: current spot price, and for tickers you hold options on, the full option chain
across every listed expiry, with bid, ask, last, IV, volume and open interest per contract.
Mark = mid (bid+ask)/2 when both exist, else last. For shares, mark = current spot.
"""
import datetime as dt
import math


def _clean(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def mark_from(bid, ask, last):
    if bid and ask and bid > 0 and ask > 0:
        return (bid + ask) / 2
    return last if last and last > 0 else None


class YahooProvider:
    """Thin wrapper around yfinance so tests can swap in a fake provider."""

    def __init__(self):
        import yfinance  # imported here so other layers can import this module without yfinance
        self.yf = yfinance

    def spot(self, ticker):
        t = self.yf.Ticker(ticker)
        try:
            price = _clean(t.fast_info["last_price"])
        except Exception:
            price = None
        if not price:
            hist = t.history(period="5d")
            price = _clean(hist["Close"].iloc[-1]) if len(hist) else None
        return price

    def sector(self, ticker):
        info = self.yf.Ticker(ticker).info or {}
        if info.get("sector"):
            return info["sector"]
        if info.get("quoteType") == "ETF":
            return f"{info.get('category') or 'Fund'} (ETF)"
        return None

    def expiries(self, ticker):
        return list(self.yf.Ticker(ticker).options)

    def chain(self, ticker, expiry):
        ch = self.yf.Ticker(ticker).option_chain(expiry)
        rows = []
        for kind, df in (("call", ch.calls), ("put", ch.puts)):
            for _, r in df.iterrows():
                rows.append({"option_type": kind, "strike": _clean(r.get("strike")),
                             "contract_symbol": r.get("contractSymbol"), "bid": _clean(r.get("bid")),
                             "ask": _clean(r.get("ask")), "last": _clean(r.get("lastPrice")),
                             "iv": _clean(r.get("impliedVolatility")), "volume": _clean(r.get("volume")),
                             "open_interest": _clean(r.get("openInterest"))})
        return rows


def pull(ticker, with_chain, provider):
    """Return one snapshot dict for an underlying."""
    snap = {"ticker": ticker, "pulled_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "spot": provider.spot(ticker), "expiries": [], "contracts": [], "errors": []}
    if not with_chain:
        return snap
    try:
        snap["expiries"] = provider.expiries(ticker)
    except Exception as e:
        snap["errors"].append(f"could not list expiries: {e}")
        return snap
    for exp in snap["expiries"]:
        try:
            for row in provider.chain(ticker, exp):
                row["expiry"] = exp
                row["mark"] = mark_from(row.get("bid"), row.get("ask"), row.get("last"))
                snap["contracts"].append(row)
        except Exception as e:
            snap["errors"].append(f"{exp}: {e}")
    return snap
