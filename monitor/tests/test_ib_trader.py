import datetime as dt
import os
import tempfile
import unittest
from types import SimpleNamespace as NS
from unittest import mock
from zoneinfo import ZoneInfo

from monitor import autotrade, config, ib_trader

NY = ZoneInfo("America/New_York")


class FakeIB:
    """Pretend IB Gateway: market orders fill at once at the given prices."""
    def __init__(self, prices, cash=1000.0, holdings=None, account="DU123"):
        self.prices, self.cash, self.acct = prices, cash, account
        self.pos = dict(holdings or {})  # symbol -> [qty, avg]
        self.n = 0

    def accountSummary(self):
        eq = self.cash + sum(q * self.prices[s] for s, (q, _) in self.pos.items())
        return [NS(tag="NetLiquidation", value=str(eq), currency="USD"),
                NS(tag="AvailableFunds", value=str(self.cash), currency="USD")]

    def positions(self):
        return [NS(contract=NS(symbol=s, secType="STK"), position=q, avgCost=a) for s, (q, a) in self.pos.items()]

    def qualifyContracts(self, c):
        return [c] if c.symbol in self.prices else []

    def placeOrder(self, contract, order):
        self.n += 1
        s, q, px = contract.symbol, float(order.totalQuantity), self.prices[contract.symbol]
        if order.action == "BUY":
            self.cash -= q * px
            old = self.pos.get(s, [0, 0])
            self.pos[s] = [old[0] + q, px]
        else:
            self.cash += q * px
            self.pos.pop(s)
        return NS(order=NS(orderId=self.n), orderStatus=NS(status="Filled", avgFillPrice=px), log=[])

    def sleep(self, *_):
        pass


def plan(asof="2026-11-09", **kw):
    p = {"id": "p1", "asof": asof, "equity": 1000, "cash": 0, "sells": [], "buys": [], "reserve": [], "stops": {},
         "holdings": []}
    p.update(kw)
    return p


class IBTraderTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        autotrade.configure(plan_file=os.path.join(d, "plan.json"), state_file=os.path.join(d, "state.json"),
                            log_file=os.path.join(d, "log.csv"), switch_file=os.path.join(d, "switch.json"),
                            label="test", max_order_pct=50)
        self.notify = mock.patch.object(autotrade, "notify", lambda t: None)
        self.notify.start()
        self.open_time = dt.datetime(2026, 11, 10, 10, 0, tzinfo=NY)   # Tuesday 10:00 New York

    def tearDown(self):
        self.notify.stop()
        autotrade.configure(plan_file=os.path.join(config.AUTO_DIR, "plan.json"),
                            state_file=os.path.join(config.AUTO_DIR, "state.json"),
                            log_file=os.path.join(config.AUTO_DIR, "log.csv"),
                            switch_file=os.path.join(config.AUTO_DIR, "switch.json"),
                            label="🤖 Autopilot (practice account)", max_order_pct=config.AUTO_MAX_ORDER_PCT)

    def client(self, ib):
        return ib_trader.IBClient(ib, price=lambda s: ib.prices.get(s), now=self.open_time)

    def test_market_hours(self):
        self.assertTrue(ib_trader.market_open(self.open_time)[0])
        self.assertFalse(ib_trader.market_open(dt.datetime(2026, 11, 10, 16, 5, tzinfo=NY))[0])
        self.assertFalse(ib_trader.market_open(dt.datetime(2026, 11, 14, 11, 0, tzinfo=NY))[0])  # Saturday

    def test_swap_buys_with_the_sale_money(self):
        ib = FakeIB({"CNC": 70.0, "TXN": 280.0, "XLV": 150.0}, cash=5.0,
                    holdings={"CNC": [4.9, 70.59], "TXN": [1.5, 273.6]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "CNC", "reason": "swap"}],
            buys=[{"ticker": "XLV", "replaces": "CNC", "reason": "replaces CNC"}]))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("CNC", ib.pos)
        self.assertAlmostEqual(ib.pos["XLV"][0] * 150.0, 4.9 * 70.0, delta=1.5)   # all of CNC's money, not 20%
        self.assertIn("TXN", ib.pos)

    def test_paired_buy_skipped_when_its_sale_did_not_happen(self):
        ib = FakeIB({"TXN": 280.0, "XLV": 150.0}, cash=500.0, holdings={"TXN": [0.6, 273.6]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "CNC", "reason": "swap"}],                      # CNC already gone
            buys=[{"ticker": "XLV", "replaces": "CNC", "reason": "replaces CNC"}]))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("XLV", ib.pos)                                       # no money from CNC -> no buy

    def test_stop_hit_sells_and_replaces(self):
        ib = FakeIB({"MRNA": 240.0, "XLV": 150.0}, cash=0.0, holdings={"MRNA": [0.6, 260.21]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            stops={"MRNA": {"stop": 244.6, "target": 397.0, "rule": "6% max-loss stop"}},
            reserve=[{"ticker": "XLV", "reason": "rank #1"}]))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("MRNA", ib.pos)
        self.assertIn("XLV", ib.pos)

    def test_fractional_quantity_and_paper_live_guard(self):
        ib = FakeIB({"MRK": 147.0}, cash=1000.0)
        c = self.client(ib)
        c.buy("MRK", 100.0)
        self.assertAlmostEqual(ib.pos["MRK"][0], 0.6802, places=4)              # 4 decimals, rounded down
        with mock.patch.object(ib_trader.autotrade, "load_json", return_value={"live": False, "port": 4001}):
            self.assertEqual(ib_trader.settings()["port"], 4002)                # paper never uses the live port


if __name__ == "__main__":
    unittest.main()
