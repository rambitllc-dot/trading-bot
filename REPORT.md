# Paper trading scoreboard

Each strategy started with **$100** of paper money on 2026-11-02.
Last update: Nov 02, 2026 18:40 UTC · Bitcoin $77,002.50 · US stock market open

| Rank | Strategy | Worth now | Profit | Trades |
|---|---|---:|---:|---:|
| 1 | Mix 60% stocks / 20% gold / 10% BTC / 10% cash | $100.02 | +$0.02 (+0.0%) | 2 |
| 2 | RSI dip-buying (S&P 500) | $100.02 | +$0.02 (+0.0%) | 1 |
| 3 | Momentum rotation (SPY/QQQ/GLD/BND) | $100.02 | +$0.02 (+0.0%) | 1 |
| 4 | S&P 500 buy & hold | $100.01 | +$0.01 (+0.0%) | 1 |
| 5 | S&P 500 trend (200 day) | $100.01 | +$0.01 (+0.0%) | 1 |
| 6 | Bitcoin trend bot (5/20 day) | $100.00 | +$0.00 (+0.0%) | 0 |
| 7 | Amazon trend (200 day) | $100.00 | +$0.00 (+0.0%) | 0 |
| 8 | Nvidia buy & hold | $100.00 | -$0.00 (-0.0%) | 1 |
| 9 | Nvidia trend (200 day) | $100.00 | -$0.00 (-0.0%) | 1 |
| 10 | Apple buy & hold | $99.99 | -$0.01 (-0.0%) | 1 |
| 11 | Apple trend (200 day) | $99.99 | -$0.01 (-0.0%) | 1 |
| 12 | Amazon buy & hold | $99.99 | -$0.01 (-0.0%) | 1 |
| 13 | Wide momentum (10 ETFs) | $99.99 | -$0.01 (-0.0%) | 1 |
| 14 | Microsoft buy & hold | $99.99 | -$0.01 (-0.0%) | 1 |
| 15 | Microsoft trend (200 day) | $99.99 | -$0.01 (-0.0%) | 1 |
| 16 | Tesla buy & hold | $99.98 | -$0.02 (-0.0%) | 1 |
| 17 | Tesla trend (200 day) | $99.98 | -$0.02 (-0.0%) | 1 |
| 18 | Bitcoin buy & hold | $98.02 | -$1.98 (-2.0%) | 1 |

## Holding vs trading, same asset

| Asset | Buy & hold | With trading rule | Better so far |
|---|---:|---:|---|
| Bitcoin | $98.02 | $100.00 | trading |
| S&P 500 | $100.01 | $100.01 | about even |
| Apple | $99.99 | $99.99 | about even |
| Microsoft | $99.99 | $99.99 | about even |
| Nvidia | $100.00 | $100.00 | about even |
| Amazon | $99.99 | $100.00 | about even |
| Tesla | $99.98 | $99.98 | about even |

**All together:** $1,798.00 from $1,800 (-2.00)

## What each one is doing

- **Mix 60% stocks / 20% gold / 10% BTC / 10% cash:** SPY $59.70, GLD $19.89, cash $20.43. Problem this run: Alpaca 403: {"code":40310000,"message":"cost basis must be \u003e= minimal amount of order 10"}.
- **RSI dip-buying (S&P 500):** SPY $99.51, cash $0.51. Holding, waiting for a bounce above the 5-day average (RSI-2 9, buys below 10).
- **Momentum rotation (SPY/QQQ/GLD/BND):** SPY $99.51, cash $0.51. Picked SPY for 2026-11 (12-month returns: SPY +11%, QQQ +9%, BND -0%, GLD -2%).
- **S&P 500 buy & hold:** SPY $99.50, cash $0.51. Holding.
- **S&P 500 trend (200 day):** SPY $99.50, cash $0.51. Signal: in the market (price $755.72 vs 200d avg $725.95).
- **Bitcoin trend bot (5/20 day):** cash $100.00. Signal: in cash (5d avg $78,385.69 vs 20d avg $80,823.58).
- **Amazon trend (200 day):** cash $100.00. Signal: in cash (price $240.34 vs 200d avg $243.39).
- **Nvidia buy & hold:** NVDA $99.49, cash $0.51. Holding.
- **Nvidia trend (200 day):** NVDA $99.49, cash $0.51. Signal: in the market (price $204.76 vs 200d avg $204.09).
- **Apple buy & hold:** AAPL $99.48, cash $0.51. Holding.
- **Apple trend (200 day):** AAPL $99.48, cash $0.51. Signal: in the market (price $344.77 vs 200d avg $296.25).
- **Amazon buy & hold:** AMZN $99.48, cash $0.51. Holding.
- **Wide momentum (10 ETFs):** XLE $99.48, cash $0.51. Picked XLE for 2026-11 (12-month returns: XLE +64%, XLV +31%, IWM +14%, VXUS +12%, SPY +11%, XLF +10%, VNQ +10%, QQQ +9%, BND -0%, GLD -2%).
- **Microsoft buy & hold:** MSFT $99.48, cash $0.51. Holding.
- **Microsoft trend (200 day):** MSFT $99.48, cash $0.51. Signal: in the market (price $521.97 vs 200d avg $436.84).
- **Tesla buy & hold:** TSLA $99.47, cash $0.51. Holding.
- **Tesla trend (200 day):** TSLA $99.47, cash $0.51. Signal: in the market (price $399.80 vs 200d avg $385.27).
- **Bitcoin buy & hold:** BTC/USD $95.63, cash $2.39. Holding.

## 15-minute Bitcoin betting test (paper)

Guessing if each 15-minute candle closes up or down. A win pays 0.8x the bet, so **55.6% wins are needed just to break even**. Each signal started with $100 and bets 5% of what it has left. Includes 30 days of history before 2026-11-02, then live candles.

| Signal | Bets | Win rate | $100 is now | Worst drop | Live bets | Live win rate |
|---|---:|---:|---:|---:|---:|---:|
| Reversal: bet against unusually big moves | 389 | 47.8% | $4.43 | -96% | 0 | - |
| Coin flip (luck benchmark) | 847 | 50.6% | $0.99 (ran out) | -99% | 0 | - |
| Session momentum: follow the busiest hour's direction | 810 | 50.4% | $0.99 (ran out) | -99% | 0 | - |
| Trend: bet with the 1-hour trend when the last candle agrees | 560 | 47.5% | $0.96 (ran out) | -99% | 0 | - |
| Momentum: bet the last candle repeats | 666 | 48.9% | $0.95 (ran out) | -99% | 0 | - |

If a signal can't beat the coin flip by a clear margin over hundreds of bets, it has no real edge.

Paper money only. Past or paper results do not predict real results.
