# Portfolio monitor

A monitor for your options and shares. It reads market data and your own positions, values them,
and (in later layers) alerts you. **It never buys or sells anything.**

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

Run it from GitHub: **Actions > Portfolio monitor > Run workflow**.
Tests: `python -m unittest discover -s monitor/tests -t .`
