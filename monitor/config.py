"""Settings shared by every layer. Change values here, not in the code."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

POSITIONS_FILE = os.path.join(BASE_DIR, "positions.json")
SNAPSHOT_DIR = os.path.join(BASE_DIR, "snapshots")
DB_FILE = os.path.join(BASE_DIR, "monitor.db")

RISK_FREE_RATE = 0.045      # annual, used for Black-Scholes Greeks
CONTRACT_MULTIPLIER = 100   # one option contract = 100 shares
