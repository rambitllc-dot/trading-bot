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
