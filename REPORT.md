# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 14:31 UTC · Bitcoin $77,158.71 · US stock market open

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Nvidia trend (200 day) | Static rule | Stock | $100.30 | +$0.30 (+0.3%) | 2 |
| 2 | Nvidia buy & hold | Hold | Stock | $100.29 | +$0.29 (+0.3%) | 1 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Amazon trend (200 day) | Static rule | Stock | $100.00 | -$0.00 (-0.0%) | 1 |
| 5 | Amazon buy & hold | Hold | Stock | $99.62 | -$0.38 (-0.4%) | 1 |
| 6 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.55 | -$0.45 (-0.4%) | 3 |
| 7 | Tesla buy & hold | Hold | Stock | $99.47 | -$0.53 (-0.5%) | 1 |
| 8 | Tesla trend (200 day) | Static rule | Stock | $99.47 | -$0.53 (-0.5%) | 1 |
| 9 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.35 | -$0.65 (-0.7%) | 1 |
| 10 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.34 | -$0.66 (-0.7%) | 1 |
| 11 | S&P 500 buy & hold | Hold | ETF | $99.34 | -$0.66 (-0.7%) | 1 |
| 12 | S&P 500 trend (200 day) | Static rule | ETF | $99.34 | -$0.66 (-0.7%) | 1 |
| 13 | Wide momentum (10 ETFs) | Monthly pick | ETF | $98.75 | -$1.25 (-1.2%) | 1 |
| 14 | Bitcoin buy & hold | Hold | Bitcoin | $98.21 | -$1.79 (-1.8%) | 1 |
| 15 | Microsoft buy & hold | Hold | Stock | $98.21 | -$1.79 (-1.8%) | 1 |
| 16 | Microsoft trend (200 day) | Static rule | Stock | $98.21 | -$1.79 (-1.8%) | 1 |
| 17 | Apple buy & hold | Hold | Stock | $97.98 | -$2.02 (-2.0%) | 1 |
| 18 | Apple trend (200 day) | Static rule | Stock | $97.98 | -$2.02 (-2.0%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.21 | $100.00 | trading |
| S&P 500 | $99.34 | $99.34 | about even |
| Apple | $97.98 | $97.98 | about even |
| Microsoft | $98.21 | $98.21 | about even |
| Nvidia | $100.29 | $100.30 | about even |
| Amazon | $99.62 | $100.00 | about even |
| Tesla | $99.47 | $99.47 | about even |

**All together:** $1,785.41 from $1,800 (-14.59)

## What each one is doing

- **Nvidia trend (200 day):** cash $100.30. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Nvidia buy & hold:** NVDA $99.78, cash $0.51. Holding.
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Amazon trend (200 day):** AMZN $99.49, cash $0.51. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Amazon buy & hold:** AMZN $99.11, cash $0.51. Holding.
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.30, GLD $19.82, BTC/USD $9.81, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **Tesla buy & hold:** TSLA $98.96, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $98.96, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).
- **RSI dip-buying (S&P 500):** SPY $98.84, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $98.83, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $98.83, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $98.83, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Wide momentum (10 ETFs):** XLE $98.24, cash $0.51. Holding XLE until next month's check.
- **Bitcoin buy & hold:** BTC/USD $95.82, cash $2.39. Holding.
- **Microsoft buy & hold:** MSFT $97.70, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $97.70, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).
- **Apple buy & hold:** AAPL $97.47, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $97.47, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 9 | 77.8% | $118.76 | -6% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 79 | 49.4% | $59.33 | -52% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 62 | 46.8% | $57.39 | -51% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 79 | 46.8% | $49.50 | -65% |
| Coin flip (luck benchmark) | Luck benchmark | 79 | 46.8% | $49.50 | -55% |

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
