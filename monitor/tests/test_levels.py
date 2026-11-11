import os
import tempfile
import unittest

from monitor import levels, storage


def bars(prices, rng=2.0, start=0):
    return [(f"2026-{10 + (i + start) // 28:02d}-{(i + start) % 28 + 1:02d}", p, p + rng / 2, 1e6, p - rng / 2)
            for i, p in enumerate(prices)]


def row(ticker, entry, mark, **kw):
    r = {"ticker": ticker, "asset_type": "shares", "entry_price": entry, "mark": mark, "status": "ok",
         "stop_price": None, "target_price": None, "dte": None, "position_id": f"{ticker}-shares"}
    r.update(kw)
    return r


class LevelsTest(unittest.TestCase):
    def setUp(self):
        self.con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))

    def test_atr(self):
        self.assertAlmostEqual(levels.atr(bars([100.0] * 30, rng=4.0)), 4.0)

    def test_first_day_levels(self):
        r = row("LRCX", entry=190.0, mark=189.80)
        levels.apply(self.con, "2026-11-05", [r], {"LRCX": bars([190.0] * 29 + [189.80], rng=8.0)})
        self.assertAlmostEqual(r["stop_price"], 190.0 * 0.955, places=2)  # 4.5% below the buy price
        self.assertAlmostEqual(r["target_price"], 189.80 + 2 * 24.0, places=1)
        self.assertEqual(r["action"], "HOLD")
        self.assertIn("4.5% trailing stop", r["action_reason"])

    def test_rule_label_on_later_days(self):
        r = row("CNC", entry=70.59, mark=69.7)
        levels.apply(self.con, "2026-11-05", [r], {"CNC": bars([70.0] * 29 + [69.7], rng=3.0)})
        r = row("CNC", entry=70.59, mark=69.4)
        levels.apply(self.con, "2026-11-06", [r], {"CNC": bars([70.0] * 29 + [69.4], rng=3.0)})
        self.assertAlmostEqual(r["stop_price"], 67.41, places=2)
        self.assertIn("4.5% below your buy price", r["stop_rule"])

    def test_merck_example_trails_up_and_never_down(self):
        r = row("MRK", entry=147.71, mark=147.71)
        levels.apply(self.con, "2026-11-06", [r], {"MRK": bars([147.0] * 29 + [147.71], rng=2.0)})
        self.assertAlmostEqual(r["stop_price"], 141.06, places=2)        # starts 4.5% below the buy price
        r = row("MRK", entry=147.71, mark=155.10)
        levels.apply(self.con, "2026-11-10", [r], {"MRK": bars([147.0] * 28 + [150.0, 155.10], rng=2.0)})
        self.assertAlmostEqual(r["stop_price"], 148.12, places=2)        # moved up with the new high
        r = row("MRK", entry=147.71, mark=150.0)
        levels.apply(self.con, "2026-11-11", [r], {"MRK": bars([147.0] * 28 + [155.10, 150.0], rng=2.0)})
        self.assertAlmostEqual(r["stop_price"], 148.12, places=2)        # price fell back: stop stays put
        self.assertEqual(r["action"], "HOLD")
        r = row("MRK", entry=147.71, mark=148.0)
        levels.apply(self.con, "2026-11-12", [r], {"MRK": bars([147.0] * 28 + [155.10, 148.0], rng=2.0)})
        self.assertEqual(r["action"], "SELL")                            # at/below the stop: sell (with a profit)

    def test_already_down_more_than_cap_is_sell(self):
        r = row("LRCX", entry=239.36, mark=189.80)
        levels.apply(self.con, "2026-11-05", [r], {"LRCX": bars([190.0] * 29 + [189.80], rng=8.0)})
        self.assertEqual(r["action"], "SELL")          # cut losses: 21% below the buy price

    def test_big_run_keeps_trailing_and_is_not_a_sell(self):
        r = row("TXN", 100.0, 100.0)
        levels.apply(self.con, "2026-10-01", [r], {"TXN": bars([100.0] * 30, rng=10.0)})
        r = row("TXN", 100.0, 108.0)
        levels.apply(self.con, "2026-11-20", [r], {"TXN": bars([100.0] * 25 + [104, 108, 111, 109, 108], rng=10.0)})
        self.assertAlmostEqual(r["stop_price"], 106.0, places=1)    # 4.5% below the 111 high: a locked-in gain
        self.assertEqual(r["action"], "HOLD")
        r = row("TXN", 100.0, 150.0)
        levels.apply(self.con, "2026-12-20", [r], {"TXN": bars([100.0] * 25 + [130, 150, 150, 150, 150], rng=10.0)})
        self.assertAlmostEqual(r["stop_price"], 143.25, places=2)
        self.assertEqual(r["action"], "HOLD")          # price above the stop is not a sell

    def test_weakening_below_50_day_average(self):
        up = row("CNC", 50.0, 59.0)
        levels.apply(self.con, "2026-11-05", [up], {"CNC": bars([50.0 + i * 0.2 for i in range(50)], rng=1.0)})
        self.assertFalse(up["weak"])
        down = row("MRK", 60.0, 50.0)
        levels.apply(self.con, "2026-11-05", [down], {"MRK": bars([60.0] * 49 + [50.0], rng=1.0)})
        self.assertTrue(down["weak"])
        self.assertIn("WEAKENING", down["weak_text"])

    def test_trailing_stop_only_rises(self):
        r = row("QQQ", 650.0, 650.0)
        levels.apply(self.con, "2026-11-05", [r], {"QQQ": bars([650.0] * 30, rng=10.0)})
        first = r["stop_price"]
        r = row("QQQ", 650.0, 700.0)
        levels.apply(self.con, "2026-11-20", [r], {"QQQ": bars([650.0] * 25 + [680, 690, 700, 700, 700], rng=10.0)})
        self.assertGreater(r["stop_price"], first)       # price rose -> stop rose
        risen = r["stop_price"]
        r = row("QQQ", 650.0, 690.0)
        levels.apply(self.con, "2026-11-21", [r], {"QQQ": bars([650.0] * 25 + [680, 690, 700, 700, 690], rng=10.0)})
        self.assertGreaterEqual(r["stop_price"], risen)  # price dipped -> stop stays put

    def test_stop_hit_is_sell_and_own_levels_win(self):
        r = row("ASML", 1378.8, 1378.8)
        levels.apply(self.con, "2026-11-05", [r], {"ASML": bars([1378.8] * 30, rng=40.0)})
        r = row("ASML", 1378.8, 1250.0)
        levels.apply(self.con, "2026-11-06", [r], {"ASML": bars([1378.8] * 29 + [1250.0], rng=40.0)})
        self.assertEqual(r["action"], "SELL")            # fell through the 3 x ATR stop
        mine = row("DIS", 112.59, 117.2, stop_price=100.0, target_price=140.0)
        levels.apply(self.con, "2026-11-05", [mine], {"DIS": bars([117.2] * 30)})
        self.assertEqual((mine["stop_price"], mine.get("levels_auto")), (100.0, None))


if __name__ == "__main__":
    unittest.main()


class SettledBarsTest(unittest.TestCase):
    def test_todays_row_is_ignored_during_market_hours(self):
        import datetime as dt
        from zoneinfo import ZoneInfo
        ny = ZoneInfo("America/New_York")
        b = [("2026-11-05", 74.17, 74.2, 0, 74.0), ("2026-11-06", 74.17, 74.2, 0, 69.5)]   # stale "today" row
        midday = dt.datetime(2026, 11, 6, 12, 0, tzinfo=ny)
        self.assertEqual(levels.settled(b, "2026-11-06", midday), b[:1])
        evening = dt.datetime(2026, 11, 6, 17, 0, tzinfo=ny)
        self.assertEqual(levels.settled(b, "2026-11-06", evening), b)
        con = storage.connect(os.path.join(tempfile.mkdtemp(), "m.db"))
        r = row("CNC", entry=70.59, mark=69.98)
        r["entry_date"] = "2026-11-06"
        bars_ = [(f"2026-10-{d:02d}", 70.0, 70.5, 0, 69.5) for d in range(1, 31)] + b
        levels.apply(con, "2026-11-06", [r], {"CNC": bars_}, now=midday)
        self.assertAlmostEqual(r["stop_price"], 70.59 * 0.955, places=2)   # not 4.5% below the stale 74.17
