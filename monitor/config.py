"""Settings shared by every layer. Change values here, not in the code."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POSITIONS_FILE = os.path.join(BASE_DIR, "positions.json")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
DB_FILE = os.environ.get("MONITOR_DB") or os.path.join(BASE_DIR, "monitor.db")

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

# ---- Layer 4: alerts, dashboard, notifier ----
NEW_STRIKE_BAND_PCT = 30    # report newly listed strikes within +/- this % of a strike you hold
TARGET_NEAR_PCT = 80        # "target_near" once a position is this far from entry to target
IV_CHANGE_PCT = 20          # "iv_change" when a held contract's IV moves this much vs the prior run
MACRO_SHIFT_POINTS = 15     # "macro_shift" when the macro score moves this many points vs the prior run

# Notifier: off by default. channel: "telegram" (needs TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID secrets),
# "imessage" (macOS only, sends to IMESSAGE_RECIPIENT), or "github" (opens an issue, which the GitHub app
# pushes to your phone).
NOTIFY_ENABLED = True
NOTIFY_CHANNEL = "telegram"
IMESSAGE_RECIPIENT = ""
NOTIFY_DIGEST = True        # Telegram: one full "daily decisions" message each evening (includes the high alerts)
NOTIFY_MIN_SEVERITY = "high"   # "high" = swaps, SELL (stop/target) and BUY only; "warn"/"info" send more

# ---- "Your plan says" labels (based only on YOUR target / stop / add_below levels) ----
REVIEW_DTE_DAYS = 21        # options with fewer days left than this get "REVIEW" (decide what to do before expiry)

# ---- Opportunity scanner + watchlist ----
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
SCAN_UNIVERSE_FILE = os.path.join(os.path.dirname(BASE_DIR), "sp500.csv")  # the ~500 S&P 500 companies
SCAN_TOP_N = 10             # candidates shown per screen
SCAN_NEWS_TOP = 5           # how many top candidates get a Claude news summary (about $0.0005 each)
WATCH_NEAR_PCT = 5          # "watch_near" when a watchlist stock is within this % of your buy level

# ---- Rotation: "follow the money" (suggests swapping your weakest holding for a clearly stronger stock) ----
ROTATION_EXTRA = ["SPY", "QQQ", "DIA", "IWM", "RSP", "XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU",
                  "XLB", "XLRE", "XLC", "SMH", "GLD"]   # ETFs scored alongside the S&P 500 stocks
ROTATION_WEIGHTS = {"momentum": 0.40, "steadiness": 0.30, "trend": 0.20, "news": 0.10}  # must add to 1.0
ROTATION_MARGIN = 25        # candidate must score this many points (0-100 scale) above your weakest holding
ROTATION_MIN_SCORE = 80     # ...and score at least this (top fifth of the market)
ROTATION_MIN_HOLD_DAYS = 7  # don't suggest selling something bought less than this many days ago
ROTATION_COOLDOWN_DAYS = 7  # each stock can be swapped at most once per this many days
ROTATION_NO_REBUY_DAYS = 30 # don't suggest buying back something swapped out within this many days

# ---- Automatic stop / target (used when a position has no stop_price / target_price of its own) ----
AUTO_LEVELS = True
ATR_PERIOD = 22             # average true range over about one month of trading days
ATR_STOP_MULT = 3.0         # stop = highest close since tracking began - 3 x ATR ("Chandelier" trailing stop)
MAX_LOSS_PCT = 6.0          # stop never sits more than 6% below what you paid (cut losses early)
BREAKEVEN_AFTER_PCT = 10.0  # once a stock has closed 10% above what you paid, the stop rises to your buy price
WEAK_MA_DAYS = 50           # a close below this moving average flags the stock WEAKENING (front of the swap line)
REWARD_RISK = 2.0           # target = starting price + 2 x the starting distance to the stop

# ---------- Autopilot (practice): trades the strategy by itself in a separate Alpaca PAPER account ----------
# Needs GitHub secrets ALPACA_AUTO_KEY / ALPACA_AUTO_SECRET (keys of a paper account used only for this).
# Pause any time: set "paused": true in monitor/autotrade/switch.json (editable from the GitHub app).
AUTO_DIR = os.path.join(BASE_DIR, "autotrade")
AUTO_DB = os.path.join(AUTO_DIR, "auto.db")
AUTO_HOLDINGS = 5           # equal weight: each stock gets 1/5 (20%) of the account
AUTO_MAX_ORDER_PCT = 25     # safety: no single buy larger than 25% of the account
AUTO_LIVE = False           # practice only; real money needs a deliberate switch later
