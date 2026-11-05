import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from monitor import config, rotation, storage


def bars(start, daily, n=300, wiggle=0.0):
    out, p = [], start
    for i in range(n):
        p *= 1 + daily + (wiggle if i % 2 else -wiggle)
        out.append((f"d{i:03d}", p, p, 1e6))
    return out


def market():
    m = {f"S{i:02d}": bars(100, 0.0002 * (i - 10), wiggle=0.005) for i in range(20)}  # spread of performers
    m["WINR"] = bars(100, 0.004, wiggle=0.002)        # strongest, steady
    m["WIN2"] = bars(100, 0.0035, wiggle=0.002)       # second strongest
    m["LOSR"] = bars(100, -0.002, wiggle=0.01)        # weak, choppy
    m["LOS2"] = bars(100, -0.0015, wiggle=0.01)
    m["OKAY"] = bars(100, 0.0015, wiggle=0.004)
    return m


def held(*tickers, entry_date=None):
    return [{"ticker": t, "asset_type": "shares", "value": 100.0, "entry_date": entry_date, "action": "HOLD"}
            for t in tickers]


class RotationTest(unittest.TestCase):
    def setUp(self):
        self.con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        self.con.executescript(rotation.SCHEMA)

    def test_several_swaps_each_into_a_different_stock(self):
        res = rotation.run(self.con, "2026-11-05", held("LOSR", "LOS2", "WIN2"), market())
        pairs = [(s["sell"], s["buy"]) for s in res["suggestions"]]
        self.assertEqual(len(pairs), 2)                               # both weak holdings, not the strong one
        self.assertEqual(pairs[0], ("LOSR", "WINR"))                  # weakest gets the strongest
        self.assertEqual(pairs[1][0], "LOS2")
        self.assertEqual(len({b for _, b in pairs}), 2)               # different stock for each swap
        self.assertNotIn("WIN2", [b for _, b in pairs])               # already held
        alerts = rotation.alert(res)
        self.assertEqual([a["kind"] for a in alerts], ["swap", "swap"])

    def test_each_stock_once_a_week(self):
        rotation.run(self.con, "2026-11-05", held("LOSR", "LOS2"), market())
        res = rotation.run(self.con, "2026-11-08", held("LOSR", "LOS2"), market())
        self.assertTrue(all(s["pending"] for s in res["suggestions"]))   # same ideas stay open, no duplicates
        self.assertEqual(len(res["suggestions"]), 2)
        # LOSR was swapped into WINR; WINR can't be swapped again this week, LOS2's idea is still open
        res = rotation.run(self.con, "2026-11-09", held("WINR", "LOS2"), market())
        self.assertEqual([s["sell"] for s in res["suggestions"]], ["LOS2"])
        # a week later the new holding is free again (it's already the strongest, so no swap for it)
        res = rotation.run(self.con, "2026-11-12", held("WINR", "WIN2"), market())
        self.assertEqual(res["suggestions"], [])

    def test_min_hold_and_margin(self):
        res = rotation.run(self.con, "2026-11-05", held("LOSR", entry_date="2026-11-01"), market())
        self.assertEqual(res["suggestions"], [])                       # bought 4 days ago
        res = rotation.run(self.con, "2026-11-06", held("WINR"), market())
        self.assertEqual(res["suggestions"], [])                       # already holds the best
        self.assertIn("no swap", res["status"])

    def test_no_rebuy_weights_and_migration(self):
        self.con.execute("INSERT INTO rotation_log VALUES ('2026-10-20','WINR','OKAY',0,0,0,0,0,'')")
        res = rotation.run(self.con, "2026-11-05", held("LOSR"), market())
        self.assertNotEqual(res["suggestions"][0]["buy"], "WINR")      # swapped out 16 days ago
        with mock.patch.object(config, "ROTATION_WEIGHTS", {"momentum": 0.5, "steadiness": 0.4}):
            with self.assertRaises(ValueError):
                rotation.check_weights()
        old = sqlite3.connect(":memory:")
        old.execute("CREATE TABLE rotation_log (asof TEXT PRIMARY KEY, sell TEXT, buy TEXT, sell_score REAL, "
                    "buy_score REAL, sell_rank INTEGER, buy_rank INTEGER, amount REAL, reason TEXT)")
        old.execute("INSERT INTO rotation_log VALUES ('2026-11-05','DIS','MRNA',44,95,335,1,31,'x')")
        rotation.migrate(old)
        pk = [r[1] for r in old.execute("PRAGMA table_info(rotation_log)") if r[5]]
        self.assertEqual(pk, ["asof", "sell"])
        self.assertEqual(old.execute("SELECT buy FROM rotation_log").fetchone()[0], "MRNA")


if __name__ == "__main__":
    unittest.main()
