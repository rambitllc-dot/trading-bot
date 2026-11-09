# Trading Bot Manual

A plain-English guide to how your trading system works, how to turn it on and off, and what to check if something breaks. Repo: github.com/rambitllc-dot/trading-bot.

## 1. The big picture

The system has four parts that work together:

1. **The evening monitor (GitHub).** Every weekday after the market closes (about 1:35 PM Pacific), GitHub runs the monitor. It reads your Interactive Brokers (IB) positions, ranks about 520 stocks and ETFs, applies your rules, and decides what to sell, buy or hold for the next day.
2. **The dashboard (Streamlit).** rambit-monitor.streamlit.app shows everything the monitor found: your positions, the plan labels, the swap line, wins and losses, and the swap scorecard.
3. **Telegram messages.** Your Rambit Monitor bot sends a "Daily decisions" report every evening, and a message for every trade the Mac makes.
4. **The IB trader (your MacBook).** The Mac runs IB Gateway plus a small program. During market hours it places the trades from the evening plan on your real IB account and watches every stop and target every 2 minutes.

There is also an optional **practice autopilot** on Alpaca (play money) and the **old paper bot** from November, both separate from your real IB money.

## 2. The trading rules

You don't stick with any stock; the money follows whatever is winning.

| Situation | What happens |
| --- | --- |
| Down 6% from your buy price | SELL now, swap into the strongest stock |
| Was up 10%+, falls back to your buy price | SELL at breakeven, swap |
| Hits its profit target | SELL, take the profit, swap |
| Closes below its 50-day average | WEAK, first in line for the next swap |
| Losing a little | Next in line |
| Another stock clearly ranks higher | Swap (each stock at most every 2 business days) |

More details:

- **Stops only move up.** The stop is the highest of three things: a trailing stop (3 times the stock's normal daily move below its highest close), 6% below your buy price, and your buy price once the stock has been up 10%.
- **Target** is set at twice the stock's normal swing above the starting price.
- **Ranking score (0-100):** momentum 40%, steadiness 30%, trend 20%, news 10%. A swap needs a candidate scoring 80 or more and at least 25 points above the stock it replaces.
- **Each stock can be swapped at most once every 2 business days.** A stock bought on Friday can be swapped from Tuesday's evening run (trade at Wednesday's open). The waiting period never blocks the 6% stop.
- **A stock that hits its stop or target skips the waiting period** and is replaced right away.
- **No buying back** a stock that was sold in the last 30 days.
- **Sector limit:** never more than 2 stocks from the same sector. Any buy (swap, stop-out replacement, new money) skips a stock whose sector is already full. Stocks you already hold aren't sold just for this; the limit stops it from getting worse, and swaps move you toward balance over time.
- **Market weather:** when the S&P 500 closes below its 200-day average 2 days in a row (a "storm"), no new stocks are bought: swaps pause, and new money and money from stop-outs wait in SGOV (a short-term Treasury fund, about 4% a year). Your stocks keep their stops. After 2 closes back above the average, the SGOV money goes back into the strongest stocks. Shown on the dashboard and in the evening Telegram report.
- **Uptrends only:** a stock is bought only if it's above its 50- and 200-day averages, its 200-day average is rising, and it's within 25% of its 1-year high.
- **Sized by how jumpy it is:** steady stocks get more money and jumpy ones less (0.5x to 1.5x of an equal share), and no single stock gets more than 35% of the account. A swap moves the sold stock's money into the new one up to that 35%; any extra is invested as new money.
- **Earnings guard:** no buying a stock that reports earnings within the next 5 business days, because an overnight earnings jump can skip right past the 6% stop. Stocks you hold aren't sold for this; the evening Telegram report warns you when one of them reports soon.
- **Equal weight:** new stocks get about 20% of the account each; a swap uses all the money from the stock it replaces.
- **New money (deposits):** when $50 or more of cash shows up that no planned trade is using (like your deposit on the 20th), the Mac invests it the same day, as soon as IB shows it as available. It buys the strongest stocks (score 80+) from **sectors you don't own yet**, each about the size of your current holdings: 1 stock for a small deposit, up to 3 for a bigger one. If no stock scores 80+, it buys SPY so the money keeps pace with the S&P 500. You get a Telegram message saying what it bought and why. Settings: `DEPOSIT_*` in `monitor/config.py`.

These are fixed rules, not predictions. They limit losses but don't guarantee profits. This isn't financial advice.

## 3. A normal day

- **6:30 AM Pacific (market open):** the Mac places any trades from last night's plan, then checks stops and targets every 2 minutes.
- **During the day:** if a stop or target is hit, the Mac sells, buys the strongest replacement, and messages you on Telegram. New cash ($50+) is invested the same day.
- **1:00 PM:** market closes.
- **About 1:35 PM:** the GitHub monitor runs, syncs your IB positions, makes tomorrow's plan, updates the dashboard, and sends the "Daily decisions" Telegram message.
- **11:45 PM:** IB Gateway restarts itself.
- **About once a week:** IB asks you to approve the Gateway login on your phone (IB Key). If you miss it, Telegram warns you that the trader can't trade.

## 4. Turning things on and off

**Pause the IB trader (real money) - easiest way:**

1. Open the GitHub app or github.com, go to the trading-bot repo.
2. Open the file `monitor/ib_switch.json` and tap the pencil (edit).
3. Change `"paused": false` to `"paused": true` and commit.
4. Within a few minutes the Mac stops trading. Change it back to `false` to resume.

**Pause on the Mac itself:** in Terminal, run `open -e ~/ib-trader/settings.json`, change `"paused": false` to `true`, save, then restart the trader (see section 6).

**Pause the practice autopilot (Alpaca):** same idea, file `monitor/autotrade/switch.json`.

**Stop the evening monitor:** on GitHub, go to Actions, choose "Portfolio monitor", tap the ... menu and choose Disable workflow. Enable it the same way.

**Stop the old paper bot:** Actions, "Paper trading bot", Disable workflow.

**Switch the IB trader between real and paper:** in `~/ib-trader/settings.json`, set `"live": true` and `"port": 4001` for real money, or `"live": false` and `"port": 4002` for IB's paper account. IB Gateway must be logged in to the matching account, or the trader refuses to trade.

**Turn Telegram messages off:** in `monitor/config.py` on GitHub, set `NOTIFY_ENABLED = False`.

## 5. Running things by hand

- **Run the monitor now:** GitHub, Actions, Portfolio monitor, Run workflow (leave the box unticked).
- **Send a Telegram test message:** same, but tick "Only send a test message to your phone".
- **Refresh the dashboard after an update:** Manage app (bottom right), the ... menu, Reboot app. Or ... menu, Clear cache, then Rerun.
- **Test the Mac connection to IB:** in Terminal, run `cd ~/trading-bot && python3.15 -m monitor.ib_trader --once`. Outside market hours it should say "market closed".
- **See what the Mac trader is doing:** `tail -f ~/ib-trader/trader.log` (press Control + C to stop watching).

## 6. The Mac setup

- **Must stay:** plugged in, on Wi-Fi, with IB Gateway open. The lid can be closed; sleep was disabled with `pmset`.
- **IB Gateway settings:** IB API, Live Trading; API Settings: Read-Only unticked, socket port 4001, localhost only ticked; Lock and Exit: Auto restart 11:45 PM; Precautions: Bypass Order Precautions ticked.
- **The trader starts by itself** when the Mac starts, and restarts if it stops.
- **Restart the trader:** `launchctl kickstart -k gui/$(id -u)/com.rambit.ibtrader`
- **Get the latest code:** the trader pulls updates from GitHub by itself. To force it: `cd ~/trading-bot && git pull`.
- **Reinstall from scratch:** `git clone https://github.com/rambitllc-dot/trading-bot.git ~/trading-bot` then `bash ~/trading-bot/mac/setup.sh` (type REAL for the real account).
- **Python:** use `python3.15`, not `python3` (that one is the Mac's old built-in 3.9).

## 7. Keys and secrets

Stored in GitHub: Settings, Secrets and variables, Actions.

| Secret | What it's for |
| --- | --- |
| ALPACA\_KEY / ALPACA\_SECRET | Old paper bot (Alpaca) |
| ALPACA\_AUTO\_KEY / ALPACA\_AUTO\_SECRET | Practice autopilot (second Alpaca paper account) |
| ANTHROPIC\_API\_KEY | Claude news summaries |
| IBKR\_FLEX\_TOKEN / IBKR\_FLEX\_QUERY\_ID | Reads your IB positions and trades (read-only) |
| TELEGRAM\_BOT\_TOKEN / TELEGRAM\_CHAT\_ID | Telegram messages |

On the Mac, the Telegram details live in `~/ib-trader/settings.json`. The bot token must be the full token: number, colon, then the code.

**Renewals to remember:**

- Anthropic API key expires **December 5, 2026**. Make a new one in the Claude Console and update the GitHub secret.
- IB Flex token expires about **November 6, 2027**. A reminder is set for October 25, 2027.

## 8. Troubleshooting

- **No Telegram messages:** check the bot token is complete; send /start to your bot once; run the Telegram test from Actions.
- **Telegram says "Can't trade right now":** usually IB Gateway needs your weekly phone approval, or the Mac lost Wi-Fi. Open IB Gateway on the Mac and log in again.
- **Dashboard shows an error:** Reboot app from Manage app. If it persists, check the latest Actions run for a red X.
- **A GitHub run has a red X:** open it, find the red step, take a screenshot and send it to Claude.
- **IB sync says "waiting":** normal right after you trade by hand; IB's report catches up the next business day.
- **Something looks wrong with real money:** pause first (section 4), then investigate.

## 9. Where things live in the repo

- `monitor/positions.json` - your positions (updated automatically from IB)
- `monitor/watchlist.json` - stocks you'd like to buy and your buy prices
- `monitor/config.py` - all the settings and rule numbers
- `monitor/output/ib_plan.json` - tonight's plan for the Mac
- `monitor/logs/` - the log of each evening run
- `monitor/ib_switch.json` - pause switch for the IB trader
- `mac/setup.sh` - Mac installer
- `monitor/README.md` - technical notes

## 10. Ideas on hold (for later)

- **Politicians' trades:** a small ranking bonus for stocks members of Congress recently bought (they report up to 45 days late, so it's a weak signal).
