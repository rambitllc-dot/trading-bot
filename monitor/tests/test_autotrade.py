import os
import tempfile
import unittest
from unittest import mock

from monitor import autotrade, config
from monitor.tests.test_rotation import market


class FakeAlpaca:
    """A pretend broker: fills market orders instantly at the given prices."""
    def __init__(self, cash=10000.0, prices=None, is_open=True, today="2026-11-09"):
        self.cash, self.prices, self.is_open, self.today = cash, prices or {}, is_open, today
        self.pos, self.orders, self.n = {}, {}, 0  # symbol -> [qty, avg]

    def _fill(self, sym, qty, side):
        self.n += 1
        o = {"id": str(self.n), "status": "filled", "filled_avg_price": str(self.prices[sym]), "symbol": sym, "side": side}
        self.orders[o["id"]] = o
        return o

    def clock(self):
        return {"is_open": self.is_open, "timestamp": f"{self.today}T15:00:00-05:00"}

    def account(self):
        eq = self.cash + sum(q * self.prices[s] for s, (q, _) in self.pos.items())
        return {"equity": str(eq), "cash": str(self.cash)}

    def positions(self):
        return [{"symbol": s, "qty": str(q), "avg_entry_price": str(a), "current_price": str(self.prices[s]),
                 "market_value": str(q * self.prices[s]), "cost_basis": str(q * a)} for s, (q, a) in self.pos.items()]

    def buy(self, sym, dollars):
        if sym not in self.prices:
            raise autotrade.AlpacaError("asset not fractionable")
        q = dollars / self.prices[sym]
        self.cash -= dollars
        self.pos[sym] = [q, self.prices[sym]]
        return self._fill(sym, q, "buy")

    def close(self, sym):
        q, _ = self.pos.pop(sym)
        self.cash += q * self.prices[sym]
        return self._fill(sym, q, "sell")

    def order(self, oid):
        return self.orders[oid]


class AutopilotTest(unittest.TestCase):
    def setUp(self):
        d = tempfile.mkdtemp()
        self.patches = [mock.patch.object(autotrade, n, os.path.join(d, f)) for n, f in
                        (("PLAN_FILE", "plan.json"), ("STATE_FILE", "state.json"), ("LOG_FILE", "log.csv"),
                         ("SWITCH_FILE", "switch.json"))] + \
                       [mock.patch.object(config, "AUTO_DIR", d), mock.patch.object(autotrade, "notify", lambda t: None)]
        for p in self.patches:
            p.start()
        self.db = os.path.join(d, "auto.db")
        self.m = market()
        self.prices = {t: b[-1][1] for t, b in self.m.items()}

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_plan_then_buy_five_equal_weight_once(self):
        fake = FakeAlpaca(prices=self.prices)
        res = autotrade.plan("2026-11-06", self.m, client=fake, db=self.db)
        buys = res["plan"]["buys"]
        self.assertTrue(1 <= len(buys) <= config.AUTO_HOLDINGS)
        self.assertEqual(buys[0]["ticker"], "WINR")                       # strongest first
        self.assertTrue(all(b["score"] >= config.ROTATION_MIN_SCORE for b in buys))
        autotrade.execute(client=fake)
        self.assertEqual(set(fake.pos), {b["ticker"] for b in buys})
        vals = {s: q * a for s, (q, a) in fake.pos.items()}   # sized by how jumpy each stock is, max 25% each
        self.assertTrue(all(v <= 10000 * config.AUTO_MAX_ORDER_PCT / 100 + 1 for v in vals.values()))
        self.assertGreater(min(vals.values()), 10000 / config.AUTO_HOLDINGS * 0.5)     # nobody gets only leftovers
        self.assertAlmostEqual(sum(vals.values()), 10000, delta=5)                       # all the money invested
        before = dict(fake.pos)
        autotrade.execute(client=fake)                                    # same plan again -> no new trades
        self.assertEqual(fake.pos.keys(), before.keys())
        self.assertTrue(os.path.exists(autotrade.LOG_FILE))

    def test_stop_hit_sells_and_buys_replacement_but_not_same_day(self):
        fake = FakeAlpaca(prices=self.prices, today="2026-11-09")
        autotrade.plan("2026-11-06", self.m, client=fake, db=self.db)
        autotrade.execute(client=fake)
        first = next(iter(fake.pos))
        fake.prices[first] *= 0.90                                        # drops 10% the same day
        autotrade.execute(client=fake)
        self.assertIn(first, fake.pos)                                    # bought today: no same-day sale
        fake.today = "2026-11-10"
        autotrade.execute(client=fake)
        self.assertNotIn(first, fake.pos)                                 # next day: 6% stop -> sold
        self.assertEqual(len(fake.pos), len(autotrade.load_json(autotrade.PLAN_FILE, {})["buys"]))  # replaced
        self.assertIn(first, autotrade.load_state()["sold"])

    def test_paused_closed_and_off(self):
        fake = FakeAlpaca(prices=self.prices)
        autotrade.plan("2026-11-06", self.m, client=fake, db=self.db)
        autotrade.save_json(autotrade.SWITCH_FILE, {"paused": True})
        self.assertIn("paused", autotrade.execute(client=fake))
        autotrade.save_json(autotrade.SWITCH_FILE, {"paused": False})
        self.assertEqual(autotrade.execute(client=FakeAlpaca(prices=self.prices, is_open=False)), "market closed")
        self.assertEqual(fake.pos, {})
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIn("off", autotrade.plan("2026-11-06", self.m, db=self.db)["status"])

    def test_stale_plan_is_not_traded(self):
        fake = FakeAlpaca(prices=self.prices, today="2026-11-20")
        autotrade.plan("2026-11-06", self.m, client=fake, db=self.db)
        self.assertIn("too old", autotrade.execute(client=fake))
        self.assertEqual(fake.pos, {})


if __name__ == "__main__":
    unittest.main()
