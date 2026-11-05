"""Settings shared by every layer. Change values here, not in the code."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POSITIONS_FILE = os.path.join(BASE_DIR, "positions.json")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
DB_FILE = os.path.join(BASE_DIR, "monitor.db")

RISK_FREE_RATE = 0.045      # annual, used for Black-Scholes Greeks
CONTRACT_MULTIPLIER = 100   # one option contract = 100 shares

# ---- Layer 2: portfolio analytics ----
TICKER_CAP_PCT = 40         # flag any single ticker above this share of total value
SECTOR_CAP_PCT = 60         # flag any sector above this share of total value
IV_LOOKBACK_DAYS = 252      # daily snapshots used for IV rank / percentile (about one trading year)
IV_MIN_HISTORY_DAYS = 20    # below this, IV rank shows "building history"
IV_RICH = 70                # IV rank above this = options are expensive vs their own history
IV_CHEAP = 30               # IV rank below this = options are cheap vs their own history
DTE_WATCH_DAYS = 45         # flag options with fewer days than this left to expiry

# Ticker -> sector. Anything missing is looked up from Yahoo Finance and remembered.
SECTORS = {
    "SPY": "Broad market (ETF)", "RSP": "Broad market (ETF)", "QQQ": "Technology (ETF)",
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology",
    "AMZN": "Consumer Cyclical", "TSLA": "Consumer Cyclical",
    "SPCX": "Aerospace & Space", "ANT": "Technology", "NOK": "Technology",
    "GLD": "Gold (ETF)", "BND": "Bonds (ETF)",
}
