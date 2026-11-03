# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 15:01 UTC · Bitcoin $77,284.20 · US stock market open

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Nvidia buy & hold | Hold | Stock | $100.69 | +$0.69 (+0.7%) | 1 |
| 2 | Nvidia trend (200 day) | Static rule | Stock | $100.30 | +$0.30 (+0.3%) | 2 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.56 | -$0.44 (-0.4%) | 3 |
| 5 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.37 | -$0.63 (-0.6%) | 1 |
| 6 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.36 | -$0.64 (-0.6%) | 1 |
| 7 | S&P 500 buy & hold | Hold | ETF | $99.36 | -$0.64 (-0.6%) | 1 |
| 8 | S&P 500 trend (200 day) | Static rule | ETF | $99.36 | -$0.64 (-0.6%) | 1 |
| 9 | Amazon trend (200 day) | Static rule | Stock | $99.15 | -$0.85 (-0.9%) | 1 |
| 10 | Amazon buy & hold | Hold | Stock | $98.77 | -$1.23 (-1.2%) | 1 |
| 11 | Wide momentum (10 ETFs) | Monthly pick | ETF | $98.62 | -$1.38 (-1.4%) | 1 |
| 12 | Apple buy & hold | Hold | Stock | $98.60 | -$1.40 (-1.4%) | 1 |
| 13 | Apple trend (200 day) | Static rule | Stock | $98.60 | -$1.40 (-1.4%) | 1 |
| 14 | Tesla buy & hold | Hold | Stock | $98.41 | -$1.59 (-1.6%) | 1 |
| 15 | Tesla trend (200 day) | Static rule | Stock | $98.41 | -$1.59 (-1.6%) | 1 |
| 16 | Bitcoin buy & hold | Hold | Bitcoin | $98.37 | -$1.63 (-1.6%) | 1 |
| 17 | Microsoft buy & hold | Hold | Stock | $98.36 | -$1.64 (-1.6%) | 1 |
| 18 | Microsoft trend (200 day) | Static rule | Stock | $98.36 | -$1.64 (-1.6%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.37 | $100.00 | trading |
| S&P 500 | $99.36 | $99.36 | about even |
| Apple | $98.60 | $98.60 | about even |
| Microsoft | $98.36 | $98.36 | about even |
| Nvidia | $100.69 | $100.30 | about even |
| Amazon | $98.77 | $99.15 | about even |
| Tesla | $98.41 | $98.41 | about even |

**All together:** $1,783.65 from $1,800 (-16.35)

## What each one is doing

- **Nvidia buy & hold:** NVDA $100.18, cash $0.51. Holding.
- **Nvidia trend (200 day):** cash $100.30. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.31, GLD $19.80, BTC/USD $9.83, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **RSI dip-buying (S&P 500):** SPY $98.86, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $98.85, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $98.85, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $98.85, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Amazon trend (200 day):** AMZN $98.64, cash $0.51. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Amazon buy & hold:** AMZN $98.26, cash $0.51. Holding.
- **Wide momentum (10 ETFs):** XLE $98.11, cash $0.51. Holding XLE until next month's check.
- **Apple buy & hold:** AAPL $98.09, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $98.09, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).
- **Tesla buy & hold:** TSLA $97.90, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $97.90, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).
- **Bitcoin buy & hold:** BTC/USD $95.98, cash $2.39. Holding.
- **Microsoft buy & hold:** MSFT $97.85, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $97.85, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 10 | 70.0% | $112.82 | -11% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 64 | 46.9% | $56.70 | -51% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 81 | 48.1% | $53.54 | -54% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 81 | 46.9% | $48.91 | -65% |
| Coin flip (luck benchmark) | Luck benchmark | 81 | 46.9% | $48.91 | -55% |

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
