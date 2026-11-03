# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 14:01 UTC · Bitcoin $77,255.64 · US stock market closed

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Nvidia buy & hold | Hold | Stock | $100.60 | +$0.60 (+0.6%) | 1 |
| 2 | Nvidia trend (200 day) | Static rule | Stock | $100.60 | +$0.60 (+0.6%) | 1 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Amazon trend (200 day) | Static rule | Stock | $100.00 | +$0.00 (+0.0%) | 0 |
| 5 | Tesla buy & hold | Hold | Stock | $99.75 | -$0.25 (-0.3%) | 1 |
| 6 | Tesla trend (200 day) | Static rule | Stock | $99.75 | -$0.25 (-0.3%) | 1 |
| 7 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.68 | -$0.32 (-0.3%) | 3 |
| 8 | Amazon buy & hold | Hold | Stock | $99.63 | -$0.37 (-0.4%) | 1 |
| 9 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.45 | -$0.55 (-0.6%) | 1 |
| 10 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.45 | -$0.55 (-0.6%) | 1 |
| 11 | S&P 500 buy & hold | Hold | ETF | $99.44 | -$0.56 (-0.6%) | 1 |
| 12 | S&P 500 trend (200 day) | Static rule | ETF | $99.44 | -$0.56 (-0.6%) | 1 |
| 13 | Wide momentum (10 ETFs) | Monthly pick | ETF | $98.56 | -$1.44 (-1.4%) | 1 |
| 14 | Bitcoin buy & hold | Hold | Bitcoin | $98.33 | -$1.67 (-1.7%) | 1 |
| 15 | Microsoft buy & hold | Hold | Stock | $97.28 | -$2.72 (-2.7%) | 1 |
| 16 | Microsoft trend (200 day) | Static rule | Stock | $97.28 | -$2.72 (-2.7%) | 1 |
| 17 | Apple buy & hold | Hold | Stock | $96.46 | -$3.54 (-3.5%) | 1 |
| 18 | Apple trend (200 day) | Static rule | Stock | $96.46 | -$3.54 (-3.5%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.33 | $100.00 | trading |
| S&P 500 | $99.44 | $99.44 | about even |
| Apple | $96.46 | $96.46 | about even |
| Microsoft | $97.28 | $97.28 | about even |
| Nvidia | $100.60 | $100.60 | about even |
| Amazon | $99.63 | $100.00 | about even |
| Tesla | $99.75 | $99.75 | about even |

**All together:** $1,782.16 from $1,800 (-17.84)

## What each one is doing

- **Nvidia buy & hold:** NVDA $100.09, cash $0.51. Holding.
- **Nvidia trend (200 day):** NVDA $100.09, cash $0.51. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Amazon trend (200 day):** cash $100.00. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Tesla buy & hold:** TSLA $99.24, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $99.24, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.36, GLD $19.88, BTC/USD $9.82, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **Amazon buy & hold:** AMZN $99.12, cash $0.51. Holding.
- **RSI dip-buying (S&P 500):** SPY $98.94, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $98.94, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $98.93, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $98.93, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Wide momentum (10 ETFs):** XLE $98.05, cash $0.51. Holding XLE until next month's check.
- **Bitcoin buy & hold:** BTC/USD $95.94, cash $2.39. Holding.
- **Microsoft buy & hold:** MSFT $96.77, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $96.77, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).
- **Apple buy & hold:** AAPL $95.95, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $95.95, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 8 | 87.5% | $125.01 | -5% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 77 | 49.4% | $60.05 | -52% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 60 | 45.0% | $53.06 | -51% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 77 | 45.5% | $45.77 | -65% |
| Coin flip (luck benchmark) | Luck benchmark | 77 | 45.5% | $45.77 | -55% |

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
