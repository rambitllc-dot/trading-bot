"""Total returns (dividends included) of a list of ETFs over standard periods, vs SPY.
Run: python backtest/etf_returns.py -> backtest/results/etf_returns.md"""
import os

import pandas as pd
import yfinance as yf

OUT = os.path.join(os.path.dirname(__file__), "results")
FUNDS = {"XLP": "Consumer Staples Select Sector SPDR", "VDC": "Vanguard Consumer Staples",
         "FSTA": "Fidelity MSCI Consumer Staples", "IYK": "iShares U.S. Consumer Staples",
         "KXI": "iShares Global Consumer Staples", "RSPS": "Invesco S&P 500 Equal Weight Consumer Staples",
         "FXG": "First Trust Consumer Staples AlphaDEX", "SPY": "S&P 500 (for comparison)"}


def main():
    px = yf.download(list(FUNDS), period="6y", auto_adjust=True, progress=False)["Close"]
    last = px.index[-1]
    periods = {"1 month": pd.DateOffset(months=1), "3 months": pd.DateOffset(months=3),
               "Year to date": None, "1 year": pd.DateOffset(years=1), "3 years": pd.DateOffset(years=3),
               "5 years": pd.DateOffset(years=5)}
    lines = [f"# ETF total returns (dividends included), to {last.date()}", "",
             "| ETF | Name | " + " | ".join(periods) + " | Worst drop (1y) |",
             "|---|---|" + "---|" * (len(periods) + 1)]
    for t, name in FUNDS.items():
        s = px[t].dropna()
        cells = []
        for p, off in periods.items():
            start = pd.Timestamp(last.year, 1, 1) if off is None else last - off
            base = s.loc[:start]
            if base.empty:
                cells.append("n/a")
                continue
            cells.append(f"{(s.iloc[-1] / base.iloc[-1] - 1) * 100:+.1f}%")
        y = s.loc[last - pd.DateOffset(years=1):]
        dd = (y / y.cummax() - 1).min() * 100
        lines.append(f"| {t} | {name} | " + " | ".join(cells) + f" | {dd:.1f}% |")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "etf_returns.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
