import os
import tempfile
import unittest
from unittest import mock

from monitor import autotrade, config, earnings, rotation, sectors, storage
from monitor.tests.test_rotation import held, market


class SectorLimitTest(unittest.TestCase):
    def test_sector_lookup_and_limit(self):
        self.assertEqual(sectors.sector_of("CNC"), "Health Care")
        self.assertEqual(sectors.sector_of("XLF"), "Financials")
        self.assertTrue(sectors.over_limit("Health Care", 3))
        self.assertFalse(sectors.over_limit("Health Care", 2))
        self.assertFalse(sectors.over_limit("Other", 9))           # unknown sector never blocks

    def test_swap_skips_a_candidate_from_a_full_sector(self):
        con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        fake = {"WINR": "Health Care", "WIN2": "Health Care", "LOSR": "Health Care", "LOS2": "Health Care"}
        with mock.patch.object(sectors, "sector_of", lambda t: fake.get(t, "Energy")):
            res = rotation.run(con, "2026-11-05", held("LOSR", "LOS2"), market())
        buys = [s["buy"] for s in res["suggestions"]]
        # two health-care holdings: swapping one health-care stock for another keeps the count at 2 (allowed);
        # the result must never leave more than 2 health-care stocks
        after = ["LOSR", "LOS2"]
        for s in res["suggestions"]:
            after = [t for t in after if t != s["sell"]] + [s["buy"]]
        self.assertLessEqual(sum(fake.get(t, "Energy") == "Health Care" for t in after), 2)
        self.assertTrue(buys)


class EarningsGuardTest(unittest.TestCase):
    def test_blocks_only_reports_within_five_business_days(self):
        d = tempfile.mkdtemp()
        dates = {"AAA": "2026-11-12", "BBB": "2026-11-30", "CCC": None}
        block = earnings.make_blocker("2026-11-09", fetch=lambda t, a: dates.get(t),
                                      cache_file=os.path.join(d, "c.json"))
        self.assertEqual(block(["AAA", "BBB", "CCC", "SPY"]), {"AAA": "2026-11-12"})

    def test_rotation_skips_a_candidate_reporting_soon(self):
        con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        first = rotation.run(con, "2026-11-05", held("LOSR"), market())["suggestions"][0]["buy"]
        con2 = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        res = rotation.run(con2, "2026-11-05", held("LOSR"), market(), blocker=lambda ts: {first: "2026-11-06"})
        self.assertNotEqual(res["suggestions"][0]["buy"], first)
        self.assertEqual(res["earnings_soon"], {first: "2026-11-06"})


if __name__ == "__main__":
    unittest.main()
