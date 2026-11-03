# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 03, 2026 16:01 UTC · Bitcoin $77,612.70 · US stock market open

**Labels:** *Hold* = buys once and never sells (the yardstick). *Static rule* = trades by one fixed rule that never changes. *Monthly pick* = once a month, switches to whichever investment rose most over the past year.

| Rank | Strategy | Type | Market | Worth now | Profit | Trades |
|---|---|---|---|---:|---:|---:|
| 1 | Nvidia buy & hold | Hold | Stock | $100.86 | +$0.86 (+0.9%) | 1 |
| 2 | Nvidia trend (200 day) | Static rule | Stock | $100.30 | +$0.30 (+0.3%) | 2 |
| 3 | Bitcoin trend bot (5/20 day) | Static rule | Bitcoin | $100.00 | +$0.00 (+0.0%) | 0 |
| 4 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | Static rule (rebalance) | Mixed | $99.80 | -$0.20 (-0.2%) | 3 |
| 5 | RSI dip-buying (S&P 500) | Static rule | ETF | $99.74 | -$0.26 (-0.3%) | 1 |
| 6 | Momentum rotation (SPY/QQQ/GLD/BND) | Monthly pick | ETF | $99.73 | -$0.27 (-0.3%) | 1 |
| 7 | S&P 500 buy & hold | Hold | ETF | $99.73 | -$0.27 (-0.3%) | 1 |
| 8 | S&P 500 trend (200 day) | Static rule | ETF | $99.73 | -$0.27 (-0.3%) | 1 |
| 9 | Microsoft buy & hold | Hold | Stock | $99.48 | -$0.52 (-0.5%) | 1 |
| 10 | Microsoft trend (200 day) | Static rule | Stock | $99.48 | -$0.52 (-0.5%) | 1 |
| 11 | Amazon trend (200 day) | Static rule | Stock | $99.46 | -$0.54 (-0.5%) | 1 |
| 12 | Amazon buy & hold | Hold | Stock | $99.09 | -$0.91 (-0.9%) | 1 |
| 13 | Wide momentum (10 ETFs) | Monthly pick | ETF | $98.99 | -$1.01 (-1.0%) | 1 |
| 14 | Bitcoin buy & hold | Hold | Bitcoin | $98.78 | -$1.22 (-1.2%) | 1 |
| 15 | Tesla buy & hold | Hold | Stock | $98.55 | -$1.45 (-1.5%) | 1 |
| 16 | Tesla trend (200 day) | Static rule | Stock | $98.55 | -$1.45 (-1.5%) | 1 |
| 17 | Apple buy & hold | Hold | Stock | $97.89 | -$2.11 (-2.1%) | 1 |
| 18 | Apple trend (200 day) | Static rule | Stock | $97.89 | -$2.11 (-2.1%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.78 | $100.00 | trading |
| S&P 500 | $99.73 | $99.73 | about even |
| Apple | $97.89 | $97.89 | about even |
| Microsoft | $99.48 | $99.48 | about even |
| Nvidia | $100.86 | $100.30 | holding |
| Amazon | $99.09 | $99.46 | about even |
| Tesla | $98.55 | $98.55 | about even |

**All together:** $1,788.03 from $1,800 (-11.97)

## What each one is doing

- **Nvidia buy & hold:** NVDA $100.35, cash $0.51. Holding.
- **Nvidia trend (200 day):** cash $100.30. Signal: in cash (price $202.21 vs 200d avg $204.17).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $77,470.13 vs 20d avg $80,502.23).
- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.53, GLD $19.78, BTC/USD $9.87, cash $10.62. Rebalanced 2026-11, next rebalance next month.
- **RSI dip-buying (S&P 500):** SPY $99.23, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 7, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $99.22, cash $0.51. Holding SPY until next month's check.
- **S&P 500 buy & hold:** SPY $99.22, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $99.22, cash $0.51. Signal: in the market (price $752.04 vs 200d avg $726.27).
- **Microsoft buy & hold:** MSFT $98.97, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $98.97, cash $0.51. Signal: in the market (price $507.00 vs 200d avg $437.11).
- **Amazon trend (200 day):** AMZN $98.95, cash $0.51. Signal: in the market (price $245.74 vs 200d avg $243.43).
- **Amazon buy & hold:** AMZN $98.58, cash $0.51. Holding.
- **Wide momentum (10 ETFs):** XLE $98.48, cash $0.51. Holding XLE until next month's check.
- **Bitcoin buy & hold:** BTC/USD $96.39, cash $2.39. Holding.
- **Tesla buy & hold:** TSLA $98.04, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $98.04, cash $0.51. Signal: in the market (price $403.93 vs 200d avg $385.10).
- **Apple buy & hold:** AAPL $97.38, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $97.38, cash $0.51. Signal: in the market (price $338.70 vs 200d avg $296.65).

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each method started with $100 and bets 5% of what it has left.

**Labels:** *Static* = always uses the same one method, never changes. *Learning* = every 15 minutes, checks which static method won the most over the last 24 hours and copies it, or sits out if none is beating 55.6%. *Luck benchmark* = a random coin flip; anything that can't beat it has no real skill.

### Live, since 2026-11-02 (fresh $100 each)

| Method | Type | Bets | Win rate | $100 is now | Worst drop |
|---|---|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | Static (one fixed method) | 11 | 63.6% | $107.18 | -15% |
| Learning: copies whichever method has been winning lately | Learning (switches methods) | 0 | - | $100.00 | 0% |
| Trend: bet with the 1-hour trend when the last candle agrees | Static (one fixed method) | 68 | 47.1% | $55.35 | -51% |
| Session momentum: follow the busiest hour's direction | Static (one fixed method) | 85 | 48.2% | $52.26 | -55% |
| Momentum: bet the last candle repeats | Static (one fixed method) | 85 | 47.1% | $47.74 | -65% |
| Coin flip (luck benchmark) | Luck benchmark | 85 | 45.9% | $43.61 | -58% |

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
