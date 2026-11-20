"""Backtest: S&P 500 (SPY, dividends included) with different "get out / get back in" rules vs just holding it.

Out of the market = Treasury bills (interest from the 13-week T-bill rate, like SGOV).
Signals are checked at each day's close; the trade happens at the next day's open (what a bot could really do).
A small cost per switch (0.05%) covers spread and fees.

Run: python backtest/spy_rules.py   -> backtest/results/spy_rules.md and .json
"""
import json
import os

import pandas as pd
import yfinance as yf

OUT = os.path.join(os.path.dirname(__file__), "results")
COST = 0.0005


def load():
    spy = yf.download("SPY", start="1993-01-29", auto_adjust=True, progress=False)
    irx = yf.download("^IRX", start="1993-01-01", auto_adjust=False, progress=False)
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
        irx.columns = irx.columns.get_level_values(0)
    df = pd.DataFrame({"open": spy["Open"], "close": spy["Close"]}).dropna()
    df["bill"] = irx["Close"].reindex(df.index).ffill().bfill() / 100 / 252  # daily T-bill interest
    df["ma200"] = df["close"].rolling(200).mean()
    return df


# --- rules: each returns a list of 1 (in the S&P) / 0 (in T-bills), decided at the close ---------------------
def hold(df):
    return [1] * len(df)


def trailing(df, stop=4.5, back=None, up_days=None):
    """Sell when the S&P falls `stop`% below its highest close since buying. Buy back when it is `back`% above its
    lowest close since selling, or after `up_days` up days in a row."""
    c, out, inn = df["close"].values, [], 1
    peak = low = c[0]
    run = 0
    for i, x in enumerate(c):
        run = run + 1 if i and x > c[i - 1] else 0
        if inn:
            peak = max(peak, x)
            if x <= peak * (1 - stop / 100):
                inn, low = 0, x
        else:
            low = min(low, x)
            if (back is not None and x >= low * (1 + back / 100)) or (up_days and run >= up_days):
                inn, peak = 1, x
        out.append(inn)
    return out


def stop_then_trend(df, stop):
    """Out when the S&P falls `stop`% below its highest close since buying; back in after 2 closes above its
    200-day average (once it has recovered)."""
    c, m, out, inn, peak, above = df["close"].values, df["ma200"].values, [], 1, df["close"].values[0], 0
    for x, a in zip(c, m):
        above = above + 1 if a == a and x > a else 0
        if inn:
            peak = max(peak, x)
            if x <= peak * (1 - stop / 100):
                inn = 0
        elif above >= 2:
            inn, peak = 1, x
        out.append(inn)
    return out


def ma200_buffer(df, below_pct=5.0, out_days=2, in_days=3):
    """Out after `out_days` closes at least `below_pct`% below the 200-day average; back in after `in_days` closes
    above the average."""
    c, m, out, inn, below, above = df["close"].values, df["ma200"].values, [], 1, 0, 0
    for x, a in zip(c, m):
        if a == a:
            below = below + 1 if x <= a * (1 - below_pct / 100) else 0
            above = above + 1 if x > a else 0
            if inn and below >= out_days:
                inn = 0
            elif not inn and above >= in_days:
                inn = 1
        out.append(inn)
    return out


def ma200_band(df, in_pct=5.0, out_pct=0.0, days=2):
    """Out after `days` closes at/below the 200-day average (+out_pct%); back in after `days` closes at least
    in_pct% above it."""
    c, m, out, inn, lo, hi = df["close"].values, df["ma200"].values, [], 1, 0, 0
    for x, a in zip(c, m):
        if a == a:
            lo = lo + 1 if x <= a * (1 + out_pct / 100) else 0
            hi = hi + 1 if x >= a * (1 + in_pct / 100) else 0
            if inn and lo >= days:
                inn = 0
            elif not inn and hi >= days:
                inn = 1
        out.append(inn)
    return out


def three_down(df, total=3.0, up_days=3):
    """Sell after 3 down days in a row totalling `total`% or more; buy back after `up_days` up days in a row."""
    c, out, inn, down, up = df["close"].values, [], 1, 0, 0
    for i, x in enumerate(c):
        if i:
            down = down + 1 if x < c[i - 1] else 0
            up = up + 1 if x > c[i - 1] else 0
        if inn and down >= 3 and x <= c[i - 3] * (1 - total / 100):
            inn = 0
        elif not inn and up >= up_days:
            inn = 1
        out.append(inn)
    return out


def ma200(df, days=2):
    """Out after `days` closes below the 200-day average; back in after `days` closes above (the bot's switch)."""
    c, m, out, inn, below, above = df["close"].values, df["ma200"].values, [], 1, 0, 0
    for x, a in zip(c, m):
        if a == a:
            below = below + 1 if x < a else 0
            above = above + 1 if x > a else 0
            if inn and below >= days:
                inn = 0
            elif not inn and above >= days:
                inn = 1
        out.append(inn)
    return out


def simulate(df, sig):
    """Daily value of $1,000. Position changes at the next day's open."""
    o, c, b = df["open"].values, df["close"].values, df["bill"].values
    v, vals, pos, switches, days_in = 1000.0, [], sig[0], 0, 0
    for i in range(len(df)):
        if i:
            want = sig[i - 1]
            if want != pos:  # switch at today's open
                if pos:  # was in: yesterday close -> today open in the S&P, then bills
                    v *= o[i] / c[i - 1] * (1 - COST)
                    v *= 1 + b[i]  # the rest of the day in bills
                else:  # was out: bills until the open, then the S&P open -> close
                    v *= (1 + b[i]) * (1 - COST) * c[i] / o[i]
                pos, switches = want, switches + 1
            else:
                v *= c[i] / c[i - 1] if pos else 1 + b[i]
        days_in += pos
        vals.append(v)
    return pd.Series(vals, index=df.index), switches, days_in / len(df)


def stats(s, switches, in_pct):
    years = (s.index[-1] - s.index[0]).days / 365.25
    dd = (s / s.cummax() - 1).min()
    return {"final": round(float(s.iloc[-1] / s.iloc[0] * 1000), 0), "per_year": round(float(
        (s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1) * 100, 2), "worst_drop": round(float(dd) * 100, 1),
        "switches": switches, "time_in_sp": round(in_pct * 100, 0)}


RULES = {
    "Just hold the S&P 500": hold,
    "Your idea: out at -4.5% from the high, back in at +4.5% from the low": lambda d: trailing(d, 4.5, back=4.5),
    "Out at -4.5% from the high, back in at +3% from the low": lambda d: trailing(d, 4.5, back=3.0),
    "Out at -4.5% from the high, back in after 3 up days in a row": lambda d: trailing(d, 4.5, up_days=3),
    "Out after 3 down days totalling -3%, back after 3 up days": three_down,
    "Bot's storm switch: 2 closes below / above the 200-day average": ma200,
    "Your new idea: out after 2 closes 5% below the 200-day, back after 3 closes above it":
        lambda d: ma200_buffer(d, 5, 2, 3),
    "Out after 2 closes 3% below the 200-day, back after 3 closes above it": lambda d: ma200_buffer(d, 3, 2, 3),
    "Out after 2 closes 2% below the 200-day, back after 3 closes above it": lambda d: ma200_buffer(d, 2, 2, 3),
    "Out after 2 closes below the 200-day, back after 3 closes above it": lambda d: ma200_buffer(d, 0.0001, 2, 3),
    "YOUR RULE: out after 2 closes at/below the 200-day, back in after 2 closes 5%+ above it":
        lambda d: ma200_band(d, 5.0, 0.0, 2),
    "Out after 2 closes at/below the 200-day, back in after 2 closes 2%+ above it": lambda d: ma200_band(d, 2.0, 0.0, 2),
    "Out at -10% from the high, back in at +10% from the low": lambda d: trailing(d, 10, back=10),
    "Out at -15% from the high, back in at +15% from the low": lambda d: trailing(d, 15, back=15),
    "Out at -20% from the high, back in at +20% from the low": lambda d: trailing(d, 20, back=20),
    "Out at -10% from the high, back in above the 200-day average": lambda d: stop_then_trend(d, 10),
    "Out at -15% from the high, back in above the 200-day average": lambda d: stop_then_trend(d, 15),
    "Out at -20% from the high, back in above the 200-day average": lambda d: stop_then_trend(d, 20),
}
PERIODS = [("Since 1993 (33 years)", "1993-01-01", None), ("Last 10 years", "2016-11-01", None),
           ("Last 5 years", "2021-11-01", None), ("Last 2 years", "2024-11-01", None),
           ("2008 crash (Oct 2007 - Mar 2013)", "2007-10-01", "2013-03-31"),
           ("2020 Covid crash (2020)", "2020-01-01", "2020-12-31"), ("2022 bear market (2022-2023)", "2022-01-01",
                                                                   "2023-12-31")]


def main():
    full = load()
    sigs = {name: f(full) for name, f in RULES.items()}  # decided on the full history (200-day needs warm-up)
    res, lines = {}, ["# S&P 500: hold vs get-out rules", "",
                      f"Data: SPY with dividends, {full.index[0].date()} to {full.index[-1].date()}. Out = T-bills. "
                      "Trades at the next day's open, 0.05% cost per switch. $1,000 at the start of each period.", ""]
    for pname, a, b in PERIODS:
        df = full.loc[a:b]
        res[pname] = {}
        lines += [f"## {pname}", "", "| Rule | $1,000 became | Per year | Worst drop | Switches | Time in S&P |",
                  "|---|---|---|---|---|---|"]
        for name in RULES:
            sig = pd.Series(sigs[name], index=full.index).loc[a:b].tolist()
            st = stats(*simulate(df, sig))
            res[pname][name] = st
            lines.append(f"| {name} | ${st['final']:,.0f} | {st['per_year']:+.2f}% | {st['worst_drop']}% | "
                         f"{st['switches']} | {st['time_in_sp']:.0f}% |")
        lines.append("")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "spy_rules.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(OUT, "spy_rules.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
