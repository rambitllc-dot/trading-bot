"""Snapshots and the SQLite database.

Every run saves each underlying's full pulled chain to snapshots/TICKER_YYYY-MM-DD.json and mirrors it
into one SQLite database, so later layers can compare today with the prior run (new strikes, new
expiries, IV history). Re-running for the same --asof date replaces that date's rows.
"""
import json
import os
import sqlite3

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS underlyings (
    asof TEXT, ticker TEXT, spot REAL, pulled_at TEXT, n_expiries INTEGER, n_contracts INTEGER,
    PRIMARY KEY (asof, ticker));
CREATE TABLE IF NOT EXISTS chain (
    asof TEXT, ticker TEXT, expiry TEXT, option_type TEXT, strike REAL, contract_symbol TEXT,
    bid REAL, ask REAL, last REAL, mark REAL, iv REAL, volume REAL, open_interest REAL,
    PRIMARY KEY (asof, ticker, expiry, option_type, strike));
CREATE INDEX IF NOT EXISTS chain_lookup ON chain (ticker, expiry, option_type, strike);
CREATE TABLE IF NOT EXISTS valuations (
    asof TEXT, position_id TEXT, ticker TEXT, asset_type TEXT, option_type TEXT, strike REAL, expiry TEXT,
    contracts REAL, entry_price REAL, target_price REAL, stop_price REAL, spot REAL, mark REAL, iv REAL,
    value REAL, cost REAL, pnl REAL, pnl_pct REAL, dte INTEGER, progress_target REAL, progress_stop REAL,
    delta REAL, gamma REAL, theta REAL, vega REAL, pos_delta REAL, pos_theta REAL, pos_vega REAL,
    status TEXT, progress_text TEXT,
    PRIMARY KEY (asof, position_id));
"""


def connect(path=None):
    con = sqlite3.connect(path or config.DB_FILE)
    con.executescript(SCHEMA)
    return con


def snapshot_path(ticker, asof, folder=None):
    return os.path.join(folder or config.SNAPSHOT_DIR, f"{ticker}_{asof}.json")


def save_snapshot(con, snap, asof, folder=None):
    folder = folder or config.SNAPSHOT_DIR
    os.makedirs(folder, exist_ok=True)
    with open(snapshot_path(snap["ticker"], asof, folder), "w") as f:
        json.dump({"asof": asof, **snap}, f, separators=(",", ":"))
    t = snap["ticker"]
    con.execute("DELETE FROM chain WHERE asof=? AND ticker=?", (asof, t))
    con.execute("INSERT OR REPLACE INTO underlyings VALUES (?,?,?,?,?,?)",
                (asof, t, snap["spot"], snap["pulled_at"], len(snap["expiries"]), len(snap["contracts"])))
    con.executemany(
        "INSERT OR REPLACE INTO chain VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(asof, t, c["expiry"], c["option_type"], c["strike"], c.get("contract_symbol"), c.get("bid"),
          c.get("ask"), c.get("last"), c.get("mark"), c.get("iv"), c.get("volume"), c.get("open_interest"))
         for c in snap["contracts"] if c.get("strike") is not None])
    con.commit()


def load_snapshot(ticker, asof, folder=None):
    path = snapshot_path(ticker, asof, folder)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def prior_asof(con, ticker, asof):
    """The most recent stored date before `asof` for this underlying, or None."""
    row = con.execute("SELECT MAX(asof) FROM underlyings WHERE ticker=? AND asof<?", (ticker, asof)).fetchone()
    return row[0] if row else None


def chain_rows(con, ticker, asof):
    cur = con.execute("SELECT expiry, option_type, strike, bid, ask, last, mark, iv, volume, open_interest "
                      "FROM chain WHERE ticker=? AND asof=?", (ticker, asof))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def save_valuations(con, asof, rows):
    con.execute("DELETE FROM valuations WHERE asof=?", (asof,))
    cols = ["position_id", "ticker", "asset_type", "option_type", "strike", "expiry", "contracts", "entry_price",
            "target_price", "stop_price", "spot", "mark", "iv", "value", "cost", "pnl", "pnl_pct", "dte",
            "progress_target", "progress_stop", "delta", "gamma", "theta", "vega", "pos_delta", "pos_theta",
            "pos_vega", "status", "progress_text"]
    con.executemany(f"INSERT INTO valuations VALUES ({','.join('?' * (len(cols) + 1))})",
                    [[asof] + [r.get(c) for c in cols] for r in rows])
    con.commit()
