"""Live holdings from IB, saved to GitHub by the Mac (so nobody has to tell the system about trades).

Every round of the IB trader (every 2 minutes in market hours), the Mac compares the stocks and cash IB reports
with monitor/positions.json. When something changed (a trade by the Mac or by you in the IB app, a deposit),
it rewrites positions.json, keeping your own stops/targets and each stock's buy date, and pushes it to GitHub.
The dashboard's live table and the evening run then always use your real holdings.

monitor/positions_meta.json records when this happened; the evening IB report sync (ibkr_sync) doesn't overwrite
holdings that are newer than IB's report.

Pushing needs a GitHub key on the Mac (mac/set-token.sh). Without it, this does nothing but warn once a day.
"""
import datetime as dt
import json
import os
import subprocess

from . import config, ibkr_sync

META_FILE = os.path.join(config.BASE_DIR, "positions_meta.json")
REPO = os.path.dirname(config.BASE_DIR)


def from_ib(ib, current, today):
    """positions.json content built from IB's live positions and cash."""
    synced = []
    for p in ib.positions():
        c = p.contract
        if c.secType != "STK" or not p.position:
            continue
        synced.append({"asset_type": "shares", "ticker": c.symbol, "contracts": round(float(p.position), 4),
                       "entry_price": round(float(p.avgCost), 4), "note": "Interactive Brokers (live from the Mac)"})
    vals = {v.tag: v.value for v in ib.accountSummary() if v.currency in ("USD", "BASE", "")}
    cash = vals.get("TotalCashValue")
    book = ibkr_sync.merge(current, synced, float(cash) if cash not in (None, "") else None, today)
    for p in book:
        if p.get("asset_type") == "cash":
            p["note"] = f"IB cash, live from the Mac ({today})"
    return book


def fingerprint(book):
    shares = sorted((p["ticker"], round(float(p.get("contracts") or 0), 4)) for p in book if p.get("asset_type") == "shares")
    cash = sum(float(p.get("amount", p.get("contracts")) or 0) for p in book if p.get("asset_type") == "cash")
    return shares, round(cash)


def git(*args, timeout=120):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def save_and_push(book, now):
    with open(config.POSITIONS_FILE, "w") as f:
        f.write(json.dumps(book, indent=2) + "\n")
    with open(META_FILE, "w") as f:
        json.dump({"source": "IB live (Mac)", "date": now.date().isoformat(), "time": now.isoformat(timespec="seconds")},
                  f, indent=1)
        f.write("\n")
    git("add", config.POSITIONS_FILE, META_FILE)
    ok, out = git("-c", "user.name=ib-trader (Mac)", "-c", "user.email=ib-trader@users.noreply.github.com",
                  "commit", "-q", "-m", "Holdings: live update from IB (Mac)")
    if not ok and "nothing to commit" not in out:
        return False, out
    for _ in range(3):
        git("pull", "-q", "--rebase", "-X", "theirs")
        ok, out = git("push", "-q", "origin", "HEAD:main")
        if ok:
            return True, "pushed"
    # couldn't push (no key yet, or offline): undo the local commit so code updates keep downloading normally
    git("fetch", "-q", "origin", "main")
    git("reset", "-q", "--hard", "origin/main")
    return False, out


def sync(ib, now, state):
    """Called every round. Returns a status line, or None when nothing changed."""
    try:
        current = json.load(open(config.POSITIONS_FILE))
    except (OSError, ValueError):
        current = []
    book = from_ib(ib, current, now.date().isoformat())
    if fingerprint(book) == fingerprint(current):
        return None
    last_fail = state.get("push_failed_at")
    if last_fail and (now - last_fail).total_seconds() < 1800:
        return None  # after a failed push, retry every 30 minutes, not every round
    ok, out = save_and_push(book, now)
    state["push_failed_at"] = None if ok else now
    if ok:
        return "holdings updated: " + ", ".join(f"{t} {q:g}" for t, q in fingerprint(book)[0]) + \
               f", cash ${fingerprint(book)[1]:,}"
    warned = state.get("push_warned")
    if warned != now.date().isoformat():
        state["push_warned"] = now.date().isoformat()
        return ("WARN couldn't save your current holdings to GitHub (" + out[:120] + "). Run "
                "`bash ~/trading-bot/mac/set-token.sh` on the Mac to add the GitHub key.")
    return None
