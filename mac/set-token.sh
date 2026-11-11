#!/bin/bash
# Lets the Mac save your live IB holdings to GitHub (so the dashboard and evening run always match IB).
# Create a fine-grained GitHub token first: GitHub > Settings > Developer settings > Personal access tokens >
# Fine-grained tokens > Generate new token: Repository access "Only select repositories" -> trading-bot;
# Permissions -> Repository permissions -> Contents: Read and write; Expiration: 1 year.
# Then run:  bash ~/trading-bot/mac/set-token.sh
set -e
REPO="$HOME/trading-bot"
read -r -s -p "Paste the GitHub token (it won't show as you paste), then press Enter: " TOKEN
echo
if [ -z "$TOKEN" ]; then echo "No token entered."; exit 1; fi
git -C "$REPO" remote set-url origin "https://x-access-token:${TOKEN}@github.com/rambitllc-dot/trading-bot.git"
chmod 600 "$REPO/.git/config"
if git -C "$REPO" ls-remote --heads origin main >/dev/null 2>&1; then
  echo "Key works. The Mac will now save your holdings to GitHub whenever they change."
  launchctl kickstart -k "gui/$(id -u)/com.rambit.ibtrader" 2>/dev/null || true
else
  echo "That token didn't work. Check it has access to trading-bot with Contents: Read and write, then run this again."
  exit 1
fi
