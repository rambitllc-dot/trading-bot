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

from . import config, data, positions, storage, valuation


def run(asof=None, positions_file=None, rate=config.RISK_FREE_RATE, provider=None, db=None, snap_dir=None):
    asof = asof or dt.date.today().isoformat()
    dt.date.fromisoformat(asof)  # validates the format
    book = positions.load(positions_file)
    provider = provider or data.YahooProvider()
    option_tickers = {p["ticker"] for p in book if p["asset_type"] == "option"}
    con = storage.connect(db)
    snaps = {}
    for t in sorted({p["ticker"] for p in book}):
        snap = data.pull(t, t in option_tickers, provider)
        storage.save_snapshot(con, snap, asof, snap_dir)
        snaps[t] = snap
    rows, totals = valuation.value_book(book, snaps, asof, rate)
    storage.save_valuations(con, asof, rows)
    con.close()
    result = {"asof": asof, "totals": totals, "positions": rows,
              "data_errors": {t: s["errors"] for t, s in snaps.items() if s["errors"]}}
    out_dir = os.path.join(config.BASE_DIR, "output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "valuation_latest.json"), "w") as f:
        json.dump(result, f, indent=1)
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
        if r["status"] != "ok":
            line += f" [{r['status']}]"
        print(line)
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
