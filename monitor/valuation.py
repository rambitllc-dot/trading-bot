"""Value each position against the latest pulled data.

Per position: mark, current value, unrealized P&L ($ and %), DTE (options), progress to target and
progress to stop as percentages with a plain-English phrase, and Greeks (options).
"""
import datetime as dt

from . import config, plan
from .greeks import bs_greeks


def find_contract(snap, p):
    for c in snap.get("contracts", []):
        if (c["expiry"] == p["expiry"] and c["option_type"] == p["option_type"]
                and c.get("strike") is not None and abs(c["strike"] - p["strike"]) < 1e-6):
            return c
    return None


def progress(entry, mark, target, stop):
    """Percent of the way from entry toward target, and from entry toward stop (long positions)."""
    to_target = to_stop = None
    if mark is not None and target is not None and target != entry:
        to_target = (mark - entry) / (target - entry) * 100
    if mark is not None and stop is not None and stop != entry:
        to_stop = (entry - mark) / (entry - stop) * 100
    return to_target, to_stop


def describe(to_target, to_stop):
    if to_target is not None and to_target >= 100:
        return "at or past your target"
    if to_stop is not None and to_stop >= 100:
        return "at or past your stop"
    parts = []
    if to_target is not None:
        parts.append(f"{max(to_target, 0):.0f}% of the way from entry to target" if to_target > 0
                     else "not moving toward target yet")
    if to_stop is not None and to_stop > 0:
        parts.append(f"{to_stop:.0f}% of the way from entry to stop")
    return "; ".join(parts) if parts else "no target or stop set"


def value_position(p, snap, asof, rate=config.RISK_FREE_RATE):
    if p["asset_type"] == "cash":
        amt = p["contracts"]
        return {"position_id": p["id"], "ticker": "CASH", "asset_type": "cash", "option_type": None, "strike": None,
                "expiry": None, "contracts": amt, "entry_price": 1.0, "target_price": None, "stop_price": None,
                "add_below": None, "spot": 1.0, "mark": 1.0, "value": amt, "cost": amt, "pnl": 0.0, "pnl_pct": 0.0,
                "status": "ok", "progress_target": None, "progress_stop": None, "progress_text": "cash",
                "action": "HOLD", "action_reason": "cash"}
    asof_date = dt.date.fromisoformat(asof)
    spot = snap.get("spot") if snap else None
    out = {"position_id": p["id"], "ticker": p["ticker"], "asset_type": p["asset_type"],
           "option_type": p.get("option_type"), "strike": p.get("strike"), "expiry": p.get("expiry"),
           "contracts": p["contracts"], "entry_price": p["entry_price"], "target_price": p.get("target_price"),
           "stop_price": p.get("stop_price"), "add_below": p.get("add_below"), "spot": spot, "status": "ok"}
    if p["asset_type"] == "shares":
        mult, mark = 1, spot
        if mark is None:
            out["status"] = "no price from the data feed"
    else:
        mult = config.CONTRACT_MULTIPLIER
        dte = (dt.date.fromisoformat(p["expiry"]) - asof_date).days
        out["dte"] = dte
        c = find_contract(snap or {}, p)
        if dte < 0:
            out["status"] = "expired"
            mark = None
        elif c is None:
            out["status"] = "contract not found in the chain (check strike and expiry)"
            mark = None
        else:
            mark, iv = c.get("mark"), c.get("iv")
            out.update({"iv": iv, "bid": c.get("bid"), "ask": c.get("ask"), "last": c.get("last"),
                        "volume": c.get("volume"), "open_interest": c.get("open_interest")})
            if mark is None:
                out["status"] = "no bid/ask or last price for this contract"
            g = bs_greeks(p["option_type"], spot, p["strike"], max(dte, 0) / 365.0, rate, iv) if iv else None
            if g:
                n = p["contracts"] * mult
                out.update({"delta": g["delta"], "gamma": g["gamma"], "theta": g["theta"], "vega": g["vega"],
                            "pos_delta": g["delta"] * n, "pos_theta": g["theta"] * n, "pos_vega": g["vega"] * n})
    cost = p["entry_price"] * p["contracts"] * mult
    out["mark"], out["cost"] = mark, cost
    if mark is not None:
        out["value"] = mark * p["contracts"] * mult
        out["pnl"] = out["value"] - cost
        out["pnl_pct"] = out["pnl"] / cost * 100 if cost else None
    if p["asset_type"] == "shares" and mark is not None:
        out.update({"delta": 1.0, "pos_delta": p["contracts"]})  # each share moves $1 per $1
    out["progress_target"], out["progress_stop"] = progress(p["entry_price"], mark, p.get("target_price"),
                                                             p.get("stop_price"))
    out["progress_text"] = describe(out["progress_target"], out["progress_stop"])
    out["action"], out["action_reason"] = plan.for_position(out)
    return out


def value_book(book, snaps, asof, rate=config.RISK_FREE_RATE):
    rows = [value_position(p, snaps.get(p["ticker"]), asof, rate) for p in book]
    for r, p in zip(rows, book):
        r.setdefault("entry_date", p.get("entry_date"))  # used by the rotation's minimum-hold rule and the scorecard
    valued = [r for r in rows if r.get("value") is not None]
    totals = {"value": sum(r["value"] for r in valued), "cost": sum(r["cost"] for r in valued),
              "positions": len(rows), "priced": len(valued),
              "net_delta": sum(r.get("pos_delta") or 0 for r in rows),
              "daily_theta": sum(r.get("pos_theta") or 0 for r in rows)}
    totals["pnl"] = totals["value"] - totals["cost"]
    totals["pnl_pct"] = totals["pnl"] / totals["cost"] * 100 if totals["cost"] else None
    return rows, totals
