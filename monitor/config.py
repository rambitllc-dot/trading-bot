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

# ---- Layer 3: macro gate + Claude news ----
# Macro gate: 0-100, higher = calmer, more supportive market. Weights must add up to 1.0.
MACRO_WEIGHTS = {
    "vix_level": 0.25,        # VIX itself: 12 or lower scores 100, 40 or higher scores 0
    "vix_percentile": 0.15,   # where today's VIX sits vs the last year (low = calm)
    "term_structure": 0.20,   # VIX vs VIX3M: short-term fear below longer-term = calm
    "breadth": 0.20,          # share of the 11 S&P sector ETFs above their 200-day average
    "credit": 0.20,           # HYG (junk bonds) vs TLT (Treasuries) ratio vs the last year
}
BREADTH_ETFS = ["XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
MACRO_CALM = 65             # score at or above = "Calm"
MACRO_STRESSED = 40         # score below = "Stressed"; in between = "Mixed"

# Claude news analysis (the only paid part; needs the ANTHROPIC_API_KEY secret)
NEWS_WINDOW_DAYS = 3
NEWS_MAX_HEADLINES = 15
CLAUDE_MODEL = "claude-haiku-5-5"
CLAUDE_PRICE_IN = 0.10      # $ per million input tokens (Haiku 5.5, prompts under 100k tokens)
CLAUDE_PRICE_OUT = 0.50     # $ per million output tokens
