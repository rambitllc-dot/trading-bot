import json
import os
import tempfile
import unittest

from monitor import positions, run
from monitor.tests.test_layer3 import MacroProvider


class CashTest(unittest.TestCase):
    def test_cash_counts_in_value_but_is_not_traded_or_looked_up(self):
        d = tempfile.mkdtemp()
        path = os.path.join(d, "pos.json")
        json.dump([{"asset_type": "shares", "ticker": "SPY", "contracts": 1, "entry_price": 700},
                   {"asset_type": "cash", "amount": 5.21}], open(path, "w"))
        self.assertEqual(positions.load(path)[1]["id"], "CASH")
        res = run.run("2026-11-06", positions_file=path, provider=MacroProvider(True),
                      db=os.path.join(d, "m.db"), snap_dir=os.path.join(d, "s"))
        cash = [r for r in res["positions"] if r["asset_type"] == "cash"][0]
        self.assertEqual((cash["value"], cash["pnl"], cash["action"]), (5.21, 0.0, "HOLD"))
        self.assertAlmostEqual(res["totals"]["value"], 733.0 + 5.21)
        self.assertNotIn("CASH", [n["ticker"] for n in res["news"]])
        self.assertIn("Cash", [a["name"] for a in res["analytics"]["allocation"]["sector"]])


if __name__ == "__main__":
    unittest.main()
