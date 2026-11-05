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

    def test_first_day_levels_and_losing_position_is_hold(self):
        r = row("LRCX", entry=239.36, mark=189.80)
        levels.apply(self.con, "2026-11-05", [r], {"LRCX": bars([190.0] * 29 + [189.80], rng=8.0)})
        self.assertAlmostEqual(r["stop_price"], 189.80 - 3 * 8.0, places=1)
        self.assertAlmostEqual(r["target_price"], 189.80 + 2 * 24.0, places=1)
        self.assertEqual(r["action"], "HOLD")          # a 21% loss from purchase isn't an instant SELL
        self.assertIn("auto levels", r["action_reason"])

    def test_trailing_stop_only_rises(self):
        r = row("QQQ", 724.04, 650.0)
        levels.apply(self.con, "2026-11-05", [r], {"QQQ": bars([650.0] * 30, rng=10.0)})
        first = r["stop_price"]
        r = row("QQQ", 724.04, 700.0)
        levels.apply(self.con, "2026-11-20", [r], {"QQQ": bars([650.0] * 25 + [680, 690, 700, 700, 700], rng=10.0)})
        self.assertGreater(r["stop_price"], first)       # price rose -> stop rose
        risen = r["stop_price"]
        r = row("QQQ", 724.04, 690.0)
        levels.apply(self.con, "2026-11-21", [r], {"QQQ": bars([650.0] * 25 + [680, 690, 700, 700, 690], rng=10.0)})
        self.assertGreaterEqual(r["stop_price"], risen)  # price dipped -> stop stays put

    def test_stop_hit_is_sell_and_own_levels_win(self):
        r = row("ASML", 1695.6, 1378.8)
        levels.apply(self.con, "2026-11-05", [r], {"ASML": bars([1378.8] * 30, rng=40.0)})
        r = row("ASML", 1695.6, 1250.0)
        levels.apply(self.con, "2026-11-06", [r], {"ASML": bars([1378.8] * 29 + [1250.0], rng=40.0)})
        self.assertEqual(r["action"], "SELL")            # fell through the 3 x ATR stop
        mine = row("DIS", 112.59, 117.2, stop_price=100.0, target_price=140.0)
        levels.apply(self.con, "2026-11-05", [mine], {"DIS": bars([117.2] * 30)})
        self.assertEqual((mine["stop_price"], mine.get("levels_auto")), (100.0, None))


if __name__ == "__main__":
    unittest.main()
