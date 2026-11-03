# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 13:31 UTC · Bitcoin $77,592.00 · US stock market closed

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Nvidia buy & hold | Hold | Stock | $100.12 | +$0.12 (+0.1%) | 1 |
| 2 | Nvidia trend (200 day) | Static rule | Stock | $100.12 | +$0.12 (+0.1%) | 1 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Amazon trend (200 day) | Static rule | Stock | $100.00 | +$0.00 (+0.0%) | 0 |
| 5 | Amazon buy & hold | Hold | Stock | $99.81 | -$0.19 (-0.2%) | 1 |
| 6 | Tesla buy & hold | Hold | Stock | $99.75 | -$0.25 (-0.3%) | 1 |
| 7 | Tesla trend (200 day) | Static rule | Stock | $99.75 | -$0.25 (-0.3%) | 1 |
| 8 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.73 | -$0.27 (-0.3%) | 3 |
| 9 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.41 | -$0.59 (-0.6%) | 1 |
| 10 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.41 | -$0.59 (-0.6%) | 1 |
| 11 | S&P 500 buy & hold | Hold | ETF | $99.40 | -$0.60 (-0.6%) | 1 |
| 12 | S&P 500 trend (200 day) | Static rule | ETF | $99.40 | -$0.60 (-0.6%) | 1 |
| 13 | Wide momentum (10 ETFs) | Monthly pick | ETF | $99.39 | -$0.61 (-0.6%) | 1 |
| 14 | Bitcoin buy & hold | Hold | Bitcoin | $98.75 | -$1.25 (-1.2%) | 1 |
| 15 | Microsoft buy & hold | Hold | Stock | $96.99 | -$3.01 (-3.0%) | 1 |
| 16 | Microsoft trend (200 day) | Static rule | Stock | $96.99 | -$3.01 (-3.0%) | 1 |
| 17 | Apple buy & hold | Hold | Stock | $96.73 | -$3.27 (-3.3%) | 1 |
| 18 | Apple trend (200 day) | Static rule | Stock | $96.73 | -$3.27 (-3.3%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.75 | $100.00 | trading |
| S&P 500 | $99.40 | $99.40 | about even |
| Apple | $96.73 | $96.73 | about even |
| Microsoft | $96.99 | $96.99 | about even |
| Nvidia | $100.12 | $100.12 | about even |
| Amazon | $99.81 | $100.00 | about even |
| Tesla | $99.75 | $99.75 | about even |

**All together:** $1,782.49 from $1,800 (-17.51)

## What each one is doing

- **Nvidia buy & hold:** NVDA $99.61, cash $0.51. Holding.
- **Nvidia trend (200 day):** NVDA $99.61, cash $0.51. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Amazon trend (200 day):** cash $100.00. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Amazon buy & hold:** AMZN $99.30, cash $0.51. Holding.
- **Tesla buy & hold:** TSLA $99.24, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $99.24, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.33, GLD $19.91, BTC/USD $9.87, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **RSI dip-buying (S&P 500):** SPY $98.90, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $98.90, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $98.89, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $98.89, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Wide momentum (10 ETFs):** XLE $98.88, cash $0.51. Holding XLE until next month's check.
- **Bitcoin buy & hold:** BTC/USD $96.36, cash $2.39. Holding.
- **Microsoft buy & hold:** MSFT $96.48, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $96.48, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).
- **Apple buy & hold:** AAPL $96.22, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $96.22, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 7 | 85.7% | $120.21 | -5% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 59 | 45.8% | $55.85 | -51% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 75 | 48.0% | $55.52 | -52% |
| Coin flip (luck benchmark) | Luck benchmark | 75 | 46.7% | $50.71 | -53% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 75 | 45.3% | $46.32 | -65% |

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
