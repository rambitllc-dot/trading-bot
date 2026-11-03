# Going live with real money

Live trading is built into the bot but **switched off**. The paper test keeps running either way.
When it's on, only the strategies you choose trade real money, each with the budget you give it.

## Safety limits built in

- **Off by default.** Nothing happens until `live_config.json` says `"enabled": true` *and* live keys are added.
- **Spending cap.** The budgets you list must add up to no more than `max_total_dollars`, or the bot refuses to start.
- **Loss limit.** If all live strategies together fall `stop_if_down_percent` (default 20%) below what was put in,
  the bot sells everything, stops, and sends you a notification.
- **Emergency stop.** Set `"sell_everything_now": true` to sell all live positions at the next run (within 30 minutes).
  Set `"enabled": false` to stop new trades but keep what you own.
- **No borrowing, no betting.** The bot only buys with the cash in each strategy's budget. The 15-minute betting test is never live.
- **Day-trading rule.** Accounts under $25,000 can't buy and sell the same stock on the same day more than 3 times a week,
  so the live bot always waits at least until the next day to sell a stock.
- **A notification for every real trade**, plus alerts for problems.
- The live status is in `LIVE_REPORT.md`; every real trade is in `trades_live.csv`.

## Checklist to go live

1. **Pick strategies** from the December results (Claude will help). Start with 1-3, not all of them.
2. **Open a live Alpaca account** (the yellow "Open Live Account" button), verify your identity, and deposit money.
3. **Create live API keys** in the live account (different from the paper keys).
4. **Add two GitHub secrets** (repo Settings > Secrets and variables > Actions): `ALPACA_LIVE_KEY` and `ALPACA_LIVE_SECRET`.
5. **Decide on privacy.** This repo is public, so anyone could see your live balances in LIVE_REPORT.md. Before going live,
   consider making it private; Claude will then switch the schedule to the cron-job.org timer so it fits GitHub's free minutes.
6. **Edit `live_config.json`**, for example:

```json
{
  "enabled": true,
  "max_total_dollars": 300,
  "stop_if_down_percent": 20,
  "sell_everything_now": false,
  "strategies": {
    "spy_trend": 100,
    "spcx_gradual": 100,
    "sp500_momentum": 100
  }
}
```

7. Watch `LIVE_REPORT.md` and your Alpaca app for the first few days.

**After a loss-limit stop:** delete the file `live_state.json` to start fresh (the bot then starts each strategy again
with its full budget from your account's cash).

## Strategy names for live_config.json

| Name | Strategy |
|---|---|
| `btc_trend` | Bitcoin trend bot (5/20 day) |
| `btc_hold` | Bitcoin buy & hold |
| `spy_hold` | S&P 500 buy & hold |
| `spy_trend` | S&P 500 trend (200 day) |
| `mix` | Mix 60% stocks / 20% gold / 10% BTC / 10% cash |
| `momentum` | Momentum rotation (SPY/QQQ/GLD/BND) |
| `rsi_dip` | RSI dip-buying (S&P 500) |
| `momentum_wide` | Wide momentum (10 ETFs) |
| `aapl_hold`, `aapl_trend` | Apple buy & hold / trend |
| `msft_hold`, `msft_trend` | Microsoft buy & hold / trend |
| `nvda_hold`, `nvda_trend` | Nvidia buy & hold / trend |
| `amzn_hold`, `amzn_trend` | Amazon buy & hold / trend |
| `tsla_hold`, `tsla_trend` | Tesla buy & hold / trend |
| `spcx_hold`, `spcx_trend` | SpaceX buy & hold / trend (50 day) |
| `spcx_gradual` | SpaceX gradual buy (budget spread over 4 weekly buys) |
| `sp500_momentum` | Stock momentum (top 10 of the S&P 500) |
| `rsp_hold` | S&P 500 equal weight (RSP) buy & hold |

Taxes: every sale with real money is a taxable event. Alpaca sends a yearly tax form (1099).
This is not financial advice.
