# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 07:01 UTC · Bitcoin $76,375.57 · US stock market closed

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Apple buy & hold | Hold | Stock | $100.77 | +$0.77 (+0.8%) | 1 |
| 2 | Apple trend (200 day) | Static rule | Stock | $100.77 | +$0.77 (+0.8%) | 1 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Amazon trend (200 day) | Static rule | Stock | $100.00 | +$0.00 (+0.0%) | 0 |
| 5 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.47 | -$0.53 (-0.5%) | 3 |
| 6 | Wide momentum (10 ETFs) | Monthly pick | ETF | $99.39 | -$0.61 (-0.6%) | 1 |
| 7 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.37 | -$0.63 (-0.6%) | 1 |
| 8 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.37 | -$0.63 (-0.6%) | 1 |
| 9 | S&P 500 buy & hold | Hold | ETF | $99.37 | -$0.63 (-0.6%) | 1 |
| 10 | S&P 500 trend (200 day) | Static rule | ETF | $99.37 | -$0.63 (-0.6%) | 1 |
| 11 | Tesla buy & hold | Hold | Stock | $99.03 | -$0.97 (-1.0%) | 1 |
| 12 | Tesla trend (200 day) | Static rule | Stock | $99.03 | -$0.97 (-1.0%) | 1 |
| 13 | Amazon buy & hold | Hold | Stock | $98.83 | -$1.17 (-1.2%) | 1 |
| 14 | Nvidia buy & hold | Hold | Stock | $98.11 | -$1.89 (-1.9%) | 1 |
| 15 | Nvidia trend (200 day) | Static rule | Stock | $98.11 | -$1.89 (-1.9%) | 1 |
| 16 | Microsoft buy & hold | Hold | Stock | $97.78 | -$2.22 (-2.2%) | 1 |
| 17 | Microsoft trend (200 day) | Static rule | Stock | $97.78 | -$2.22 (-2.2%) | 1 |
| 18 | Bitcoin buy & hold | Hold | Bitcoin | $97.24 | -$2.76 (-2.8%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $97.24 | $100.00 | trading |
| S&P 500 | $99.37 | $99.37 | about even |
| Apple | $100.77 | $100.77 | about even |
| Microsoft | $97.78 | $97.78 | about even |
| Nvidia | $98.11 | $98.11 | about even |
| Amazon | $98.83 | $100.00 | trading |
| Tesla | $99.03 | $99.03 | about even |

**All together:** $1,783.77 from $1,800 (-16.23)

## What each one is doing

- **Apple buy & hold:** AAPL $100.26, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $100.26, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Amazon trend (200 day):** cash $100.00. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.31, GLD $19.83, BTC/USD $9.71, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **Wide momentum (10 ETFs):** XLE $98.88, cash $0.51. Holding XLE until next month's check.
- **RSI dip-buying (S&P 500):** SPY $98.86, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $98.86, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $98.86, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $98.86, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Tesla buy & hold:** TSLA $98.52, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $98.52, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).
- **Amazon buy & hold:** AMZN $98.32, cash $0.51. Holding.
- **Nvidia buy & hold:** NVDA $97.60, cash $0.51. Holding.
- **Nvidia trend (200 day):** NVDA $97.60, cash $0.51. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Microsoft buy & hold:** MSFT $97.27, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $97.27, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).
- **Bitcoin buy & hold:** BTC/USD $94.85, cash $2.39. Holding.

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 5 | 100.0% | $121.67 | 0% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 49 | 57.1% | $102.12 | -18% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Coin flip (luck benchmark) | Luck benchmark | 49 | 44.9% | $59.33 | -47% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 39 | 38.5% | $52.59 | -48% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 49 | 34.7% | $37.73 | -64% |

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
