"""Load and check positions.json.

Two row types live in one book:
  option: ticker, option_type (call/put), strike, expiry (YYYY-MM-DD), entry_price (per-share premium),
          contracts, entry_date, target_price (optional, per share), stop_price (optional, per share)
  shares: ticker, entry_price (per share), contracts (= number of shares), entry_date,
          target_price, stop_price
For options, entry/target/stop are PER SHARE; one contract is 100 shares, so a contract's
dollar value is price x 100.
"""
import datetime as dt
import json

from . import config


class PositionError(ValueError):
    pass


def make_id(p):
    if p["asset_type"] == "option":
        strike = f"{float(p['strike']):g}"
        return f"{p['ticker']}-{strike}{p['option_type'][0].upper()}-{p['expiry']}"
    return f"{p['ticker']}-shares"


def _date(value, field, row):
    try:
        return dt.date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise PositionError(f"{row}: {field} must be YYYY-MM-DD, got {value!r}")


def _num(p, field, row, required=True):
    if p.get(field) in (None, ""):
        if required:
            raise PositionError(f"{row}: missing {field}")
        return None
    try:
        return float(p[field])
    except (TypeError, ValueError):
        raise PositionError(f"{row}: {field} must be a number, got {p[field]!r}")


def normalize(p, row="position"):
    """Return a clean copy of one position, raising PositionError on bad input."""
    kind = str(p.get("asset_type", "")).lower()
    if kind not in ("option", "shares"):
        raise PositionError(f"{row}: asset_type must be 'option' or 'shares'")
    out = {"asset_type": kind, "ticker": str(p.get("ticker", "")).upper().strip()}
    if not out["ticker"]:
        raise PositionError(f"{row}: missing ticker")
    out["entry_price"] = _num(p, "entry_price", row)
    out["contracts"] = _num(p, "contracts", row)
    out["entry_date"] = _date(p.get("entry_date"), "entry_date", row) if p.get("entry_date") else None
    out["target_price"] = _num(p, "target_price", row, required=False)
    out["stop_price"] = _num(p, "stop_price", row, required=False)
    if kind == "option":
        ot = str(p.get("option_type", "")).lower()
        if ot not in ("call", "put"):
            raise PositionError(f"{row}: option_type must be 'call' or 'put'")
        out["option_type"] = ot
        out["strike"] = _num(p, "strike", row)
        out["expiry"] = _date(p.get("expiry"), "expiry", row)
    if p.get("note"):
        out["note"] = p["note"]
    out["id"] = str(p.get("id") or make_id(out))
    return out


def load(path=None):
    with open(path or config.POSITIONS_FILE) as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        raise PositionError("positions.json must be a list of positions")
    book = [normalize(p, f"row {i + 1}") for i, p in enumerate(raw)]
    ids = [p["id"] for p in book]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise PositionError(f"duplicate position ids: {', '.join(sorted(dupes))}")
    return book
