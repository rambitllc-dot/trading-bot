# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 16:31 UTC · Bitcoin $77,461.60 · US stock market open

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Nvidia buy & hold | Hold | Stock | $101.06 | +$1.06 (+1.1%) | 1 |
| 2 | Nvidia trend (200 day) | Static rule | Stock | $100.30 | +$0.30 (+0.3%) | 2 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Amazon trend (200 day) | Static rule | Stock | $99.72 | -$0.28 (-0.3%) | 1 |
| 5 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.71 | -$0.29 (-0.3%) | 3 |
| 6 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.66 | -$0.34 (-0.3%) | 1 |
| 7 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.65 | -$0.35 (-0.3%) | 1 |
| 8 | S&P 500 buy & hold | Hold | ETF | $99.65 | -$0.35 (-0.4%) | 1 |
| 9 | S&P 500 trend (200 day) | Static rule | ETF | $99.65 | -$0.35 (-0.4%) | 1 |
| 10 | Microsoft buy & hold | Hold | Stock | $99.42 | -$0.58 (-0.6%) | 1 |
| 11 | Microsoft trend (200 day) | Static rule | Stock | $99.42 | -$0.58 (-0.6%) | 1 |
| 12 | Amazon buy & hold | Hold | Stock | $99.34 | -$0.66 (-0.7%) | 1 |
| 13 | Wide momentum (10 ETFs) | Monthly pick | ETF | $98.79 | -$1.21 (-1.2%) | 1 |
| 14 | Bitcoin buy & hold | Hold | Bitcoin | $98.59 | -$1.41 (-1.4%) | 1 |
| 15 | Apple buy & hold | Hold | Stock | $98.37 | -$1.63 (-1.6%) | 1 |
| 16 | Apple trend (200 day) | Static rule | Stock | $98.37 | -$1.63 (-1.6%) | 1 |
| 17 | Tesla buy & hold | Hold | Stock | $97.99 | -$2.01 (-2.0%) | 1 |
| 18 | Tesla trend (200 day) | Static rule | Stock | $97.99 | -$2.01 (-2.0%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.59 | $100.00 | trading |
| S&P 500 | $99.65 | $99.65 | about even |
| Apple | $98.37 | $98.37 | about even |
| Microsoft | $99.42 | $99.42 | about even |
| Nvidia | $101.06 | $100.30 | holding |
| Amazon | $99.34 | $99.72 | about even |
| Tesla | $97.99 | $97.99 | about even |

**All together:** $1,787.67 from $1,800 (-12.33)

## What each one is doing

- **Nvidia buy & hold:** NVDA $100.55, cash $0.51. Holding.
- **Nvidia trend (200 day):** cash $100.30. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Amazon trend (200 day):** AMZN $99.21, cash $0.51. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.48, GLD $19.76, BTC/USD $9.85, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **RSI dip-buying (S&P 500):** SPY $99.15, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $99.14, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $99.14, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $99.14, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Microsoft buy & hold:** MSFT $98.91, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $98.91, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).
- **Amazon buy & hold:** AMZN $98.83, cash $0.51. Holding.
- **Wide momentum (10 ETFs):** XLE $98.28, cash $0.51. Holding XLE until next month's check.
- **Bitcoin buy & hold:** BTC/USD $96.20, cash $2.39. Holding.
- **Apple buy & hold:** AAPL $97.86, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $97.86, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).
- **Tesla buy & hold:** TSLA $97.48, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $97.48, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 11 | 63.6% | $107.18 | -15% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 69 | 46.4% | $52.58 | -51% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 87 | 48.3% | $51.64 | -57% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 87 | 47.1% | $47.17 | -65% |
| Coin flip (luck benchmark) | Luck benchmark | 87 | 46.0% | $43.09 | -60% |

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
