"""Run with:  python -m unittest discover -s monitor/tests -t ."""
import json
import os
import tempfile
import unittest

from monitor import greeks, positions, run, storage, valuation


class FakeProvider:
    """Stands in for Yahoo: two expiries per ticker, calls and puts around the spot."""
    SPOT = {"SPCX": 125.40, "NVDA": 182.0, "SPY": 733.0}

    def spot(self, t):
        return self.SPOT[t]

    def expiries(self, t):
        return ["2026-12-18", "2027-01-15"]

    def chain(self, t, exp):
        rows = []
        for strike in (100, 125, 150, 175, 200):
            for kind in ("call", "put"):
                g = greeks.bs_greeks(kind, self.SPOT[t], strike, 0.2, 0.045, 0.6)
                rows.append({"option_type": kind, "strike": float(strike), "contract_symbol": f"{t}{exp}{kind}{strike}",
                             "bid": round(g["price"] * 0.98, 2), "ask": round(g["price"] * 1.02, 2),
                             "last": round(g["price"], 2), "iv": 0.6, "volume": 10.0, "open_interest": 100.0})
        return rows


class GreeksTest(unittest.TestCase):
    def test_textbook_values(self):  # Hull: S=K=100, T=1, r=5%, sigma=20%
        c = greeks.bs_greeks("call", 100, 100, 1, 0.05, 0.2)
        p = greeks.bs_greeks("put", 100, 100, 1, 0.05, 0.2)
        self.assertAlmostEqual(c["price"], 10.4506, places=3)
        self.assertAlmostEqual(p["price"], 5.5735, places=3)
        self.assertAlmostEqual(c["delta"], 0.6368, places=3)
        self.assertAlmostEqual(p["delta"], -0.3632, places=3)
        self.assertAlmostEqual(c["gamma"], 0.01876, places=4)
        self.assertAlmostEqual(c["vega"], 0.3752, places=3)          # per 1 IV point
        self.assertAlmostEqual(c["theta"] * 365, -6.414, places=2)   # per year
        self.assertAlmostEqual(p["theta"] * 365, -1.658, places=2)

    def test_put_call_parity(self):
        import math
        c = greeks.bs_greeks("call", 120, 100, 0.5, 0.045, 0.4)["price"]
        p = greeks.bs_greeks("put", 120, 100, 0.5, 0.045, 0.4)["price"]
        self.assertAlmostEqual(c - p, 120 - 100 * math.exp(-0.045 * 0.5), places=6)

    def test_bad_inputs(self):
        self.assertIsNone(greeks.bs_greeks("call", 100, 100, 1, 0.05, 0))
        self.assertEqual(greeks.bs_greeks("call", 110, 100, 0, 0.05, 0.3)["price"], 10)


class PositionsTest(unittest.TestCase):
    def test_example_file_loads_with_ids(self):
        book = positions.load()
        self.assertEqual(book[0]["id"], "SPCX-150C-2027-01-15")
        self.assertEqual(book[2]["id"], "SPY-shares")

    def test_rejects_bad_rows(self):
        with self.assertRaises(positions.PositionError):
            positions.normalize({"asset_type": "option", "ticker": "X", "option_type": "call", "strike": 1,
                                 "expiry": "15/01/2027", "entry_price": 1, "contracts": 1})


class EndToEndTest(unittest.TestCase):
    def test_run_saves_snapshots_db_and_values(self):
        with tempfile.TemporaryDirectory() as d:
            db, snaps = os.path.join(d, "m.db"), os.path.join(d, "snaps")
            r1 = run.run("2026-11-04", provider=FakeProvider(), db=db, snap_dir=snaps)
            r2 = run.run("2026-11-05", provider=FakeProvider(), db=db, snap_dir=snaps)
            self.assertTrue(os.path.exists(os.path.join(snaps, "SPCX_2026-11-05.json")))
            con = storage.connect(db)
            self.assertEqual(storage.prior_asof(con, "SPCX", "2026-11-05"), "2026-11-04")
            self.assertEqual(len(storage.chain_rows(con, "SPCX", "2026-11-04")), 20)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM valuations").fetchone()[0], 6)
            spcx = r2["positions"][0]
            self.assertEqual(spcx["status"], "ok")
            self.assertEqual(spcx["dte"], 71)
            self.assertAlmostEqual(spcx["value"], spcx["mark"] * 100)
            self.assertIsNotNone(spcx["delta"])
            spy = r2["positions"][2]
            self.assertEqual(spy["value"], 733.0 * 2)
            self.assertAlmostEqual(spy["progress_stop"], (740 - 733) / (740 - 680) * 100)

    def test_missing_contract_is_flagged(self):
        p = positions.normalize({"asset_type": "option", "ticker": "SPCX", "option_type": "call", "strike": 999,
                                 "expiry": "2027-01-15", "entry_price": 1, "contracts": 1})
        snap = {"spot": 125.4, "contracts": []}
        out = valuation.value_position(p, snap, "2026-11-05")
        self.assertIn("not found", out["status"])

    def test_progress_text(self):
        self.assertEqual(valuation.describe(120, None), "at or past your target")
        self.assertIn("62% of the way from entry to target", valuation.describe(62, -10))


if __name__ == "__main__":
    unittest.main()
