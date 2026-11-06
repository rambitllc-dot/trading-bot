"""Layer 4b: optional notifier, off by default (NOTIFY_ENABLED in config.py).

Pushes the day's alerts to Telegram (TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID environment variables),
iMessage (macOS only, via osascript, to IMESSAGE_RECIPIENT), or a GitHub issue (GITHUB_TOKEN +
GITHUB_REPOSITORY, which GitHub Actions provides). When disabled it does nothing.
"""
import os
import platform
import subprocess

import requests

from . import config
from .alerts import SEVERITY_ORDER

ICON = {"high": "🔴", "warn": "🟠", "info": "🔵"}


def format_message(alerts, asof):
    lines = [f"Portfolio monitor {asof}: {len(alerts)} alert(s)"]
    lines += [f"{ICON.get(a['severity'], '-')} {a['message']}"
              + (f" -> Your plan: {a['action']}" if a.get("action") else "") for a in alerts]
    lines.append("Plan labels apply your own target/stop levels; they are not predictions or advice.")
    return "\n".join(lines)


def _telegram(text):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return "skipped: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set"
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30,
                      json={"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True})
    return "sent" if r.ok else f"telegram error {r.status_code}"


def _imessage(text):
    if platform.system() != "Darwin":
        return "skipped: iMessage only works on a Mac"
    if not config.IMESSAGE_RECIPIENT:
        return "skipped: IMESSAGE_RECIPIENT not set"
    esc = text.replace("\\", "\\\\").replace('"', '\\"')
    script = (f'tell application "Messages" to send "{esc}" to buddy "{config.IMESSAGE_RECIPIENT}" '
              f'of (service 1 whose service type is iMessage)')
    res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    return "sent" if res.returncode == 0 else f"imessage error: {res.stderr.strip()[:200]}"


def _github(text, asof):
    token, repo = os.environ.get("GITHUB_TOKEN"), os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return "skipped: not running on GitHub"
    r = requests.post(f"https://api.github.com/repos/{repo}/issues", timeout=30,
                      headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
                      json={"title": f"Portfolio monitor alerts {asof}", "body": text})
    return "sent" if r.ok else f"github error {r.status_code}"


def maybe_send(alerts, asof):
    if not config.NOTIFY_ENABLED:
        return "off"
    floor = SEVERITY_ORDER.get(config.NOTIFY_MIN_SEVERITY, 2)
    picked = [a for a in alerts if SEVERITY_ORDER.get(a["severity"], 9) <= floor]
    if not picked:
        return "nothing to send"
    text = format_message(picked, asof)
    try:
        if config.NOTIFY_CHANNEL == "telegram":
            return _telegram(text)
        if config.NOTIFY_CHANNEL == "imessage":
            return _imessage(text)
        if config.NOTIFY_CHANNEL == "github":
            return _github(text, asof)
        return f"skipped: unknown channel {config.NOTIFY_CHANNEL!r}"
    except requests.RequestException as e:
        return f"error: {e}"


def send_test():
    """Sends one test message through the configured channel (used by the workflow's test option)."""
    text = ("✅ Portfolio monitor is connected. You'll get swap ideas and SELL / BUY alerts here "
            "after each weekday run.")
    if config.NOTIFY_CHANNEL == "telegram":
        return _telegram(text)
    if config.NOTIFY_CHANNEL == "github":
        return _github(text, "test")
    return _imessage(text)


if __name__ == "__main__":
    print("Test message:", send_test())
