"""Layer 2: portfolio analytics on top of Layer 1's valuation.

- Allocation: percent of total value by ticker and by sector, with concentration flags (informational).
- Aggregate Greeks: net delta in share terms, total daily theta in dollars, net vega ($ per 1 IV point).
- IV environment per option: current IV, IV rank and IV percentile from stored daily snapshots,
  "building history" until there's enough, and rich/cheap flags.
- Expiry watch: options with few days left, so upcoming time decay and roll decisions are visible.
It surfaces facts only. It never advises trades.
"""
from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS sectors (ticker TEXT PRIMARY KEY, sector TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS analytics (
    asof TEXT PRIMARY KEY, total_value REAL, total_cost REAL, pnl REAL, pnl_pct REAL,
    net_delta REAL, daily_theta REAL, net_vega REAL, n_flags INTEGER);
CREATE TABLE IF NOT EXISTS allocation (
    asof TEXT, kind TEXT, name TEXT, value REAL, pct REAL, cap_pct REAL, over_cap INTEGER,
    PRIMARY KEY (asof, kind, name));
CREATE TABLE IF NOT EXISTS iv_environment (
    asof TEXT, position_id TEXT, iv REAL, iv_rank REAL, iv_percentile REAL, history_days INTEGER,
    label TEXT, PRIMARY KEY (asof, position_id));
CREATE TABLE IF NOT EXISTS flags (asof TEXT, kind TEXT, severity TEXT, position_id TEXT, message TEXT);
"""


def sector_of(con, ticker, provider=None):
    if ticker in config.SECTORS:
        return config.SECTORS[ticker]
    row = con.execute("SELECT sector FROM sectors WHERE ticker=?", (ticker,)).fetchone()
    if row:
        return row[0]
    sector = None
    if provider is not None and hasattr(provider, "sector"):
        try:
            sector = provider.sector(ticker)
        except Exception:
            sector = None
    if sector:
        con.execute("INSERT OR REPLACE INTO sectors VALUES (?,?,?)", (ticker, sector, "yahoo"))
        con.commit()
    return sector or "Unknown"


def allocation(con, rows, provider=None):
    priced = [r for r in rows if r.get("value") is not None]
    total = sum(abs(r["value"]) for r in priced)
    by_ticker, by_sector = {}, {}
    for r in priced:
        by_ticker[r["ticker"]] = by_ticker.get(r["ticker"], 0) + abs(r["value"])
        s = sector_of(con, r["ticker"], provider)
        by_sector[s] = by_sector.get(s, 0) + abs(r["value"])
    def table(d, cap, kind):
        return [{"kind": kind, "name": k, "value": v, "pct": v / total * 100 if total else 0, "cap_pct": cap,
                 "over_cap": bool(total and v / total * 100 > cap)}
                for k, v in sorted(d.items(), key=lambda kv: -kv[1])]
    return (table(by_ticker, config.TICKER_CAP_PCT, "ticker"),
            table(by_sector, config.SECTOR_CAP_PCT, "sector"), total)


def aggregate_greeks(rows):
    return {"net_delta": sum(r.get("pos_delta") or 0 for r in rows),
            "daily_theta": sum(r.get("pos_theta") or 0 for r in rows),
            "net_vega": sum(r.get("pos_vega") or 0 for r in rows),
            "net_gamma": sum((r.get("gamma") or 0) * r["contracts"] * config.CONTRACT_MULTIPLIER
                             for r in rows if r["asset_type"] == "option")}


def iv_history(con, r, asof):
    """This contract's stored IV, one value per day, oldest first, up to and including `asof`."""
    cur = con.execute(
        "SELECT iv FROM chain WHERE ticker=? AND expiry=? AND option_type=? AND ABS(strike-?)<1e-6 "
        "AND asof<=? AND iv IS NOT NULL AND iv>0 ORDER BY asof DESC LIMIT ?",
        (r["ticker"], r["expiry"], r["option_type"], r["strike"], asof, config.IV_LOOKBACK_DAYS))
    return [x[0] for x in cur.fetchall()][::-1]


def iv_environment(con, r, asof):
    hist = iv_history(con, r, asof)
    iv = r.get("iv")
    out = {"position_id": r["position_id"], "iv": iv, "history_days": len(hist),
           "iv_rank": None, "iv_percentile": None}
    if iv is None:
        out["label"] = "no IV available"
    elif len(hist) < config.IV_MIN_HISTORY_DAYS:
        out["label"] = f"building history: {len(hist)} of {config.IV_MIN_HISTORY_DAYS} days"
    else:
        lo, hi = min(hist), max(hist)
        out["iv_rank"] = (iv - lo) / (hi - lo) * 100 if hi > lo else 50.0
        out["iv_percentile"] = sum(1 for x in hist if x < iv) / len(hist) * 100
        out["label"] = ("rich" if out["iv_rank"] > config.IV_RICH else
                        "cheap" if out["iv_rank"] < config.IV_CHEAP else "normal")
    return out


def name_of(r):
    if r["asset_type"] == "option":
        return f"{r['ticker']} {r['strike']:g} {r['option_type']} {r['expiry']}"
    return f"{r['ticker']} shares"


def analyze(con, rows, asof, provider=None):
    con.executescript(SCHEMA)
    tickers, sectors, total = allocation(con, rows, provider)
    greeks = aggregate_greeks(rows)
    flags = []
    for a in tickers + sectors:
        if a["over_cap"]:
            flags.append({"kind": "concentration", "severity": "info", "position_id": None,
                          "message": f"{a['name']} is {a['pct']:.0f}% of the book (cap {a['cap_pct']:.0f}%)."})
    ivs = []
    for r in rows:
        if r["asset_type"] != "option" or r.get("status") == "expired":
            continue
        env = iv_environment(con, r, asof)
        ivs.append(env)
        if env["label"] in ("rich", "cheap"):
            flags.append({"kind": f"iv_{env['label']}", "severity": "info", "position_id": r["position_id"],
                          "message": f"{name_of(r)}: IV {env['iv'] * 100:.0f}% is {env['label']} vs its last "
                                     f"{env['history_days']} days (IV rank {env['iv_rank']:.0f})."})
        dte = r.get("dte")
        if dte is not None and 0 <= dte < config.DTE_WATCH_DAYS:
            flags.append({"kind": "expiry_watch", "severity": "warn", "position_id": r["position_id"],
                          "message": f"{name_of(r)}: {dte} days to expiry (under {config.DTE_WATCH_DAYS}). "
                                     f"Time decay usually speeds up in the final weeks."})
    priced = [r for r in rows if r.get("value") is not None]
    cost = sum(r["cost"] for r in priced)
    summary = {"asof": asof, "total_value": total, "total_cost": cost, "pnl": total - cost,
               "pnl_pct": (total - cost) / cost * 100 if cost else None, **greeks,
               "allocation": {"ticker": tickers, "sector": sectors}, "iv_environment": ivs, "flags": flags}
    store(con, summary)
    return summary


def store(con, s):
    a = s["asof"]
    for table in ("allocation", "iv_environment", "flags"):
        con.execute(f"DELETE FROM {table} WHERE asof=?", (a,))
    con.execute("INSERT OR REPLACE INTO analytics VALUES (?,?,?,?,?,?,?,?,?)",
                (a, s["total_value"], s["total_cost"], s["pnl"], s["pnl_pct"], s["net_delta"],
                 s["daily_theta"], s["net_vega"], len(s["flags"])))
    con.executemany("INSERT INTO allocation VALUES (?,?,?,?,?,?,?)",
                    [(a, x["kind"], x["name"], x["value"], x["pct"], x["cap_pct"], int(x["over_cap"]))
                     for x in s["allocation"]["ticker"] + s["allocation"]["sector"]])
    con.executemany("INSERT INTO iv_environment VALUES (?,?,?,?,?,?,?)",
                    [(a, x["position_id"], x["iv"], x["iv_rank"], x["iv_percentile"], x["history_days"], x["label"])
                     for x in s["iv_environment"]])
    con.executemany("INSERT INTO flags VALUES (?,?,?,?,?)",
                    [(a, f["kind"], f["severity"], f["position_id"], f["message"]) for f in s["flags"]])
    con.commit()


def money(v):
    return f"{'-' if v < 0 else ''}${abs(v):,.2f}"


def summary_text(s, rows):
    by_id = {r["position_id"]: r for r in rows}
    L = ["", "ANALYTICS",
         f"Net delta {s['net_delta']:,.0f} shares-equivalent · daily theta {money(s['daily_theta'])} "
         f"(what the book loses per day if nothing moves) · net vega {money(s['net_vega'])} per IV point", ""]
    for kind in ("ticker", "sector"):
        L.append(f"By {kind}: " + ", ".join(f"{x['name']} {x['pct']:.0f}%{' (over cap)' if x['over_cap'] else ''}"
                                             for x in s["allocation"][kind]))
    if s["iv_environment"]:
        L.append("")
        L.append("IV environment:")
        for e in s["iv_environment"]:
            r = by_id[e["position_id"]]
            iv = f"IV {e['iv'] * 100:.0f}%" if e["iv"] else "IV n/a"
            rank = (f", rank {e['iv_rank']:.0f}, percentile {e['iv_percentile']:.0f}" if e["iv_rank"] is not None else "")
            L.append(f"- {name_of(r)}: {iv}{rank} ({e['label']})")
    L.append("")
    L.append("Flags:" if s["flags"] else "Flags: none")
    L += [f"- [{f['severity']}] {f['message']}" for f in s["flags"]]
    return "\n".join(L)
