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
                    holdings={"CNC": [5, 70.59], "TXN": [2, 273.6]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "CNC", "reason": "swap"}],
            buys=[{"ticker": "XLV", "replaces": "CNC", "reason": "replaces CNC"}]))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("CNC", ib.pos)
        # CNC's $350 goes to XLV, capped at 35% of the account ($320): 2 whole shares ($300)
        self.assertEqual(ib.pos["XLV"][0], 2)
        self.assertIn("TXN", ib.pos)

    def test_already_sold_by_hand_then_cash_buys_the_planned_replacement(self):
        ib = FakeIB({"TXN": 280.0, "XLV": 150.0}, cash=500.0, holdings={"TXN": [1, 273.6]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "CNC", "reason": "swap"}],                      # CNC already sold in the app
            buys=[{"ticker": "XLV", "replaces": "CNC", "reason": "replaces CNC"}]))
        autotrade.execute(client=self.client(ib))
        self.assertIn("XLV", ib.pos)                                          # the cash goes to the planned pick

    def test_no_cash_no_replacement(self):
        ib = FakeIB({"TXN": 280.0, "XLV": 150.0}, cash=10.0, holdings={"TXN": [1, 273.6]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "CNC", "reason": "swap"}],
            buys=[{"ticker": "XLV", "replaces": "CNC", "reason": "replaces CNC"}]))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("XLV", ib.pos)                                       # no money from CNC -> no buy

    def test_stop_hit_sells_and_replaces(self):
        ib = FakeIB({"MRNA": 240.0, "XLV": 150.0}, cash=300.0, holdings={"MRNA": [1, 260.21]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            stops={"MRNA": {"stop": 244.6, "target": 397.0, "rule": "6% max-loss stop"}},
            reserve=[{"ticker": "XLV", "reason": "rank #1"}]))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("MRNA", ib.pos)
        self.assertIn("XLV", ib.pos)

    def test_fractional_quantity_and_paper_live_guard(self):
        ib = FakeIB({"MRK": 147.0}, cash=1000.0, holdings={"CNC": [4.9, 70.0]})
        ib.prices["CNC"] = 70.0
        c = self.client(ib)
        c.buy("MRK", 300.0)
        self.assertEqual(ib.pos["MRK"][0], 2)                                   # whole shares only, rounded down
        with self.assertRaises(autotrade.AlpacaError):
            c.buy("MRK", 100.0)                                                 # less than 1 share
        with self.assertRaises(autotrade.AlpacaError):
            c.close("CNC")                                                      # fractional: only in the IB app
        with mock.patch.object(ib_trader.autotrade, "load_json", return_value={"live": False, "port": 4001}):
            self.assertEqual(ib_trader.settings()["port"], 4002)                # paper never uses the live port


if __name__ == "__main__":
    unittest.main()


class DepositTest(IBTraderTest):
    def cands(self):
        return [{"ticker": "MRK", "rank": 1, "score": 99, "sector": "Health Care", "reason": "rank #1"},
                {"ticker": "LLY", "rank": 2, "score": 97, "sector": "Health Care", "reason": "rank #2"},
                {"ticker": "JPM", "rank": 3, "score": 95, "sector": "Financials", "reason": "rank #3"},
                {"ticker": "XOM", "rank": 4, "score": 90, "sector": "Energy", "reason": "rank #4"}]

    def prices(self):
        return {"CNC": 70.0, "MRK": 150.0, "LLY": 900.0, "JPM": 95.0, "XOM": 60.0, "SPY": 150.0}

    def test_deposit_goes_to_new_sectors_same_day(self):
        ib = FakeIB(self.prices(), cash=400.0, holdings={"CNC": [3, 70.0], "MRK": [1, 150.0]})  # ~$180 each
        autotrade.save_json(autotrade.PLAN_FILE, plan(deposit_candidates=self.cands()))
        msg = autotrade.execute(client=self.client(ib))
        self.assertIn("New cash found", msg)
        self.assertEqual(set(ib.pos) - {"CNC", "MRK"}, {"JPM", "XOM"})   # 2 stocks, new sectors, not more healthcare
        self.assertLess(ib.cash, 60)                                     # whole shares leave a little cash
        self.assertNotIn("LLY", ib.pos)

    def test_small_cash_is_left_and_nothing_good_means_spy(self):
        ib = FakeIB(self.prices(), cash=30.0, holdings={"CNC": [3, 70.0]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(deposit_candidates=self.cands()))
        autotrade.execute(client=self.client(ib))
        self.assertEqual(set(ib.pos), {"CNC"})                            # under $50: leave it
        ib.cash = 300.0
        autotrade.save_json(autotrade.PLAN_FILE, plan(id="p2", deposit_candidates=[], fallback="SPY"))
        autotrade.execute(client=self.client(ib))
        self.assertIn("SPY", ib.pos)                                      # nothing qualifies, SPY rising -> S&P 500
        ib.cash, ib.prices["SGOV"] = 300.0, 100.5
        autotrade.save_json(autotrade.PLAN_FILE, plan(id="p3", deposit_candidates=[], fallback="SGOV"))
        autotrade.execute(client=self.client(ib))
        self.assertIn("SGOV", ib.pos)                                     # SPY not rising -> short-term T-bills

    def test_retries_are_limited(self):
        ib = FakeIB({"CNC": 70.0}, cash=500.0, holdings={"CNC": [3, 70.0]})   # nothing buyable (no prices)
        autotrade.save_json(autotrade.PLAN_FILE, plan(deposit_candidates=self.cands()))
        for _ in range(5):
            autotrade.execute(client=self.client(ib))
        self.assertEqual(autotrade.load_state()["deposit_tries"]["2026-11-10"], config.DEPOSIT_MAX_TRIES_PER_DAY)


class CodeVersionTest(unittest.TestCase):
    def test_data_changes_do_not_count_as_code(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "a.py"), "w") as f:
            f.write("x = 1\n")
        with mock.patch.object(config, "BASE_DIR", d):
            v1 = ib_trader.code_version()
            with open(os.path.join(d, "plan.json"), "w") as f:
                f.write("{}")                                   # data commit (plans, positions, logs)
            self.assertEqual(ib_trader.code_version(), v1)
            with open(os.path.join(d, "a.py"), "w") as f:
                f.write("x = 2\n")                              # real code update
            self.assertNotEqual(ib_trader.code_version(), v1)


class IntradayTrailTest(IBTraderTest):
    def test_stop_trails_the_days_high(self):
        ib = FakeIB({"MRNA": 280.0, "XLV": 150.0}, cash=300.0, holdings={"MRNA": [1, 260.21]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            stops={"MRNA": {"stop": 248.5, "target": 397.0}}, reserve=[{"ticker": "XLV", "reason": "rank #1"}]))
        autotrade.execute(client=self.client(ib))           # sees 280: new high, stop moves to 267.40
        self.assertIn("MRNA", ib.pos)
        ib.prices["MRNA"] = 268.0
        autotrade.execute(client=self.client(ib))           # 268 is above 267.40: keep
        self.assertIn("MRNA", ib.pos)
        ib.prices["MRNA"] = 267.0
        autotrade.execute(client=self.client(ib))           # 4.5% below the 280 high: sell, still a profit
        self.assertNotIn("MRNA", ib.pos)
        self.assertIn("XLV", ib.pos)


class PeakFromPlanTest(IBTraderTest):
    def test_daytime_stop_starts_from_the_evening_high(self):
        ib = FakeIB({"MRNA": 250.4, "XLV": 150.0}, cash=300.0, holdings={"MRNA": [1, 260.21]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            stops={"MRNA": {"stop": 244.6, "target": 397.0, "peak": 269.0}}, reserve=[{"ticker": "XLV", "reason": "#1"}]))
        autotrade.execute(client=self.client(ib))           # 250.40 is 6.9% below the 269 high: sold
        self.assertNotIn("MRNA", ib.pos)
        self.assertIn("XLV", ib.pos)


class FractionalTest(IBTraderTest):
    def test_fractional_position_asks_you_once_instead_of_retrying(self):
        msgs = []
        ib = FakeIB({"MRNA": 250.0, "TGT": 95.0}, cash=0.0, holdings={"MRNA": [0.6, 260.21]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "MRNA", "reason": "stop hit"}], buys=[{"ticker": "TGT", "replaces": "MRNA", "reason": "x"}],
            stops={"MRNA": {"stop": 256.89, "peak": 269.0}}))
        with mock.patch.object(autotrade, "notify", msgs.append):
            autotrade.execute(client=self.client(ib))
            autotrade.execute(client=self.client(ib))
        self.assertIn("MRNA", ib.pos)                                   # couldn't sell a fraction via the API
        self.assertNotIn("TGT", ib.pos)                                 # so no buy without the money
        self.assertEqual(len(msgs), 1)                                   # one message, then quiet (no retry spam)
        self.assertIn("Please SELL MRNA yourself in the IB app", msgs[0])


class WholeShareTest(IBTraderTest):
    def test_manual_sale_then_planned_replacement_in_whole_shares(self):
        # you sold MRNA in the app; its planned replacement TGT ($95) is bought with the cash, whole shares only
        ib = FakeIB({"CNC": 70.0, "TGT": 95.0, "LLY": 900.0, "SPYM": 80.0}, cash=150.0, holdings={"CNC": [3, 70.0]})
        msgs = []
        autotrade.save_json(autotrade.PLAN_FILE, plan(
            sells=[{"ticker": "MRNA", "reason": "stop"}],
            buys=[{"ticker": "TGT", "replaces": "MRNA", "reason": "replaces MRNA"}],
            deposit_candidates=[{"ticker": "LLY", "rank": 1, "score": 99, "sector": "Health Care", "reason": "#1"}],
            fallback="SPYM"))
        with mock.patch.object(autotrade, "notify", msgs.append):
            autotrade.execute(client=self.client(ib))
        self.assertEqual(ib.pos["TGT"][0], 1)                     # 1 whole share of the planned replacement
        self.assertNotIn("LLY", ib.pos)                           # $900 stock: too expensive, skipped quietly
        self.assertFalse(any("Couldn't buy" in m for m in msgs))


class LeftoverTest(IBTraderTest):
    def test_leftover_cash_goes_to_the_sp500_fund_in_whole_shares(self):
        ib = FakeIB({"CNC": 70.0, "SPYM": 80.0, "SGOV": 100.5}, cash=250.0, holdings={"CNC": [3, 70.0]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(fallback="SPYM"))
        autotrade.execute(client=self.client(ib))
        self.assertEqual(ib.pos["SPYM"][0], 3)                   # $250 -> 3 whole shares ($240), $10 stays cash
        self.assertLess(ib.cash, 80)

    def test_sp500_not_rising_means_tbills(self):
        ib = FakeIB({"CNC": 70.0, "SPYM": 80.0, "SGOV": 100.5}, cash=250.0, holdings={"CNC": [3, 70.0]})
        autotrade.save_json(autotrade.PLAN_FILE, plan(fallback="SGOV"))
        autotrade.execute(client=self.client(ib))
        self.assertNotIn("SPYM", ib.pos)
        self.assertEqual(ib.pos["SGOV"][0], 2)
