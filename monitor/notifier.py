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


ICONS = {"SELL": "🔴", "SWAP": "🟣", "WEAK": "🟠", "BUY MORE": "🟢", "REVIEW": "🟡", "HOLD": "⚪"}
COVERED = {"swap", "stop_hit", "target_hit", "weak"}  # already shown in the per-stock lines


def _short_rule(rule):
    return (rule or "").split(" (")[0]


def digest(res):
    """The evening 'daily decisions' message: every stock's decision, stop moves, swaps, and what to do."""
    t, asof = res["totals"], res["asof"]
    pp = f" ({t['pnl_pct']:+.1f}%)" if t.get("pnl_pct") is not None else ""
    L = [f"📊 Daily decisions · {asof}", f"Your IB book ${t['value']:,.0f} · open P&L {t['pnl']:+,.2f}{pp}", ""]
    todo = []
    for r in res["positions"]:
        if r["asset_type"] == "cash":
            continue
        a = r.get("action") or "HOLD"
        line = f"{ICONS.get(a, '⚪')} {r['ticker']} {a}"
        if r.get("mark") is not None:
            line += f" · {r['mark']:,.2f}" + (f" ({r['pnl_pct']:+.1f}%)" if r.get("pnl_pct") is not None else "")
        if r.get("stop_price") is not None:
            line += f" · stop {r['stop_price']:,.2f}"
        if r.get("target_price") is not None:
            line += f" · target {r['target_price']:,.2f}"
        L.append(line)
        if a in ("SELL", "SWAP", "BUY MORE"):
            todo.append(f"{r['ticker']}: {a} - {r.get('action_reason', '')[:220]}")
        elif a == "WEAK":
            L.append("   below its 50-day average; first in line for the next swap")
    moves = [x for x in res.get("auto_levels") or [] if x.get("prev_stop") and x["stop"] > x["prev_stop"] + 0.005]
    if moves:
        L += ["", "⬆️ Stops raised:"] + [f"{x['ticker']} {x['prev_stop']:,.2f} → {x['stop']:,.2f} ({_short_rule(x.get('rule'))})"
                                     for x in moves]
    rot = res.get("rotation") or {}
    sw = rot.get("suggestions") or []
    L.append("")
    if sw:
        L += [f"🔁 SWAP: sell {s['sell']} → buy {s['buy']} (rank #{s['buy_rank']})" for s in sw]
    else:
        L.append(f"🔁 Swaps: none today ({(rot.get('status') or '').split(' (')[0][:90]})")
    he = rot.get("held_earnings") or {}
    if he:
        L += ["", "📅 Earnings coming up (an overnight jump can skip past the stop):"] + \
             [f"{t} reports on {d}" for t, d in sorted(he.items(), key=lambda x: x[1])]
    extra = [a for a in res.get("alerts") or [] if a["severity"] == "high" and a["kind"] not in COVERED]
    if extra:
        L += ["", "⚠️ Alerts:"] + [f"- {a['message'][:200]}" for a in extra[:5]]
    perf = (res.get("performance") or {}).get("wins_losses") or {}
    if perf.get("trades"):
        L += ["", f"💰 Locked in {perf['realized']:+,.2f} · {perf['wins']} win(s) / {perf['losses']} loss(es)"]
    L += ["", "👉 To do in IB:" if todo else "👉 Nothing to do in IB today."] + [f"- {x}" for x in todo]
    ap = res.get("autopilot") or {}
    if ap.get("status"):
        L += ["", f"🤖 Autopilot (practice): {ap['status'][:120]}"]
    return "\n".join(L)


def send_digest(res):
    if not (config.NOTIFY_ENABLED and config.NOTIFY_DIGEST and config.NOTIFY_CHANNEL == "telegram"):
        return maybe_send(res.get("alerts") or [], res["asof"])
    try:
        return _telegram(digest(res))
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
