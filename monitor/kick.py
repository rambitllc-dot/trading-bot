"""Backup starter for the evening monitor run (called every 30 minutes by the always-on bot loop).

GitHub's own timer often starts scheduled runs late (hours, on busy days). On weekdays after 4:10 PM New York
time, if today's run hasn't happened and none was started in the last 3 hours, this starts it.
"""
import datetime as dt
import json
import os
import subprocess
from zoneinfo import ZoneInfo

from . import config

LATEST = os.path.join(config.BASE_DIR, "output", "valuation_latest.json")


def needed(now=None, latest_asof=None, recent_runs=None):
    now = now or dt.datetime.now(ZoneInfo("America/New_York"))
    if now.weekday() >= 5 or now.time() < dt.time(16, 10):
        return False, "not time yet"
    if latest_asof == now.date().isoformat():
        return False, "today's run already done"
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)
    if any(r >= cutoff for r in recent_runs or []):
        return False, "a run was started recently"
    return True, "starting today's evening run"


def main():
    try:
        asof = json.load(open(LATEST)).get("asof")
    except (OSError, ValueError):
        asof = None
    out = subprocess.run(["gh", "run", "list", "--workflow", "monitor.yml", "-L", "5", "--json", "createdAt"],
                         capture_output=True, text=True, timeout=60)
    runs = [dt.datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")) for r in json.loads(out.stdout or "[]")]
    go, why = needed(latest_asof=asof, recent_runs=runs)
    print("Monitor kick:", why)
    if go:
        subprocess.run(["gh", "workflow", "run", "monitor.yml", "--ref", "main"], timeout=60)


if __name__ == "__main__":
    main()
