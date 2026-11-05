import datetime as dt
import json
import os
import tempfile
import unittest

from monitor import analytics, config, run, storage
from monitor.tests.test_layer1 import FakeProvider


class IVProvider(FakeProvider):
    """Fake feed whose IV can be changed day by day."""
    def __init__(self, iv):
        self.iv = iv

    def chain(self, t, exp):
        rows = super().chain(t, exp)
        for r in rows:
            r["iv"] = self.iv
        return rows

    def sector(self, t):
        return "Test sector"


def days(n, start="2026-09-01"):
    d0 = dt.date.fromisoformat(start)
    return [(d0 + dt.timedelta(days=i)).isoformat() for i in range(n)]


class AnalyticsTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.db, self.snaps = os.path.join(self.d, "m.db"), os.path.join(self.d, "s")

    def go(self, asof, iv=0.6, positions_file=None):
        return run.run(asof, positions_file=positions_file, provider=IVProvider(iv), db=self.db, snap_dir=self.snaps)

    def test_building_history_then_rank(self):
        res = self.go("2026-11-05")
        env = res["analytics"]["iv_environment"][0]
        self.assertTrue(env["label"].startswith("building history: 1 of 20"))
        # 25 days of IV rising from 40% to 64%, then today at 64% = top of range -> rich
        for i, day in enumerate(days(25, "2026-10-01")):
            self.go(day, iv=0.40 + i * 0.01)
        res = self.go("2026-11-05", iv=0.64)
        env = res["analytics"]["iv_environment"][0]
        self.assertEqual(env["history_days"], 26)
        self.assertAlmostEqual(env["iv_rank"], 100.0)
        self.assertEqual(env["label"], "rich")
        self.assertTrue(any(f["kind"] == "iv_rich" for f in res["analytics"]["flags"]))
        res = self.go("2026-11-05", iv=0.41)
        self.assertEqual(res["analytics"]["iv_environment"][0]["label"], "cheap")

    def test_aggregate_greeks_and_allocation(self):
        res = self.go("2026-11-05")
        a, rows = res["analytics"], res["positions"]
        self.assertAlmostEqual(a["net_delta"], sum(r.get("pos_delta") or 0 for r in rows))
        self.assertLess(a["daily_theta"], 0)        # long options lose value each day
        self.assertGreater(a["net_vega"], 0)
        pcts = [x["pct"] for x in a["allocation"]["ticker"]]
        self.assertAlmostEqual(sum(pcts), 100.0)
        names = {x["name"] for x in a["allocation"]["sector"]}
        self.assertIn("Aerospace & Space", names)    # from the config lookup

    def test_concentration_and_expiry_flags(self):
        book = [{"asset_type": "option", "ticker": "SPCX", "option_type": "call", "strike": 125,
                 "expiry": "2026-12-18", "entry_price": 10, "contracts": 3, "entry_date": "2026-10-01"},
                {"asset_type": "shares", "ticker": "XYZ", "entry_price": 1, "contracts": 1, "entry_date": "2026-10-01"}]
        path = os.path.join(self.d, "pos.json")
        json.dump(book, open(path, "w"))
        FakeProvider.SPOT["XYZ"] = 1.0
        res = self.go("2026-11-05", positions_file=path)
        kinds = [f["kind"] for f in res["analytics"]["flags"]]
        self.assertIn("concentration", kinds)        # SPCX is ~100% of the book
        self.assertIn("expiry_watch", kinds)         # 43 days left < 45
        msg = [f["message"] for f in res["analytics"]["flags"] if f["kind"] == "expiry_watch"][0]
        self.assertIn("43 days to expiry", msg)
        self.assertNotIn("roll", msg.lower())        # facts only, no advice
        sec = [x for x in res["analytics"]["allocation"]["sector"] if x["name"] == "Test sector"]
        self.assertEqual(len(sec), 1)                # unknown ticker looked up via the provider

    def test_stored_each_run(self):
        self.go("2026-11-04"); self.go("2026-11-05")
        con = storage.connect(self.db)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM analytics").fetchone()[0], 2)
        self.assertGreater(con.execute("SELECT COUNT(*) FROM allocation WHERE asof='2026-11-05'").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
