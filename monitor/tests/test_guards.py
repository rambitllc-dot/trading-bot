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


class WeatherAndTrendTest(unittest.TestCase):
    def series(self, closes):
        return [(f"d{i:03d}", c, c, 0, c) for i, c in enumerate(closes)]

    def test_storm_needs_two_days_below_and_two_above_to_clear(self):
        con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        from monitor import regime
        up = [100 + i * 0.1 for i in range(250)]
        self.assertFalse(regime.check(con, "2026-11-02", {"SPY": self.series(up)})["storm"])
        one_day = up + [80]
        self.assertFalse(regime.check(con, "2026-11-03", {"SPY": self.series(one_day)})["storm"])   # 1 day: no
        two_days = up + [80, 79]
        self.assertTrue(regime.check(con, "2026-11-04", {"SPY": self.series(two_days)})["storm"])   # 2 days: storm
        back_one = two_days + [200]
        self.assertTrue(regime.check(con, "2026-11-05", {"SPY": self.series(back_one)})["storm"])   # still storm
        back_two = back_one + [201]
        self.assertFalse(regime.check(con, "2026-11-06", {"SPY": self.series(back_two)})["storm"])  # cleared

    def test_uptrend_and_volatility(self):
        rising = self.series([100 * 1.002 ** i for i in range(300)])
        falling = self.series([100 * 1.002 ** i for i in range(260)] + [168 * 0.99 ** i for i in range(40)])
        self.assertTrue(rotation.uptrend(rising))
        self.assertFalse(rotation.uptrend(falling))                         # broke below its averages
        calm = self.series([100 + (i % 2) * 0.5 for i in range(100)])
        wild = self.series([100 + (i % 2) * 5 for i in range(100)])
        self.assertLess(rotation.daily_vol(calm), rotation.daily_vol(wild))

    def test_storm_parks_new_money_and_stops_swaps(self):
        con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        res = rotation.run(con, "2026-11-05", held("LOSR", "LOS2"), market(), storm=True)
        self.assertEqual(res["suggestions"], [])
        self.assertIn("storm", res["status"])
        rows = [{"ticker": "LOSR", "asset_type": "shares", "value": 100.0, "action": "HOLD"}]
        p = autotrade.build_plan("2026-11-05", rows, res, con, 1000.0, 900.0)
        self.assertTrue(p["storm"])
        self.assertEqual((p["buys"], p["deposit_candidates"]), ([], []))
        # fair weather again while holding the parking fund: sell it, money back into stocks
        fair = rotation.run(con, "2026-11-06", held("LOSR"), market())
        rows2 = rows + [{"ticker": config.SAFE_FUND, "asset_type": "shares", "value": 800.0, "action": "HOLD"}]
        p2 = autotrade.build_plan("2026-11-06", rows2, fair, con, 1000.0, 100.0)
        self.assertIn(config.SAFE_FUND, [x["ticker"] for x in p2["sells"]])
        self.assertTrue(p2["buys"])
