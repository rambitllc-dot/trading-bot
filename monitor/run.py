"""Layer 1 runner: pull data, save snapshots, value the book.

Usage (from the repo folder):
    python -m monitor.run                 # today's date
    python -m monitor.run --asof 2026-11-05
--asof only stamps the run date for storage and comparisons; prices still come from the current
feed (there is no rebuilding of past option chains).
"""
import argparse
import datetime as dt
import json
import os
import sys

from . import alerts, analytics, config, data, levels, macro, news, notifier, performance, positions, rotation, scanner, storage, valuation


def market_today():
    """Today's date in New York, where US markets trade (GitHub's clock is UTC, a day ahead in the evening)."""
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def run(asof=None, positions_file=None, rate=config.RISK_FREE_RATE, provider=None, db=None, snap_dir=None,
        news_caller=None):
    asof = asof or market_today()
    dt.date.fromisoformat(asof)  # validates the format
    book = positions.load(positions_file)
    provider = provider or data.YahooProvider()
    option_tickers = {p["ticker"] for p in book if p["asset_type"] == "option"}
    con = storage.connect(db)
    snaps = {}
    for t in sorted({p["ticker"] for p in book if p["asset_type"] != "cash"}):
        snap = data.pull(t, t in option_tickers, provider)
        storage.save_snapshot(con, snap, asof, snap_dir)
        snaps[t] = snap
    rows, totals = valuation.value_book(book, snaps, asof, rate)
    storage.save_valuations(con, asof, rows)
    summary = analytics.analyze(con, rows, asof, provider)
    macro_result = macro.run(con, asof, provider)
    news_result = news.run(con, asof, book, provider, macro_result.get("label"), news_caller)
    if hasattr(provider, "bulk"):
        scan, bars = scanner.run(con, asof, provider, macro_result.get("label"), news_caller,
                                 extra_tickers=[p["ticker"] for p in book if p["asset_type"] != "cash"]
                                 + performance.tracked_tickers(con, asof=asof))
    else:
        scan, bars = {"screens": {}, "watchlist": [], "alerts": [], "news": [], "error": "scanner skipped (no bulk data)"}, {}
    sentiment = {n["ticker"]: n.get("sentiment") for n in news_result + scan.get("news", []) if n.get("status") == "ok"}
    auto = levels.apply(con, asof, rows, bars) if bars else []
    if auto:
        storage.save_valuations(con, asof, rows)
    rot = rotation.run(con, asof, rows, bars, sentiment) if bars else {"status": "no market data", "holdings": [],
                                                                         "top": [], "suggestions": []}
    swaps = {s["sell"]: s for s in rot.get("suggestions") or []}
    losing = {h["ticker"]: h for h in rot.get("holdings") or [] if h.get("losing")}
    for r in rows:  # flag losing holdings: first in line for the next swap
        h = losing.get(r["ticker"])
        if h and r["ticker"] not in swaps and r.get("action") in ("HOLD", "REVIEW"):
            r["action_reason"] = (f"{r.get('action_reason') or ''} · LOSING {h['pnl_pct']:.1f}%: "
                                  f"#{h['queue']} in line for the next swap").lstrip(" ·")
    if losing and not swaps:
        storage.save_valuations(con, asof, rows)
    if swaps:  # holdings to swap out get the SWAP label unless a stop/target already says SELL
        for r in rows:
            s = swaps.get(r["ticker"])
            if s and r.get("action") in ("HOLD", "REVIEW"):
                r["action"], r["action_reason"] = "SWAP", f"rotation: swap for {s['buy']} (rank #{s['buy_rank']})"
        storage.save_valuations(con, asof, rows)
    perf = performance.run(con, asof, rows, totals, bars)
    alert_list, diffs = alerts.build(con, asof, rows, summary, macro_result, news_result,
                                     scan["alerts"] + rotation.alert(rot))
    con.close()
    result = {"asof": asof, "totals": totals, "positions": rows, "analytics": summary,
              "macro": macro_result, "news": news_result, "alerts": alert_list, "chain_diffs": diffs, "scan": scan,
              "rotation": rot, "auto_levels": auto, "performance": perf,
              "data_errors": {t: s["errors"] for t, s in snaps.items() if s["errors"]}}
    out_dir = os.path.join(config.BASE_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "valuation_latest.json"), "w") as f:
        json.dump(result, f, indent=1)
    result["notifier"] = notifier.maybe_send(alert_list, asof)
    return result


def fmt(v, kind="money"):
    if v is None:
        return "-"
    if kind == "money":
        return f"{'-' if v < 0 else ''}${abs(v):,.2f}"
    if kind == "pct":
        return f"{v:+.1f}%"
    return f"{v:,.2f}"


def print_report(res):
    print(f"Portfolio as of {res['asof']}")
    t = res["totals"]
    print(f"Value {fmt(t['value'])} · cost {fmt(t['cost'])} · P&L {fmt(t['pnl'])} ({fmt(t['pnl_pct'], 'pct')}) · "
          f"net delta {t['net_delta']:,.0f} shares · theta {fmt(t['daily_theta'])}/day · "
          f"{t['priced']}/{t['positions']} positions priced\n")
    for r in res["positions"]:
        name = (f"{r['ticker']} {r['strike']:g} {r['option_type']} {r['expiry']} x{r['contracts']:g}"
                if r["asset_type"] == "option" else f"{r['ticker']} shares x{r['contracts']:g}")
        line = f"- {name}: mark {fmt(r['mark'])}, value {fmt(r.get('value'))}, P&L {fmt(r.get('pnl'))} " \
               f"({fmt(r.get('pnl_pct'), 'pct')})"
        if r["asset_type"] == "option":
            line += f", {r.get('dte')} days left"
            if r.get("delta") is not None:
                line += (f", IV {r['iv'] * 100:.0f}%, delta {r['delta']:.2f}, theta {fmt(r['pos_theta'])}/day, "
                         f"vega {fmt(r['pos_vega'])}/IV pt")
        line += f". {r['progress_text'][:1].upper() + r['progress_text'][1:]}."
        line += f" YOUR PLAN: {r['action']} ({r['action_reason']})."
        if r["status"] != "ok":
            line += f" [{r['status']}]"
        print(line)
    if res.get("analytics"):
        print(analytics.summary_text(res["analytics"], res["positions"]))
    m = res.get("macro")
    if m:
        print("\nMARKET ENVIRONMENT (macro gate)")
        if m["score"] is None:
            print("Unavailable this run.")
        else:
            parts = ", ".join(f"{k.replace('_', ' ')} {v['score']:.0f}" for k, v in m["components"].items())
            print(f"{m['score']:.0f}/100 · {m['label']} ({parts})"
                  + (f" · missing: {', '.join(m['missing'])}" if m["missing"] else ""))
    if res.get("news"):
        print("\nNEWS (Claude summaries, facts only)")
        cost = 0.0
        for n in res["news"]:
            if n.get("status") != "ok":
                print(f"- {n['ticker']}: {n.get('status')}")
                continue
            cost += n.get("cost_usd") or 0
            tag = " (cached)" if n.get("cached") else ""
            print(f"- {n['ticker']} [{n['sentiment']}]{tag}: {n['summary']}")
            if n.get("drivers"):
                print(f"  Drivers: {'; '.join(n['drivers'])}")
            for f in n.get("position_flags") or []:
                print(f"  Flag for {f.get('position_id')}: {f['flag']}")
        print(f"Claude cost this run: ${cost:.4f}")
    sc = res.get("scan")
    if sc:
        print("\nOPPORTUNITIES (candidates to research, not recommendations)")
        if sc.get("error"):
            print(sc["error"])
        else:
            print(f"Scanned {sc.get('scanned')} of {sc.get('requested')} stocks.")
            for w in sc["watchlist"]:
                price = f"{w['price']:,.2f}" if w["price"] else "-"
                print(f"- Watchlist {w['ticker']} {price}: {w['status']}" + (f" -> YOUR PLAN: {w['action']}" if w["action"] else ""))
            for key, title in scanner.SCREENS.items():
                items = sc["screens"].get(key, [])
                print(f"{title}: " + (", ".join(f"{x['ticker']} ({x['reason']})" for x in items[:5]) or "none today"))
            for n in sc.get("news", []):
                if n.get("status") == "ok":
                    print(f"  {n['ticker']} [{n['sentiment']}]: {n['summary']}")
    if res.get("auto_levels"):
        print("\nAUTO LEVELS (3 x ATR trailing stop, 2:1 target, from the first tracked day)")
        for x in res["auto_levels"]:
            print(f"- {x['ticker']}: stop {x['stop']:,.2f} · target {x['target']:,.2f} · typical daily move {x['atr']:,.2f}")
    rt = res.get("rotation")
    if rt:
        print("\nROTATION (follow the money)")
        for h in rt.get("holdings", []):
            print(f"- #{h.get('queue')} in swap line: {h['ticker']}, rank #{h['rank']} of {rt.get('universe')}, "
                  f"score {h['score']:.0f}" + (f", LOSING {h['pnl_pct']:.1f}%" if h.get("losing") else ""))
        if rt.get("top"):
            print("Strongest stocks you don't own: " + ", ".join(f"{x['ticker']} ({x['score']:.0f})" for x in rt["top"][:5]))
        for s in rt.get("suggestions") or []:
            print(f"SWAP IDEA{' (open since ' + s['suggested_on'] + ')' if s.get('pending') else ''}: "
                  f"sell {s['sell']} -> buy {s['buy']}. {s['reason']}")
        print(f"Status: {rt.get('status')}")
    if res.get("performance"):
        print(performance.text(res["performance"]))
    if "alerts" in res:
        print(f"\nALERTS ({len(res['alerts'])})")
        for a in res["alerts"]:
            print(f"- [{a['severity']}]{' NEW' if a['is_new'] else ''} {a['message']}"
                  + (f" -> YOUR PLAN: {a['action']}" if a.get("action") else ""))
        print(f"Notifier: {res.get('notifier')}")
    for t_, errs in res["data_errors"].items():
        print(f"Data problems for {t_}: {'; '.join(errs[:3])}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pull data and value the options + shares book.")
    ap.add_argument("--asof", help="run date stamp YYYY-MM-DD (default: today)")
    ap.add_argument("--positions", help="path to positions.json")
    ap.add_argument("--rate", type=float, default=config.RISK_FREE_RATE, help="annual risk-free rate")
    ap.add_argument("--json", action="store_true", help="print the full result as JSON")
    a = ap.parse_args(argv)
    try:
        res = run(a.asof, a.positions, a.rate)
    except (positions.PositionError, ValueError) as e:
        sys.exit(f"Error: {e}")
    print(json.dumps(res, indent=1) if a.json else "", end="")
    if not a.json:
        print_report(res)


if __name__ == "__main__":
    main()
