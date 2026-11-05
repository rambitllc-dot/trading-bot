"""Tests use their own example book and an empty watchlist, never your real positions.json."""
import os

from monitor import config

_HERE = os.path.dirname(os.path.abspath(__file__))
config.POSITIONS_FILE = os.path.join(_HERE, "fixtures", "positions_example.json")
config.WATCHLIST_FILE = os.path.join(_HERE, "fixtures", "no_watchlist.json")
