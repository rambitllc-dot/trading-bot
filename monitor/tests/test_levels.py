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
        self.assertAlmostEqual(r["stop_price"], 190.0 * 0.94, places=1)   # 6% cap beats 3 x ATR (24 below)
        self.assertAlmostEqual(r["target_price"], 189.80 + 2 * 24.0, places=1)
        self.assertEqual(r["action"], "HOLD")
        self.assertIn("max-loss", r["action_reason"])

    def test_rule_label_on_later_days(self):
        r = row("CNC", entry=70.59, mark=69.7)
        levels.apply(self.con, "2026-11-05", [r], {"CNC": bars([70.0] * 29 + [69.7], rng=3.0)})
        r = row("CNC", entry=70.59, mark=69.4)
        levels.apply(self.con, "2026-11-06", [r], {"CNC": bars([70.0] * 29 + [69.4], rng=3.0)})
        self.assertAlmostEqual(r["stop_price"], 66.35, places=2)
        self.assertEqual(r["stop_rule"], "6% max-loss stop")   # not "trailing" on the second day

    def test_already_down_more_than_cap_is_sell(self):
        r = row("LRCX", entry=239.36, mark=189.80)
        levels.apply(self.con, "2026-11-05", [r], {"LRCX": bars([190.0] * 29 + [189.80], rng=8.0)})
        self.assertEqual(r["action"], "SELL")          # cut losses: 21% below the buy price

    def test_breakeven_after_ten_percent_and_high_stop_is_not_a_sell(self):
        r = row("TXN", 100.0, 100.0)
        levels.apply(self.con, "2026-10-01", [r], {"TXN": bars([100.0] * 30, rng=10.0)})
        r = row("TXN", 100.0, 108.0)
        levels.apply(self.con, "2026-11-20", [r], {"TXN": bars([100.0] * 25 + [104, 108, 111, 109, 108], rng=10.0)})
        self.assertEqual(r["stop_price"], 100.0)       # touched +11% -> stop at the buy price
        self.assertEqual(r["action"], "HOLD")
        self.assertIn("breakeven", r["action_reason"])
        r = row("TXN", 100.0, 150.0)                   # big run: trailing stop above the start price
        levels.apply(self.con, "2026-12-20", [r], {"TXN": bars([100.0] * 25 + [130, 150, 150, 150, 150], rng=10.0)})
        self.assertGreater(r["stop_price"], 105)
        self.assertLess(r["target_price"], 165)
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
