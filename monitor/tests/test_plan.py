import unittest

from monitor import plan


def pos(**kw):
    r = {"entry_price": 10.0, "mark": 10.0, "target_price": 20.0, "stop_price": 5.0, "status": "ok", "dte": 100}
    r.update(kw)
    return r


class PlanTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(plan.for_position(pos(mark=4))[0], "SELL")         # stop
        self.assertIn("take profit", plan.for_position(pos(mark=21))[1])     # target
        self.assertEqual(plan.for_position(pos(mark=12))[0], "HOLD")
        self.assertEqual(plan.for_position(pos(mark=8, add_below=8.5))[0], "BUY MORE")
        self.assertEqual(plan.for_position(pos(dte=10))[0], "REVIEW")
        self.assertEqual(plan.for_position(pos(mark=None, status="no price"))[0], "REVIEW")

    def test_stop_beats_add_level(self):
        self.assertEqual(plan.for_position(pos(mark=4, add_below=8))[0], "SELL")


if __name__ == "__main__":
    unittest.main()


class CrossedTest(unittest.TestCase):
    def test_trailing_stop_above_buy_price_is_still_a_stop_below(self):
        from monitor import alerts, plan
        # TXN: bought 273.60, trailing stop now 287.00, price 300.52 -> nothing hit
        self.assertFalse(alerts.hit(300.52, 287.00, False, "stop"))
        self.assertTrue(alerts.hit(286.90, 287.00, False, "stop"))
        r = {"mark": 300.52, "entry_price": 273.6, "contracts": 0.6, "stop_price": 287.0, "target_price": 346.77,
             "status": "ok", "asset_type": "shares"}
        self.assertEqual(plan.for_position(r)[0], "HOLD")
        self.assertTrue(plan.crossed(110, 100, "stop", short=True))       # a short's stop is above the price
