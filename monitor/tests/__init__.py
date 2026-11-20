"""Tests use their own example book and an empty watchlist, never your real positions.json."""
import os

from monitor import config

_HERE = os.path.dirname(os.path.abspath(__file__))
config.POSITIONS_FILE = os.path.join(_HERE, "fixtures", "positions_example.json")
config.WATCHLIST_FILE = os.path.join(_HERE, "fixtures", "no_watchlist.json")

# Same test settings for both test runners (GitHub runs `unittest`, which doesn't read conftest.py)
import tempfile  # noqa: E402

config.DB_FILE = os.path.join(tempfile.mkdtemp(), "test_monitor.db")   # never the real monitor.db
config.OUTPUT_DIR = tempfile.mkdtemp()                                 # never the real output files
config.BUY_ONLY_UP_TODAY = False  # tests that need it switch it on with a fake price feed (no network)
config.STRATEGY = "stocks"        # the stock-bot tests; index-plan tests switch it on themselves
