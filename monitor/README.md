# Portfolio monitor

A monitor for your options and shares. It reads market data and your own positions, values them,
and (in later layers) alerts you. **It never buys or sells anything.**

## "Your plan says" labels

Every position and alert gets a simple label: **SELL** (price reached your stop, or your target = take profit),
**BUY MORE** (price at or below your optional `add_below` level), **REVIEW** (an option has under 21 days left,
no price, or a news/volatility alert needs a look) or **HOLD** (between your stop and target). They only apply the
levels you write in `positions.json`; they are not predictions or advice, and nothing is ever traded.

## Automatic stop and target

For shares without your own `stop_price` / `target_price`, `levels.py` sets them the way many traders do:
a **trailing "Chandelier" stop** 3 x ATR (the stock's typical daily move over ~22 days) below its highest close
since the monitor started tracking it, which only ever moves up; and a **2-to-1 target** (twice the starting
distance to the stop, above the starting price). Levels start from the first tracked day, not your purchase
price. Write your own numbers in `positions.json` to override them.

## Rotation: follow the money

`rotation.py` scores every S&P 500 stock plus major ETFs (and whatever you hold) on the same 0-100 scale:
momentum 40% (12-month return, skipping the latest month), steadiness 30% (that return vs how much the price
swings), trend 20% (above the 50- and 200-day averages) and news 10% (Claude's sentiment, where available).
Your holdings are ranked against the whole market. Starting with the weakest, each holding is paired with the
strongest stock you don't own (a different one for each swap), and a **SWAP** is suggested when the candidate
scores 80+ and leads by 25+ points. **Each stock can be swapped at most once a week** (a stock bought through a
swap is also free again after a week), and something swapped out isn't bought back within 30 days.
All of these are in `config.py`.
It is a fixed rule, not a prediction, and nothing is traded automatically.

## Opportunities: watchlist and market scan

Looks beyond what you own, every run:
- **Watchlist** (`watchlist.json`): stocks you'd like to own, each with an optional `buy_below` price you choose.
  When a stock reaches it, you get **BUY** (alert `watch_buy`); within 5% above it, **REVIEW** (`watch_near`);
  otherwise **WAIT**. The three entries in it now are examples.
- **S&P 500 scan** of every company (list in `sp500.csv`): momentum leaders (best 12-month return, skipping the
  latest month), pullbacks inside uptrends (above the 200-day average with RSI-2 under 10), new 52-week highs,
  and unusual volume (3x normal with a 3%+ move). Top 10 per screen.
- The top 5 candidates and your watchlist names get a short Claude news summary (cached per day).
Scan results are **candidates to research, not recommendations**. Only a buy level you set produces a BUY.

## Layer 1: data and valuation (built)

- `positions.json`: your book. Two kinds of rows, `"option"` and `"shares"` (the three rows in it now are
  **examples** to replace). For options, `entry_price`, `target_price` and `stop_price` are **per share**;
  one contract = 100 shares. `id` is optional (made from ticker + strike + expiry).
- `data.py`: pulls spot prices and, for anything you hold options on, the full option chain across every
  expiry from Yahoo Finance (bid, ask, last, IV, volume, open interest). Mark = middle of bid/ask, or last.
- `greeks.py`: Black-Scholes delta, gamma, theta (per day) and vega (per IV point), computed locally.
  Risk-free rate is in `config.py` (default 4.5%).
- `storage.py`: saves every pulled chain to `snapshots/TICKER_YYYY-MM-DD.json` and to one SQLite database
  (`monitor.db`), so later layers can spot new strikes/expiries and track IV over time.
- `valuation.py`: per position: mark, value, P&L ($ and %), days to expiry, progress to target and stop.
- `run.py`: runs it all. `python -m monitor.run` (or `--asof YYYY-MM-DD` to stamp a date; prices still come
  from the current feed). Output also goes to `output/valuation_latest.json` for later layers.

## Layer 2: portfolio analytics (built)

`analytics.py`, run automatically after Layer 1. Facts only, never advice.
- **Allocation** by ticker and by sector (sector from `SECTORS` in `config.py`, else looked up on Yahoo and
  remembered). Flags any ticker over 40% or sector over 60% of the book.
- **Aggregate Greeks**: net delta in share terms, daily theta in dollars (what the book loses per day if
  nothing moves), net vega in dollars per 1 IV point.
- **IV environment** per option: current IV, IV rank and IV percentile versus that contract's own stored
  daily IV (up to 252 days). Shows "building history" until 20 days exist; flags **rich** (rank > 70) or
  **cheap** (rank < 30).
- **Expiry watch**: flags options with fewer than 45 days left, so time decay and roll decisions are visible.
- Stored each run in the database (`analytics`, `allocation`, `iv_environment`, `flags` tables).
All thresholds live in `config.py`.

## Layer 3: macro gate and Claude news (built)

**Macro gate** (`macro.py`): a deterministic 0-100 score of the market environment (higher = calmer),
blending, with weights in `config.py` that must add to 1.0:
- VIX level (12 or lower = 100, 40 or higher = 0) and where today's VIX sits in its last year
- VIX term structure (VIX vs VIX3M; short-term fear above long-term = stress)
- Breadth: share of the 11 S&P 500 sector ETFs above their 200-day average (a breadth proxy)
- Credit: the HYG (junk bonds) / TLT (Treasuries) ratio vs its last year
Labels: Calm (65+), Mixed, Stressed (under 40). Same data in, same score out.

**News** (`news.py`): for each ticker you hold, headlines from the last 3 days go to Claude (Haiku 5.5),
which returns a short summary, a sentiment (positive / neutral / negative), the key drivers, and flags
for anything that affects one of your positions in that name. It never says buy or sell.
Each name is analyzed once per day and cached, so re-runs aren't billed. This is the only paid part:
roughly $0.0005 per name per day. It needs an Anthropic API key saved as the GitHub secret
`ANTHROPIC_API_KEY`; without it everything else still runs and news shows as "off".
Both are stored in the database each run (`macro`, `news_analysis` tables).

## Layer 4: alerts, dashboard, notifier, schedule (built)

**Alerts** (`alerts.py`), facts only, never buy/sell:
- **New strikes / expiries**: today's chain vs the prior run. New expiries, and new strikes within +/-30% of
  strikes you hold (fresh LEAPS dates and nearby strikes, without scanning the whole chain).
- `target_hit` (high), e.g. "NOK 100 calls (2027-01-15) hit your target level"; `stop_hit` (high);
  `target_near` (info, 80%+ of the way); `iv_change` (warn, IV moved 20%+ vs prior run);
  `new_strikes` / `new_expiry` (info); plus the Layer 2 flags.
- `news_flag`, `news_negative` and `macro_shift` (warn), with the one-line driver attached. *These fill a gap
  in the original prompt (that part was missing from the source); they match its surviving text and Layer 3.*
- Alerts are marked NEW when they weren't raised at the prior run, and stored in the `alerts` table.

**Dashboard** (`dashboard/app.py`, Streamlit, Bloomberg-terminal style, one page): status strip (NAV, P&L,
positions, alert count, macro score, net delta, daily theta, as-of date), active alerts color-coded by
severity (new strikes/expiries in yellow), dense positions grid with DTE pills and progress bars to target
and stop, theta decay (stacked $ value to the longest expiry + extrinsic value per share, Black-Scholes at
constant spot and IV: illustrative, not predictive), strike ladder (+/-6 strikes, held strike highlighted,
NEW badges), allocation bars with concentration flags, macro panel and news panel (summary, sentiment,
drivers, position flag, clickable headlines). *The macro and news panels also fill the gap in the prompt.*
- Run on a computer: `pip install -r monitor/dashboard/requirements.txt` then `streamlit run monitor/dashboard/app.py`
- Or host it free: share.streamlit.io > sign in with GitHub > New app > repo `rambitllc-dot/trading-bot`,
  branch `main`, main file `monitor/dashboard/app.py` > Deploy. It shows the latest data after each run.

**Notifier** (`notifier.py`), off by default. In `config.py` set `NOTIFY_ENABLED = True` and pick
`NOTIFY_CHANNEL`: `"telegram"` (add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as GitHub secrets),
`"imessage"` (Mac only, via osascript, to `IMESSAGE_RECIPIENT`), or `"github"` (an issue that the GitHub app
pushes to your phone). `NOTIFY_MIN_SEVERITY` limits what gets sent. The runner calls
`notifier.maybe_send(alerts, asof)` at the end; when disabled it does nothing.

**Schedule**: GitHub runs the full pipeline every weekday after the close (21:35 UTC) and saves the log to
`monitor/logs/`. To run it on your own computer instead, this cron line does the same at 1:35 PM Pacific
(market close is 1:00 PM Pacific):

    35 13 * * 1-5 cd /path/to/trading-bot && /usr/bin/env python3 -m monitor.run >> monitor/logs/monitor.log 2>&1

The whole system is a monitor. It reports conditions, tracks your own targets, and Claude summarizes the
news. Nothing recommends trades or routes orders.

Run it from GitHub any time: **Actions > Portfolio monitor > Run workflow**.
Tests: `python -m unittest discover -s monitor/tests -t .`

## Automatic positions from Interactive Brokers (read-only)

Before each evening run, `monitor/ibkr_sync.py` downloads your IB **Flex report**
(open positions + cash) and rewrites `positions.json`. Your own stop/target/add_below
values are kept. It can only *read* your account; it cannot trade.

- Needs GitHub secrets `IBKR_FLEX_TOKEN` and `IBKR_FLEX_QUERY_ID` (without them it does nothing).
- IB builds the report once a day after the close, so it shows the last business day.
- If you edited `positions.json` with trades newer than IB's report, the sync waits until IB catches up.
- If IB is down or the download fails, the old `positions.json` is kept.

## Wins & losses and the swap scorecard

`monitor/performance.py` (dashboard section "Wins & losses · did the swaps work?"):
- **Wins & losses**: every trade from IB (needs the **Trades** section in the Flex Query). Sales carry IB's realized
  profit/loss; open positions add the not-yet-locked-in part. Win rate, average win/loss, fees.
- **Your book vs the S&P 500**: book value each evening against SPY from the first tracked day.
- **Swap line**: holdings losing money since you bought them are flagged LOSING and go first in line for the next
  swap (biggest loss first), then the lowest-scoring. They still need a clearly stronger replacement.
- **Swap scorecard**: for every swap idea, the bought stock's return minus the sold stock's return since the
  idea's close ("edge"). Marked FOLLOWED / PARTLY / SKIPPED / OPEN from your trades, so skipped ideas are judged too.

## Protecting against a top-ranked stock that rolls over

- **6% max loss**: an automatic stop is never more than 6% below what you paid (`MAX_LOSS_PCT`). A position already
  down more than that shows SELL.
- **Breakeven lock**: once a stock has closed 10% above what you paid (`BREAKEVEN_AFTER_PCT`), its stop rises to your
  buy price, so a winner can't become a loser. The trailing stop keeps rising from there; stops never move down.
- **WEAK**: a close below the 50-day average (`WEAK_MA_DAYS`) labels the stock WEAK and puts it first in the swap
  line, even if it still ranks near the top (the ranking looks back 3-12 months, so it reacts slowly).
- **Stopped out = swapped**: a holding that hits its stop (or target) is swapped right away into the strongest stock
  you don't own, whatever its own rank, skipping the weekly, 7-day-hold and 25-point-lead rules. If nothing scores
  80+, the SELL stands and the money waits in cash. Sold stocks can't be bought back for 30 days.

## Autopilot (practice): trades the strategy by itself in a paper account

`monitor/autotrade.py`, with its files in `monitor/autotrade/`. No real money (`AUTO_LIVE = False`).
- **Evening** (inside the monitor run): reads the practice Alpaca account, applies every rule above, and writes
  `plan.json`: what to sell, what to buy, each holding's stop and target, and backup stocks.
- **Market hours** (the always-on bot loop, every 30 minutes): carries out a new plan once (sells, then buys
  at 20% of the account each), and every round sells any holding at its stop or target and replaces it with
  the next backup stock.
- Safety: paper only; buys only stocks from the plan; no buy over 25% of the account; no same-day sale of a
  stock bought that day; doesn't trade on a plan older than 4 days; pause with `"paused": true` in
  `monitor/autotrade/switch.json`. Every trade goes to `log.csv` and Telegram.
- Needs GitHub secrets `ALPACA_AUTO_KEY` / `ALPACA_AUTO_SECRET` from a paper account used only for this
  (not the one the old paper bot trades in).

## IB trader on the Mac

`monitor/ib_trader.py` runs next to IB Gateway on an always-on Mac and carries out `monitor/output/ib_plan.json`
(written each evening, same format and rules as the autopilot) on your IB account: sells, paired buys with the
sale money, and a stop/target watch every 2 minutes during market hours, with Telegram messages for everything.
Paper account by default (port 4002); real money only with `"live": true` in `~/ib-trader/settings.json` and
IB Gateway logged in to the live account (it refuses a mismatch). Pause: `"paused": true` in
`monitor/ib_switch.json` (GitHub) or in the settings file. Setup: `bash ~/trading-bot/mac/setup.sh`.
