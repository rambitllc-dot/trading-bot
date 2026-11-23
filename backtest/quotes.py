"""Latest prices for a list of tickers -> backtest/results/quotes.md"""
import os
import sys

import yfinance as yf

T = ["SPYM", "SMH", "CIBR", "AIQ", "PAVE", "PPA", "XLV", "NLR", "SGOV", "SPY"]
px = yf.download(T, period="1y", auto_adjust=False, progress=False)["Close"]
lines = [f"# Prices, close of {px.index[-1].date()}", "", "| Ticker | Price | 200-day average | Gap |", "|---|---|---|---|"]
for t in T:
    c = px[t].dropna()
    ma = c.rolling(200).mean().iloc[-1]
    lines.append(f"| {t} | ${c.iloc[-1]:,.2f} | ${ma:,.2f} | {(c.iloc[-1] / ma - 1) * 100:+.1f}% |")
os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)
open(os.path.join(os.path.dirname(__file__), "results", "quotes.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
