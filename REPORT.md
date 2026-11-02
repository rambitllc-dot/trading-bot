# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 02, 2026 19:31 UTC · Bitcoin $76,858.79 · US stock market open

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Apple buy & hold | Hold | Stock | $100.08 | +$0.08 (+0.1%) | 1 |
| 2 | Apple trend (200 day) | Static rule | Stock | $100.07 | +$0.07 (+0.1%) | 1 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Amazon trend (200 day) | Static rule | Stock | $100.00 | +$0.00 (+0.0%) | 0 |
| 5 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.69 | -$0.31 (-0.3%) | 3 |
| 6 | Wide momentum (10 ETFs) | Monthly pick | ETF | $99.68 | -$0.32 (-0.3%) | 1 |
| 7 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.61 | -$0.39 (-0.4%) | 1 |
| 8 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.61 | -$0.39 (-0.4%) | 1 |
| 9 | S&P 500 buy & hold | Hold | ETF | $99.60 | -$0.40 (-0.4%) | 1 |
| 10 | S&P 500 trend (200 day) | Static rule | ETF | $99.60 | -$0.40 (-0.4%) | 1 |
| 11 | Amazon buy & hold | Hold | Stock | $99.54 | -$0.46 (-0.5%) | 1 |
| 12 | Microsoft buy & hold | Hold | Stock | $99.49 | -$0.51 (-0.5%) | 1 |
| 13 | Microsoft trend (200 day) | Static rule | Stock | $99.49 | -$0.51 (-0.5%) | 1 |
| 14 | Tesla buy & hold | Hold | Stock | $99.34 | -$0.66 (-0.7%) | 1 |
| 15 | Tesla trend (200 day) | Static rule | Stock | $99.34 | -$0.66 (-0.7%) | 1 |
| 16 | Nvidia buy & hold | Hold | Stock | $99.08 | -$0.92 (-0.9%) | 1 |
| 17 | Nvidia trend (200 day) | Static rule | Stock | $99.08 | -$0.92 (-0.9%) | 1 |
| 18 | Bitcoin buy & hold | Hold | Bitcoin | $97.84 | -$2.16 (-2.2%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $97.84 | $100.00 | trading |
| S&P 500 | $99.60 | $99.60 | about even |
| Apple | $100.08 | $100.07 | about even |
| Microsoft | $99.49 | $99.49 | about even |
| Nvidia | $99.08 | $99.08 | about even |
| Amazon | $99.54 | $100.00 | about even |
| Tesla | $99.34 | $99.34 | about even |

**All together:** $1,791.15 from $1,800 (-8.85)

## What each one is doing

- **Apple buy & hold:** AAPL $99.57, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $99.56, cash $0.51. Signal: in the market (price $344.77 vs 200d avg $296.25).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $78,385.69 vs 20d avg $80,823.58).
- **Amazon trend (200 day):** cash $100.00. Signal: in cash (price $240.34 vs 200d avg $243.39).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.45, GLD $19.85, BTC/USD $9.77, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **Wide momentum (10 ETFs):** XLE $99.17, cash $0.51. Holding XLE until next month's check.
- **RSI dip-buying (S&P 500):** SPY $99.10, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 9, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $99.10, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $99.09, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $99.09, cash $0.51. Signal: in the market (price $755.72 vs 200d avg $725.95).
- **Amazon buy & hold:** AMZN $99.03, cash $0.51. Holding.
- **Microsoft buy & hold:** MSFT $98.98, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $98.98, cash $0.51. Signal: in the market (price $521.97 vs 200d avg $436.84).
- **Tesla buy & hold:** TSLA $98.83, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $98.83, cash $0.51. Signal: in the market (price $399.80 vs 200d avg $385.27).
- **Nvidia buy & hold:** NVDA $98.57, cash $0.51. Holding.
- **Nvidia trend (200 day):** NVDA $98.57, cash $0.51. Signal: in the market (price $204.76 vs 200d avg $204.09).
- **Bitcoin buy & hold:** BTC/USD $95.45, cash $2.39. Holding.

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Coin flip (luck benchmark) | Luck benchmark | 3 | 66.7% | $102.75 | -5% |
| Reversal: bet against unusually big moves | Static (one fixed method) | 0 | - | $100.00 | 0% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 1 | 0.0% | $95.00 | -5% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 3 | 33.3% | $93.86 | -6% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 3 | 0.0% | $85.74 | -14% |

### Backtest: the 30 days before that

| Method | Type | Bets | Win rate | $100 became | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 389 | 47.8% | $4.43 | -96% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 581 | 48.0% | $1.06 | -99% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 540 | 47.2% | $0.99 (ran out) | -99% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 662 | 48.9% | $0.98 (ran out) | -99% |
| Coin flip (luck benchmark) | Luck benchmark | 842 | 50.6% | $0.98 (ran out) | -99% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 814 | 50.4% | $0.96 (ran out) | -99% |

If a method can't beat the coin flip by a clear margin over hundreds of bets, it has no real edge.

Paper money only. Past or paper results do not predict real results.
