"""Turns your own levels into a simple label for each position: SELL, HOLD, BUY MORE or REVIEW.

These are not predictions or advice. They only apply the plan you wrote in positions.json:
  SELL      the price reached your stop, or reached your target (take profit)
  BUY MORE  the price is at or below your optional "add_below" level
  REVIEW    something needs a decision your plan doesn't cover: few days left on an option,
            no price available, or news / volatility alerts
  HOLD      the price is between your stop and your target
  WEAK      (set by the run) closed below its 50-day average: first in line for the next swap
"""
from . import config

COLORS = {"SELL": "#FF5C5C", "BUY MORE": "#3DDC84", "BUY": "#3DDC84", "HOLD": "#8A93A3", "REVIEW": "#FFA62B",
          "WAIT": "#5A6472", "SWAP": "#B48BEB", "WEAK": "#E8803A"}


def crossed(mark, level, side, short=False):
    """Has the price reached a level? A long position's stop is hit at or BELOW it and its target at or ABOVE it
    (reversed for a short position). Decided by the position's direction, never by where the level sits
    relative to the buy price: a trailing stop can rise above the buy price and is still a stop below."""
    if mark is None or level is None:
        return False
    below = (side == "stop") != bool(short)
    return mark <= level if below else mark >= level


def _crossed(mark, level, entry, side, short=False):  # kept for older callers; entry no longer decides
    return crossed(mark, level, side, short)


def for_position(r):
    """(action, plain-English reason) for one valued position."""
    mark, entry = r.get("mark"), r.get("level_ref") or r["entry_price"]
    if r.get("status") not in (None, "ok") or mark is None:
        return "REVIEW", f"no current price ({r.get('status')})"
    short = (r.get("contracts") or 0) < 0
    if crossed(mark, r.get("stop_price"), "stop", short):
        return "SELL", f"price {mark:,.2f} reached your stop {r['stop_price']:,.2f}"
    if crossed(mark, r.get("target_price"), "target", short):
        return "SELL", f"price {mark:,.2f} reached your target {r['target_price']:,.2f} (take profit)"
    if r.get("add_below") is not None and mark <= r["add_below"]:
        return "BUY MORE", f"price {mark:,.2f} is at or below your add level {r['add_below']:,.2f}"
    dte = r.get("dte")
    if dte is not None and dte < config.REVIEW_DTE_DAYS:
        return "REVIEW", f"only {dte} days left before this option expires"
    if r.get("target_price") is None and r.get("stop_price") is None:
        return "HOLD", "no target or stop set"
    return "HOLD", "price is between your stop and your target"


ALERT_ACTION = {"target_hit": "SELL", "stop_hit": "SELL", "target_near": "HOLD", "iv_change": "REVIEW",
                "news_flag": "REVIEW", "news_negative": "REVIEW", "macro_shift": "REVIEW",
                "expiry_watch": "REVIEW", "concentration": "REVIEW", "watch_buy": "BUY", "watch_near": "REVIEW",
                "swap": "SWAP", "weak": "WEAK"}
