"""Theme funds: chips, health care, cybersecurity, nuclear, power/grid for data centers, defense, AI.
Total returns (dividends included) over 1/3/5 years, per-year since 2016 where available, worst drop, fee, size,
and where each stands vs its 200-day average. Run: python backtest/theme_screen.py -> results/theme_screen.md"""
import os

import pandas as pd
import yfinance as yf

OUT = os.path.join(os.path.dirname(__file__), "results")
THEMES = {
    "Chips (semiconductors)": {"SMH": "VanEck Semiconductor", "SOXX": "iShares Semiconductor"},
    "Health care": {"XLV": "Health Care Select Sector SPDR", "VHT": "Vanguard Health Care"},
    "Cybersecurity": {"CIBR": "First Trust Nasdaq Cybersecurity", "HACK": "Amplify Cybersecurity",
                      "BUG": "Global X Cybersecurity"},
    "Nuclear / uranium": {"NLR": "VanEck Uranium & Nuclear", "URA": "Global X Uranium", "NUKZ": "Range Nuclear Renaissance"},
    "Power & grid for data centers": {"GRID": "First Trust Clean Edge Smart Grid Infrastructure",
                                      "XLU": "Utilities Select Sector SPDR", "PAVE": "Global X U.S. Infrastructure Development"},
    "Defense / wars": {"ITA": "iShares U.S. Aerospace & Defense", "XAR": "SPDR S&P Aerospace & Defense",
                       "PPA": "Invesco Aerospace & Defense"},
    "AI (broad)": {"AIQ": "Global X Artificial Intelligence & Technology", "BOTZ": "Global X Robotics & AI"},
    "Benchmark": {"SPY": "S&P 500"},
}


def main():
    tickers = [t for g in THEMES.values() for t in g]
    px = yf.download(tickers, start="2015-11-01", auto_adjust=True, progress=False)["Close"]
    raw = yf.download(tickers, period="2y", auto_adjust=False, progress=False)["Close"]
    last = px.index[-1]

    def ret(s, y):
        base = s.loc[:last - pd.DateOffset(years=y)]
        if base.empty or base.index[-1] < last - pd.DateOffset(years=y, days=10):
            return None
        return (s.iloc[-1] / base.iloc[-1]) ** (1 / y) - 1

    spy = px["SPY"].dropna()
    lines = [f"# Theme funds vs the S&P 500, to {last.date()}", "",
             "Per-year returns with dividends; ✅ beat SPY. Fee = yearly expense ratio. Gap = price vs 200-day average.", "",
             "| Theme | Fund | Name | 1 year | 3 years/yr | 5 years/yr | Since 2016/yr | Worst drop | Fee | Size | 200-day gap |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for theme, funds in THEMES.items():
        for t, name in funds.items():
            s = px[t].dropna()
            cells = []
            for y in (1, 3, 5):
                r, b = ret(s, y), ret(spy, y)
                cells.append("n/a" if r is None else f"{r * 100:+.1f}%" + (" ✅" if t != "SPY" and r > b else ""))
            since = s.loc["2016-01-01":]
            yrs = (since.index[-1] - since.index[0]).days / 365.25
            sr = (since.iloc[-1] / since.iloc[0]) ** (1 / yrs) - 1 if len(since) and yrs > 1 else None
            spy_s = spy.loc[since.index[0]:] if len(since) else spy
            spy_r = (spy_s.iloc[-1] / spy_s.iloc[0]) ** (1 / yrs) - 1 if sr is not None else None
            sr_txt = "n/a" if sr is None else (f"{sr * 100:+.1f}%" + (" ✅" if t != "SPY" and sr > spy_r else "")
                                               + ("" if since.index[0] < pd.Timestamp("2016-02-01") else f" (from {since.index[0].year})"))
            dd = (since / since.cummax() - 1).min() * 100 if len(since) else float("nan")
            c = raw[t].dropna()
            gap = (c.iloc[-1] / c.rolling(200).mean().iloc[-1] - 1) * 100
            fee, size = "?", "?"
            try:
                info = yf.Ticker(t).info
                er = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
                fee = f"{er:.2f}%" if er and er > 0.05 else (f"{er * 100:.2f}%" if er else "?")
                aum = info.get("totalAssets")
                size = f"${aum / 1e9:,.1f}B" if aum else "?"
            except Exception:  # noqa: BLE001
                pass
            lines.append(f"| {theme} | {t} | {name} | " + " | ".join(cells) + f" | {sr_txt} | {dd:.0f}% | {fee} | {size} | "
                         f"{gap:+.1f}% |")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "theme_screen.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
