"""Backtest: sector rotation vs the S&P 500.

Each month (last trading day's close) rank the 9 original sector funds (SPDR, since Dec 1998) by their gain over the
last N months; hold the top K, equal weight, bought at the next day's open. Optional protection: when SPY is "out"
by the 200-day switch (out at/below the average for 2 closes, back after 2 closes 2%+ above), hold T-bills instead.
0.05% cost on everything traded. All prices include dividends.

Run: python backtest/sector_rotation.py -> backtest/results/sector_rotation.md
"""
import os

import pandas as pd
import yfinance as yf

OUT = os.path.join(os.path.dirname(__file__), "results")
SECTORS = {"XLK": "Technology", "XLF": "Financials", "XLV": "Health Care", "XLE": "Energy", "XLI": "Industrials",
           "XLY": "Consumer Discretionary", "XLP": "Consumer Staples", "XLU": "Utilities", "XLB": "Materials"}
COST = 0.0005


def load():
    t = list(SECTORS) + ["SPY"]
    px = yf.download(t, start="1998-12-22", auto_adjust=True, progress=False)
    close, opn = px["Close"][t].dropna(), px["Open"][t].dropna()
    idx = close.index.intersection(opn.index)
    irx = yf.download("^IRX", start="1998-12-01", progress=False)["Close"]
    if isinstance(irx, pd.DataFrame):
        irx = irx.iloc[:, 0]
    bill = irx.reindex(idx).ffill().bfill() / 100 / 252
    return close.loc[idx], opn.loc[idx], bill


def switch(spy, in_pct=2.0, days=2):
    ma = spy.rolling(200).mean()
    out, inn, lo, hi = [], 1, 0, 0
    for x, a in zip(spy.values, ma.values):
        if a == a:
            lo = lo + 1 if x <= a else 0
            hi = hi + 1 if x >= a * (1 + in_pct / 100) else 0
            if inn and lo >= days:
                inn = 0
            elif not inn and hi >= days:
                inn = 1
        out.append(inn)
    return pd.Series(out, index=spy.index)


def targets(close, months, top, sw=None, rebalance="M"):
    """{date: {ticker: weight}} decided at each month-end (and on switch changes when sw is given)."""
    ends = close.groupby(close.index.to_period(rebalance)).tail(1).index
    look = months * 21
    plan, prev_in = {}, None
    for d in close.index:
        i = close.index.get_loc(d)
        is_in = int(sw.loc[d]) if sw is not None else 1
        changed = sw is not None and prev_in is not None and is_in != prev_in
        prev_in = is_in
        if d not in ends and not changed:
            continue
        if not is_in:
            plan[d] = {}
            continue
        if i < look:
            continue
        ret = close.iloc[i][list(SECTORS)] / close.iloc[i - look][list(SECTORS)] - 1
        best = ret.sort_values(ascending=False).index[:top]
        plan[d] = {t: 1 / top for t in best}
    return plan


def simulate(close, opn, bill, plan, fixed=None):
    """Daily value of $1,000; a plan made at a close is traded at the next day's open."""
    v, hold, cash, vals, trades = 1000.0, {}, 1000.0, [], 0
    if fixed:
        hold, cash = {t: 1000.0 * w for t, w in fixed.items()}, 0.0
    pending = None
    dates = close.index
    for k, d in enumerate(dates):
        if k:
            p = dates[k - 1]
            if pending is not None:
                # move holdings from yesterday's close to today's open, rebalance at the open, then open -> close
                hold = {t: x * opn.loc[d, t] / close.loc[p, t] for t, x in hold.items()}
                tot = sum(hold.values()) + cash * (1 + bill.loc[d])
                new = {t: tot * w for t, w in pending.items()}
                turnover = sum(abs(new.get(t, 0) - hold.get(t, 0)) for t in set(new) | set(hold))
                if turnover > 1e-6:
                    trades += 1
                tot -= turnover * COST
                hold = {t: tot * w for t, w in pending.items()}
                cash = tot - sum(hold.values())
                hold = {t: x * close.loc[d, t] / opn.loc[d, t] for t, x in hold.items()}
                pending = None
            else:
                hold = {t: x * close.loc[d, t] / close.loc[p, t] for t, x in hold.items()}
                cash *= 1 + bill.loc[d]
        elif not fixed:
            cash = 1000.0
        if d in plan:
            pending = plan[d]
        vals.append(sum(hold.values()) + cash)
    return pd.Series(vals, index=dates), trades


def stats(s, trades):
    years = (s.index[-1] - s.index[0]).days / 365.25
    return {"final": float(s.iloc[-1] / s.iloc[0] * 1000), "per_year": float((s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1) * 100,
            "worst": float((s / s.cummax() - 1).min()) * 100, "trades": trades}


def main():
    close, opn, bill = load()
    sw = switch(close["SPY"])
    rules = {
        "Just hold the S&P 500 (SPY)": (None, {"SPY": 1.0}),
        "S&P 500 + your switch": ({d: ({"SPY": 1.0} if int(sw.loc[d]) else {}) for d in sw.index
                                   if d == sw.index[0] or sw.loc[d] != sw.shift(1).loc[d]}, None),
        "All 9 sectors equally, held": (None, {t: 1 / 9 for t in SECTORS}),
    }
    for m in (3, 6, 12):
        for top in (1, 2, 3):
            rules[f"Top {top} sector(s) by {m}-month gain, monthly"] = (targets(close, m, top), None)
            rules[f"Top {top} sector(s) by {m}-month gain, monthly + your switch"] = (targets(close, m, top, sw), None)
    periods = [("Since 1999 (27 years)", None, None), ("Last 10 years", "2016-11-01", None),
               ("Last 5 years", "2021-11-01", None), ("Last 2 years", "2024-11-01", None),
               ("2000-2002 dot-com crash", "2000-01-01", "2002-12-31"), ("2008 crash", "2007-10-01", "2009-12-31"),
               ("2022 bear market", "2022-01-01", "2023-12-31")]
    full = {}
    for name, (plan, fixed) in rules.items():
        full[name] = simulate(close, opn, bill, plan or {}, fixed)
    lines = ["# Sector rotation vs the S&P 500", "",
             f"Data: 9 SPDR sector funds + SPY with dividends, {close.index[0].date()} to {close.index[-1].date()}. "
             "Monthly ranking at the close, trades at the next open, 0.05% per trade. $1,000 at the start of each period.", ""]
    for pname, a, b in periods:
        lines += [f"## {pname}", "", "| Strategy | $1,000 became | Per year | Worst drop | Rebalances |", "|---|---|---|---|---|"]
        for name, (s, tr) in full.items():
            seg = s.loc[a:b]
            st = stats(seg, tr if a is None else 0)
            lines.append(f"| {name} | ${st['final']:,.0f} | {st['per_year']:+.2f}% | {st['worst']:.1f}% | "
                         f"{st['trades'] if a is None else ''} |")
        lines.append("")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "sector_rotation.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
