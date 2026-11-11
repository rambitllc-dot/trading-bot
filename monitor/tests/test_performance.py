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


class VsSP500Test(unittest.TestCase):
    """Same buys and sells made in SPY: deposits don't count, sold stocks stay in the history."""

    def setUp(self):
        self.con = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "t.db"))
        performance.save_trades(self.con, [
            # Nov 2: sell all 1 AAA at 100 and buy 2 BBB at 50 (a swap); Nov 3: buy 1 more BBB at 50 (new money)
            {"trade_id": "1", "trade_date": "2026-11-02", "ticker": "AAA", "asset_type": "shares", "side": "SELL",
             "quantity": 1, "price": 100, "proceeds": 100, "commission": 0, "realized": 0},
            {"trade_id": "2", "trade_date": "2026-11-02", "ticker": "BBB", "asset_type": "shares", "side": "BUY",
             "quantity": 2, "price": 50, "proceeds": -100, "commission": 0, "realized": 0},
            {"trade_id": "3", "trade_date": "2026-11-03", "ticker": "BBB", "asset_type": "shares", "side": "BUY",
             "quantity": 1, "price": 50, "proceeds": -50, "commission": 0, "realized": 0}])
        performance.save_snapshot(self.con, "2026-11-03", [{"asset_type": "shares", "ticker": "BBB", "contracts": 3}])

    def test_shadow_mirrors_trades(self):
        b = {"SPY": bars(("2026-10-30", 500), ("2026-11-02", 500), ("2026-11-03", 500), ("2026-11-04", 550)),
             "AAA": bars(("2026-10-30", 100), ("2026-11-02", 100), ("2026-11-03", 90), ("2026-11-04", 80)),
             "BBB": bars(("2026-10-30", 50), ("2026-11-02", 50), ("2026-11-03", 50), ("2026-11-04", 60))}
        v = performance.vs_sp500(self.con, "2026-11-04", b)
        self.assertEqual(v["since"], "2026-10-30")             # held 1 AAA before the first trade
        self.assertEqual(v["holdings"], {"BBB": 3})
        # shadow: 100 in SPY at 500 (0.2 sh), swap keeps it, +50 new money -> 0.3 sh; at 550 = 165
        self.assertAlmostEqual(v["sp500"], 165.0)
        self.assertAlmostEqual(v["mine"], 180.0)                # 3 BBB at 60
        self.assertAlmostEqual(v["edge"], 15.0)
        self.assertEqual([x["mine"] for x in v["series"]], [100, 100, 150, 180])

    def test_needs_ib_report(self):
        con = sqlite3.connect(os.path.join(tempfile.mkdtemp(), "t.db"))
        self.assertIsNone(performance.vs_sp500(con, "2026-11-04", {"SPY": bars(("2026-11-04", 1))}))
