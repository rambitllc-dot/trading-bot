"""Which popular funds beat the S&P 500 (SPY)? Total returns with dividends over 1/3/5/10 years + worst drop (10y).
Run: python backtest/fund_screen.py -> backtest/results/fund_screen.md"""
import os

import pandas as pd
import yfinance as yf

OUT = os.path.join(os.path.dirname(__file__), "results")
FUNDS = {
    "SPY": "S&P 500 (benchmark)", "VOO": "Vanguard S&P 500", "QQQ": "Nasdaq-100 (tech-heavy)",
    "VGT": "Vanguard Information Technology", "XLK": "Technology Select Sector", "SMH": "Semiconductors",
    "VUG": "Vanguard Growth", "SCHG": "Schwab U.S. Large-Cap Growth", "MGK": "Vanguard Mega Cap Growth",
    "IWF": "Russell 1000 Growth", "SPMO": "S&P 500 Momentum", "MTUM": "MSCI USA Momentum",
    "QUAL": "MSCI USA Quality", "SCHD": "Schwab U.S. Dividend Equity", "VIG": "Vanguard Dividend Appreciation",
    "VTV": "Vanguard Value", "RSP": "S&P 500 Equal Weight", "VTI": "Vanguard Total Stock Market",
    "IWM": "Russell 2000 (small caps)", "VXUS": "International stocks", "XLP": "Consumer Staples",
    "XLV": "Health Care", "XLF": "Financials", "XLI": "Industrials", "XLE": "Energy", "XLU": "Utilities",
    "GLD": "Gold", "BRK-B": "Berkshire Hathaway (Warren Buffett)",
}


def main():
    px = yf.download(list(FUNDS), period="11y", auto_adjust=True, progress=False)["Close"]
    last = px.index[-1]
    yrs = [1, 3, 5, 10]
    spy = px["SPY"].dropna()

    def ret(s, y):
        base = s.loc[:last - pd.DateOffset(years=y)]
        return None if base.empty or base.index[-1] < last - pd.DateOffset(years=y, days=10) else s.iloc[-1] / base.iloc[-1] - 1

    rows = []
    for t, name in FUNDS.items():
        s = px[t].dropna()
        r = {y: ret(s, y) for y in yrs}
        w = s.loc[last - pd.DateOffset(years=10):]
        r["dd"] = (w / w.cummax() - 1).min()
        r["beats"] = sum(1 for y in yrs if r[y] is not None and r[y] > ret(spy, y))
        rows.append((t, name, r))
    rows.sort(key=lambda x: -(x[2][10] if x[2][10] is not None else -9))
    lines = [f"# Popular funds vs the S&P 500, total returns to {last.date()}", "",
             "Per-year (annualized) returns; ✅ = beat SPY over that period. Sorted by 10-year return.", "",
             "| Fund | Name | 1 year | 3 years/yr | 5 years/yr | 10 years/yr | Worst drop (10y) | Beat SPY in |",
             "|---|---|---|---|---|---|---|---|"]
    spy_r = {y: ret(spy, y) for y in yrs}
    for t, name, r in rows:
        cells = []
        for y in yrs:
            if r[y] is None:
                cells.append("n/a")
                continue
            ann = (1 + r[y]) ** (1 / y) - 1
            mark = " ✅" if t != "SPY" and r[y] > spy_r[y] else ""
            cells.append(f"{ann * 100:+.1f}%{mark}")
        lines.append(f"| {t} | {name} | " + " | ".join(cells) + f" | {r['dd'] * 100:.0f}% | "
                     f"{r['beats'] if t != 'SPY' else '-'}/4 |")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "fund_screen.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
