import os
import sqlite3
import tempfile
import unittest

from monitor import ibkr_sync, performance

XML = """<FlexQueryResponse><FlexStatements><FlexStatement toDate="20261106"><Trades>
 <Trade assetCategory="STK" symbol="DIS" buySell="SELL" quantity="-2" tradePrice="110" tradeDate="20261106"
   ibCommission="-1" fifoPnlRealized="-12.5" tradeID="1" levelOfDetail="EXECUTION"/>
 <Trade assetCategory="STK" symbol="SPY" buySell="SELL" quantity="-0.1" tradePrice="740" tradeDate="20261106"
   ibCommission="-1" fifoPnlRealized="4" tradeID="2" levelOfDetail="EXECUTION"/>
 <Trade assetCategory="STK" symbol="MRNA" buySell="BUY" quantity="0.6" tradePrice="260" tradeDate="20261106"
   ibCommission="-1" fifoPnlRealized="0" tradeID="3" levelOfDetail="EXECUTION"/>
 <Trade assetCategory="STK" symbol="MRNA" buySell="BUY" quantity="0.6" tradePrice="260" tradeDate="20261106"
   tradeID="3" levelOfDetail="ORDER"/>
</Trades></FlexStatement></FlexStatements></FlexQueryResponse>"""


def bars(*pts):
    return [(d, c, c, 0, c) for d, c in pts]


class PerformanceTest(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "t.db"))

    def test_trades_saved_once_and_wins_losses(self):
        trades = ibkr_sync.parse_trades(XML)
        self.assertEqual(len(trades), 3)                      # ORDER summary rows skipped
        self.assertEqual(performance.save_trades(self.con, trades), 3)
        self.assertEqual(performance.save_trades(self.con, trades), 0)   # same trades again -> no duplicates
        w = performance.wins_losses(self.con, unrealized=10)
        self.assertEqual((w["wins"], w["losses"], w["realized"], w["total"], w["fees"]), (1, 1, -8.5, 1.5, 3.0))

    def test_swap_scorecard(self):
        self.con.execute("CREATE TABLE rotation_log (asof TEXT, sell TEXT, buy TEXT, sell_score REAL, buy_score REAL,"
                         " sell_rank INTEGER, buy_rank INTEGER, amount REAL, reason TEXT)")
        self.con.execute("INSERT INTO rotation_log VALUES ('2026-11-05','DIS','MRNA',0,0,0,0,0,'')")   # followed
        self.con.execute("INSERT INTO rotation_log VALUES ('2026-10-20','SPY','XLV',0,0,0,0,0,'')")    # skipped
        b = {"DIS": bars(("2026-11-05", 100), ("2026-11-12", 95)), "MRNA": bars(("2026-11-05", 50), ("2026-11-12", 55)),
             "SPY": bars(("2026-10-20", 100), ("2026-11-12", 102)), "XLV": bars(("2026-10-20", 100), ("2026-11-12", 101))}
        rows = [{"asset_type": "shares", "ticker": "MRNA", "entry_date": "2026-11-06"},
                {"asset_type": "shares", "ticker": "SPY", "entry_date": "2026-09-01"}]
        cards = {c["sell"]: c for c in performance.scorecard(self.con, "2026-11-12", rows, b)}
        self.assertEqual(cards["DIS"]["followed"], "yes")
        self.assertAlmostEqual(cards["DIS"]["edge"], 0.15)     # MRNA +10% vs DIS -5%
        self.assertEqual(cards["SPY"]["followed"], "no")
        self.assertAlmostEqual(cards["SPY"]["edge"], -0.01)    # skipping was right
        s = performance.score_summary(list(cards.values()))
        self.assertEqual((s["all"]["beat"], s["all"]["scored"], s["followed"]["count"], s["skipped"]["count"]), (1, 2, 1, 1))


if __name__ == "__main__":
    unittest.main()
