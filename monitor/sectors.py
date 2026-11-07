"""Sector of any stock or ETF the system can trade (from the S&P 500 list in the repo, plus the ETFs)."""
import csv
import functools
import os

from . import config

ETF_SECTORS = {
    "SPY": "Broad market", "RSP": "Broad market", "DIA": "Broad market", "IWM": "Broad market",
    "QQQ": "Broad market", "XLK": "Information Technology", "SMH": "Information Technology",
    "XLF": "Financials", "XLV": "Health Care", "XLE": "Energy", "XLI": "Industrials",
    "XLY": "Consumer Discretionary", "XLP": "Consumer Staples", "XLU": "Utilities", "XLB": "Materials",
    "XLRE": "Real Estate", "XLC": "Communication Services", "GLD": "Gold",
}


@functools.lru_cache(maxsize=1)
def _table():
    out = {}
    path = config.SCAN_UNIVERSE_FILE
    if os.path.exists(path):
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                t = (row.get("Symbol") or "").strip().replace(".", "-")
                if t:
                    out[t] = row.get("GICS Sector") or "Other"
    return out


def sector_of(ticker):
    t = (ticker or "").upper().replace(".", "-")
    return ETF_SECTORS.get(t) or _table().get(t) or "Other"
