import json
import os
import tempfile
import unittest
from unittest import mock

from monitor import config, scanner, storage


def bars(closes, vols=None, start_vol=1e6):
    vols = vols or [start_vol] * len(closes)
    return [(f"d{i:03d}", c, c * 1.001, v) for i, (c, v) in enumerate(zip(closes, vols))]


def market():
    n = 300
    up = [100 * 1.004 ** i for i in range(n)]                      # steady uptrend, ends at a new high
    flat = [100.0 + (i % 5) * 0.1 for i in range(n)]
    pull = up[:-3] + [up[-4] * 0.97, up[-4] * 0.94, up[-4] * 0.91]  # sharp 3-day drop, still above 200-day avg
    spike = flat[:-1] + [flat[-1] * 1.08]
    return {"UPCO": bars(up), "FLAT": bars(flat), "PULL": bars(pull),
            "SPKE": bars(spike, [1e6] * (n - 1) + [5e6]), "WATCH": bars([120.0] * (n - 1) + [99.0])}


class ScannerTest(unittest.TestCase):
    def test_screens(self):
        found, m = scanner.screens(market())
        names = {k: [x["ticker"] for x in v] for k, v in found.items()}
        self.assertEqual(names["momentum_leaders"][0], "UPCO")
        self.assertIn("PULL", names["pullback_in_uptrend"])
        self.assertIn("UPCO", names["new_52w_high"])
        self.assertEqual(names["unusual_volume"], ["SPKE"])
        self.assertNotIn("FLAT", names["new_52w_high"])

    def test_watchlist_levels(self):
        _, m = scanner.screens(market())
        wl = [{"ticker": "WATCH", "buy_below": 100.0, "note": ""}, {"ticker": "FLAT", "buy_below": 98.0, "note": ""},
              {"ticker": "UPCO", "buy_below": None, "note": ""}, {"ticker": "ANT", "buy_below": 50.0, "note": ""}]
        rows, alerts = scanner.watch(wl, m)
        by = {r["ticker"]: r for r in rows}
        self.assertEqual(by["WATCH"]["action"], "BUY")               # 99 <= your 100 level
        self.assertEqual(by["FLAT"]["action"], "REVIEW")             # within 5% above 98
        self.assertEqual(by["UPCO"]["action"], "WAIT")               # no level set
        self.assertIsNone(by["ANT"]["action"])                       # not trading yet
        self.assertEqual([a["kind"] for a in alerts], ["watch_buy", "watch_near"])

    def test_run_stores_and_summarizes(self):
        class P:
            def bulk(self, tickers): return market()
            def news(self, t): return []
        d = tempfile.mkdtemp()
        wl = os.path.join(d, "w.json")
        json.dump([{"ticker": "WATCH", "buy_below": 100}], open(wl, "w"))
        con = storage.connect(os.path.join(d, "m.db"))
        with mock.patch.object(config, "WATCHLIST_FILE", wl), mock.patch.object(scanner, "universe", lambda: list(market())):
            res = scanner.run(con, "2026-11-05", P())
        self.assertEqual(res["scanned"], 5)
        self.assertGreater(con.execute("SELECT COUNT(*) FROM scan_results").fetchone()[0], 3)
        self.assertEqual(con.execute("SELECT action FROM watchlist WHERE ticker='WATCH'").fetchone()[0], "BUY")
        self.assertTrue(res["news"])                                  # top candidates got a (no-headline) summary


if __name__ == "__main__":
    unittest.main()
