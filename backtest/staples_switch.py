"""Backtest: your S&P switch, but when it's "out" hold consumer staples (XLP) instead of T-bills.

Variants (all since Dec 1998, dividends included, trades at the next open, 0.05% per trade):
  - hold the S&P; hold XLP
  - S&P + switch, T-bills when out (your current plan)
  - S&P + switch, XLP when out (always)
  - S&P + switch, XLP when out only if XLP is in its own uptrend (same switch rule on XLP), else T-bills
Run: python backtest/staples_switch.py -> backtest/results/staples_switch.md
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import sector_rotation as sr  # noqa: E402

OUT = sr.OUT


def plan_from(daily):
    """{date: weights} only where the wanted holding changes (traded at the next open)."""
    plan, prev = {}, None
    for d, w in daily.items():
        key = tuple(sorted(w.items()))
        if key != prev:
            plan[d], prev = w, key
    return plan


def main():
    close, opn, bill = sr.load()
    spy_in, xlp_in = sr.switch(close["SPY"]), sr.switch(close["XLP"])
    rules = {
        "Just hold the S&P 500": {d: {"SPY": 1.0} for d in close.index},
        "Just hold consumer staples (XLP)": {d: {"XLP": 1.0} for d in close.index},
        "S&P + switch, T-bills when out (YOUR PLAN)": {d: ({"SPY": 1.0} if spy_in[d] else {}) for d in close.index},
        "S&P + switch, staples (XLP) when out": {d: ({"SPY": 1.0} if spy_in[d] else {"XLP": 1.0}) for d in close.index},
        "S&P + switch, staples when out only if staples are in an uptrend, else T-bills":
            {d: ({"SPY": 1.0} if spy_in[d] else ({"XLP": 1.0} if xlp_in[d] else {})) for d in close.index},
    }
    full = {n: sr.simulate(close, opn, bill, plan_from(r)) for n, r in rules.items()}
    periods = [("Since 1999 (27 years)", None, None), ("Last 10 years", "2016-11-01", None),
               ("Last 5 years", "2021-11-01", None), ("Last 2 years", "2024-11-01", None),
               ("2000-2002 dot-com crash", "2000-01-01", "2002-12-31"), ("2008 crash", "2007-10-01", "2009-12-31"),
               ("2020 Covid crash", "2020-01-01", "2020-12-31"), ("2022 bear market", "2022-01-01", "2023-12-31")]
    lines = ["# S&P switch: T-bills vs consumer staples when out", "",
             f"Data: SPY and XLP with dividends, {close.index[0].date()} to {close.index[-1].date()}. "
             "Switch: out after 2 closes at/below the 200-day average, back after 2 closes 2%+ above. "
             "$1,000 at the start of each period.", ""]
    for pname, a, b in periods:
        lines += [f"## {pname}", "", "| Strategy | $1,000 became | Per year | Worst drop |", "|---|---|---|---|"]
        for name, (s, tr) in full.items():
            st = sr.stats(s.loc[a:b], tr)
            lines.append(f"| {name} | ${st['final']:,.0f} | {st['per_year']:+.2f}% | {st['worst']:.1f}% |")
        lines.append("")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "staples_switch.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
