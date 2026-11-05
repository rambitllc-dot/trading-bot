import os
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
    m["WINR"] = bars(100, 0.004, wiggle=0.002)        # strong, steady
    m["LOSR"] = bars(100, -0.002, wiggle=0.01)        # weak, choppy
    m["OKAY"] = bars(100, 0.0015, wiggle=0.004)
    return m


def held(*tickers, entry_date=None):
    return [{"ticker": t, "asset_type": "shares", "value": 100.0, "entry_date": entry_date, "action": "HOLD"}
            for t in tickers]


class RotationTest(unittest.TestCase):
    def setUp(self):
        self.con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        self.con.executescript(rotation.SCHEMA)

    def test_scores_and_swap(self):
        res = rotation.run(self.con, "2026-11-05", held("LOSR", "OKAY"), market())
        self.assertEqual(res["holdings"][0]["ticker"], "LOSR")          # weakest first
        s = res["suggestion"]
        self.assertEqual((s["sell"], s["buy"]), ("LOSR", "WINR"))
        self.assertIn("ranks #1", s["reason"])
        a = rotation.alert(res)[0]
        self.assertEqual(a["kind"], "swap")
        self.assertIn("sell all LOSR", a["message"])

    def test_one_swap_per_week(self):
        rotation.run(self.con, "2026-11-05", held("LOSR", "OKAY"), market())
        res = rotation.run(self.con, "2026-11-08", held("LOSR", "OKAY"), market())
        self.assertTrue(res["suggestion"]["pending"])                    # same idea stays open, no new one
        res = rotation.run(self.con, "2026-11-08", held("WINR", "OKAY"), market())
        self.assertIsNone(res["suggestion"])                             # swap done: wait out the week
        self.assertIn("next suggestion allowed from 2026-11-12", res["status"])

    def test_min_hold_and_margin(self):
        res = rotation.run(self.con, "2026-11-05", held("LOSR", entry_date="2026-10-20"), market())
        self.assertIsNone(res["suggestion"])                             # bought 16 days ago
        res = rotation.run(self.con, "2026-11-06", held("WINR"), market())
        self.assertIsNone(res["suggestion"])                             # already holds the best
        self.assertIn("isn't clearly better", res["status"])

    def test_no_rebuy_and_weights(self):
        self.con.execute("INSERT INTO rotation_log VALUES ('2026-10-20','WINR','OKAY',0,0,0,0,0,'')")
        res = rotation.run(self.con, "2026-11-05", held("LOSR"), market())
        self.assertNotEqual(res["suggestion"]["buy"], "WINR")            # swapped out 16 days ago
        with mock.patch.object(config, "ROTATION_WEIGHTS", {"momentum": 0.5, "steadiness": 0.4}):
            with self.assertRaises(ValueError):
                rotation.check_weights()


if __name__ == "__main__":
    unittest.main()
