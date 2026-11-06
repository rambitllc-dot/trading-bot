#!/bin/bash
# One-time setup of the IB trader on your Mac. Run it from Terminal:
#   bash ~/trading-bot/mac/setup.sh
# It installs the Python pieces, asks for your Telegram details, and makes the trader start by itself
# (and restart if it ever stops). It asks whether to trade the REAL account (port 4001) or paper (4002).
# It can only buy and sell stocks; it has no way to withdraw or transfer money.
set -e
REPO="$HOME/trading-bot"
HOME_DIR="$HOME/ib-trader"
PY="$(command -v python3)"
mkdir -p "$HOME_DIR"
if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "This needs Python 3.10 or newer. Install it from python.org (macOS 64-bit universal installer),"
  echo "then open a NEW Terminal window and run this script again."
  exit 1
fi

echo "1/4  Installing Python packages..."
"$PY" -m pip install --user --quiet --upgrade pip
"$PY" -m pip install --user --quiet ib_async yfinance requests

echo "2/4  Settings"
if [ ! -f "$HOME_DIR/settings.json" ]; then
  read -r -p "  Telegram bot token (same one as on GitHub): " TOKEN
  read -r -p "  Telegram chat id: " CHAT
  echo ""
  echo "  This trader will place REAL orders in your Interactive Brokers account."
  read -r -p "  Type REAL to confirm (anything else sets up the paper account): " MODE
  if [ "$MODE" = "REAL" ]; then LIVE=true; PORT=4001; else LIVE=false; PORT=4002; fi
  cat > "$HOME_DIR/settings.json" <<JSON
{
  "live": $LIVE,
  "port": $PORT,
  "paused": false,
  "max_order_pct": 50,
  "telegram_bot_token": "$TOKEN",
  "telegram_chat_id": "$CHAT"
}
JSON
  chmod 600 "$HOME_DIR/settings.json"
  echo "  Saved to $HOME_DIR/settings.json (live: $LIVE, port $PORT)."
else
  echo "  Keeping your existing $HOME_DIR/settings.json"
fi

echo "3/4  Making it start by itself"
PLIST="$HOME/Library/LaunchAgents/com.rambit.ibtrader.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.rambit.ibtrader</string>
  <key>ProgramArguments</key><array><string>$PY</string><string>-m</string><string>monitor.ib_trader</string></array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME_DIR/trader.log</string>
  <key>StandardErrorPath</key><string>$HOME_DIR/trader.log</string>
</dict></plist>
PL
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "4/4  Done. The trader is running."
echo "  It sends a Telegram message now, and acts only while the market is open."
echo "  Its activity:  tail -f $HOME_DIR/trader.log"
