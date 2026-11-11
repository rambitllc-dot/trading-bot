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
# momentum = 12-month gain (skipping the last month); recent = last month's gain (catches a sustained rally, not
# a 1-3 day spike); steadiness = gain per unit of ups and downs; trend = above the 50/200-day averages; news = Claude.
ROTATION_WEIGHTS = {"momentum": 0.35, "recent": 0.15, "steadiness": 0.25, "trend": 0.15, "news": 0.10}  # sum 1.0
ROTATION_MARGIN = 10        # candidate must score this many points (0-100 scale) above the holding it replaces
ROTATION_MIN_SCORE = 80     # ...and score at least this (top fifth of the market)
ROTATION_MIN_HOLD_DAYS = 2  # business days: a stock bought Friday can be swapped from Tuesday's evening run
ROTATION_COOLDOWN_DAYS = 2  # business days: each stock can be swapped at most once per this many market days
ROTATION_NO_REBUY_DAYS = 30 # don't suggest buying back something swapped out within this many days

# ---- Automatic stop / target (used when a position has no stop_price / target_price of its own) ----
AUTO_LEVELS = True
ATR_PERIOD = 22             # average true range over about one month of trading days
ATR_STOP_MULT = 3.0         # used for the profit target only: target = 2 x (3 x ATR) above the starting price
TRAIL_PCT = 4.5             # the stop always sits 4.5% below the highest price since you bought (starts 4.5% below
                            # your buy price) and only ever moves up
MAX_LOSS_PCT = TRAIL_PCT    # the most a new position can lose before it's sold
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
AUTO_MIN_BUY_USD = 20.0     # don't place buys smaller than this (avoids dust orders)
AUTO_LIVE = False           # practice only; real money needs a deliberate switch later

# ---------- New money (deposits) ----------
# During market hours, when the account has at least this much cash that no planned trade is using (for example
# your deposit on the 20th), it is invested the same day: the strongest stocks (score 80+) from sectors you don't
# own yet, each about the size of your current holdings (1 to 3 stocks). If nothing scores 80+, it buys SPY so
# the money at least keeps pace with the S&P 500.
DEPOSIT_MIN_USD = 50.0
DEPOSIT_MAX_STOCKS = 3
DEPOSIT_FALLBACK = "SPYM"   # S&P 500 fund at ~1/10 of SPY's share price, so leftovers buy whole shares
PARK_FUND = "SPYM"          # leftover cash after whole-share buys goes here when the S&P 500 is in an uptrend
INDEX_TICKER = "SPY"        # the S&P 500 fund whose trend decides between PARK_FUND and SAFE_FUND
DEPOSIT_MAX_TRIES_PER_DAY = 3

# ---------- Diversification and earnings guard ----------
MAX_PER_SECTOR = 2          # never buy a stock if you'd then hold more than 2 from its sector (swaps, stop-out
                            # replacements, new money). Holdings already over it aren't sold for that reason.
EARNINGS_GUARD = True       # don't buy a stock that reports earnings within the next...
EARNINGS_BLACKOUT_DAYS = 5  # ...business days (an overnight earnings jump can skip right past the 6% stop)
EARNINGS_CHECK_TOP = 60     # how many top-ranked candidates get their earnings date checked each evening

# ---------- Market weather, uptrend check, volatility sizing ----------
WEATHER_SWITCH = True       # S&P 500 (SPY) below its 200-day average 2 days in a row = storm: no new stock buys,
SAFE_FUND = "SGOV"          # ...new money and stop-out money wait in this short-term Treasury fund until SPY closes
                            # above the average 2 days in a row; then it's moved back into the strongest stocks
UPTREND_REQUIRED = True     # only buy stocks above their 50- and 200-day averages, 200-day rising, within 25% of high
UPTREND_MAX_FROM_HIGH = 25  # percent below the 1-year high still counted as "near the high"
VOL_SIZING = True           # steadier stocks get more money, jumpy ones less (0.5x to 1.5x of an equal share)
VOL_SIZE_MIN, VOL_SIZE_MAX = 0.5, 1.5
MAX_POSITION_PCT = 35       # no single buy larger than this share of the account

PARKING = {PARK_FUND, "SGOV"}  # funds that hold idle money: not one of the 5 stock slots, no stop, never ranked
