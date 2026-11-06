"""Read your current positions and cash from Interactive Brokers (read-only) and update positions.json.

Uses IBKR's Flex Web Service: an Activity Flex Query with the "Open Positions" and "Cash Report" sections,
fetched with a read-only token. The token cannot trade or move money.
Needs two GitHub secrets: IBKR_FLEX_TOKEN and IBKR_FLEX_QUERY_ID.

IB refreshes these reports once a day after the close, so they show the previous trading day's holdings.
To never overwrite newer information, the sync is skipped while positions.json holds a position bought
after the report's date (for example right after a swap); it catches up once IB's report includes it.
Your own levels (target_price, stop_price, add_below) and buy dates are kept for positions that remain.
"""
import datetime as dt
import json
import os
import time
import xml.etree.ElementTree as ET

import requests

from . import config

SEND_URL = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService/SendRequest"
HEADERS = {"User-Agent": "portfolio-monitor/1.0"}
KEEP = ("target_price", "stop_price", "add_below", "entry_date")


def _date(s):
    s = (s or "").strip().replace("-", "")[:8]
    try:
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8])).isoformat()
    except ValueError:
        return None


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch(token, query_id, tries=8, wait=5):
    r = requests.get(SEND_URL, params={"t": token, "q": query_id, "v": 3}, headers=HEADERS, timeout=30)
    root = ET.fromstring(r.text)
    if root.findtext("Status") != "Success":
        raise RuntimeError(f"IB refused the request: {root.findtext('ErrorMessage') or r.text[:200]}")
    ref, url = root.findtext("ReferenceCode"), root.findtext("Url")
    for _ in range(tries):
        time.sleep(wait)  # IB allows about one request per second; the report takes a few seconds to build
        g = requests.get(url, params={"t": token, "q": ref, "v": 3}, headers=HEADERS, timeout=60)
        if "<FlexQueryResponse" in g.text:
            return g.text
        status = ET.fromstring(g.text)
        if status.findtext("ErrorCode") not in ("1019", "1018"):  # 1019: still generating, 1018: too many requests
            raise RuntimeError(f"IB statement error: {status.findtext('ErrorMessage') or g.text[:200]}")
    raise RuntimeError("IB statement wasn't ready in time; will try again next run")


def parse(xml_text):
    """-> (report date ISO, [positions], cash amount or None)"""
    root = ET.fromstring(xml_text)
    stmt = root.find(".//FlexStatement")
    report_date = _date(stmt.get("toDate")) if stmt is not None else None
    out = []
    for p in root.iter("OpenPosition"):
        if p.get("levelOfDetail", "SUMMARY").upper() not in ("SUMMARY", ""):
            continue
        qty = _f(p.get("position"))
        if not qty:
            continue
        cat = (p.get("assetCategory") or "").upper()
        mult = _f(p.get("multiplier")) or 1.0
        cost_money = _f(p.get("costBasisMoney"))
        per_share = (cost_money / (qty * mult) if cost_money and qty else _f(p.get("costBasisPrice")))
        if cat == "STK":
            out.append({"asset_type": "shares", "ticker": p.get("symbol"), "contracts": qty,
                        "entry_price": round(per_share, 4), "note": "Interactive Brokers (synced)"})
        elif cat == "OPT":
            out.append({"asset_type": "option", "ticker": p.get("underlyingSymbol") or p.get("symbol", "").split()[0],
                        "option_type": "call" if (p.get("putCall") or "").upper().startswith("C") else "put",
                        "strike": _f(p.get("strike")), "expiry": _date(p.get("expiry")), "contracts": qty,
                        "entry_price": round(per_share, 4), "note": "Interactive Brokers (synced)"})
    cash = None
    for c in root.iter("CashReportCurrency"):
        if c.get("currency") in ("BASE_SUMMARY", "USD"):
            cash = _f(c.get("endingCash"))
            if c.get("currency") == "BASE_SUMMARY":
                break
    return report_date, out, cash


def key(p):
    if p["asset_type"] == "option":
        return (p["ticker"], p["option_type"], float(p["strike"]), p["expiry"])
    return (p["ticker"], p["asset_type"])


def merge(current, synced, cash, report_date):
    """Build the new positions.json content, keeping your own levels and buy dates."""
    old = {key(p): p for p in current if p.get("asset_type") != "cash"}
    new = []
    for p in synced:
        prev = old.get(key(p), {})
        for k in KEEP:
            if prev.get(k) is not None:
                p[k] = prev[k]
        p.setdefault("entry_date", report_date)
        for k in ("target_price", "stop_price"):
            p.setdefault(k, None)
        new.append(p)
    if cash is not None:
        new.append({"asset_type": "cash", "amount": round(cash, 2), "note": f"IB cash as of {report_date} (synced)"})
    return new


def sync(path=None, fetcher=None):
    """Returns a short status line. Never raises: a failed sync leaves positions.json as it was."""
    token, qid = os.environ.get("IBKR_FLEX_TOKEN"), os.environ.get("IBKR_FLEX_QUERY_ID")
    if not (token and qid) and fetcher is None:
        return "IB sync off (no IBKR_FLEX_TOKEN / IBKR_FLEX_QUERY_ID)"
    path = path or config.POSITIONS_FILE
    try:
        xml_text = (fetcher or fetch)(token, qid)
        report_date, synced, cash = parse(xml_text)
        with open(path) as f:
            current = json.load(f)
        newest = max((p.get("entry_date") or "" for p in current), default="")
        if report_date and newest > report_date:
            return (f"IB sync waiting: IB's report is from {report_date}, but positions.json has a buy from "
                    f"{newest}; it will sync once IB's report includes it")
        if not synced and current:
            return "IB sync skipped: the report had no open positions (check the Flex Query has Open Positions)"
        merged = merge(current, synced, cash, report_date)
        with open(path, "w") as f:
            f.write(json.dumps(merged, indent=2) + "\n")
        names = ", ".join(p["ticker"] for p in synced)
        return f"IB sync: {len(synced)} position(s) as of {report_date} ({names})" + \
               (f", cash {cash:,.2f}" if cash is not None else "")
    except Exception as e:  # noqa: BLE001 - a sync problem must never stop the monitor
        return f"IB sync failed, kept positions.json as it was: {e}"


if __name__ == "__main__":
    print(sync())
