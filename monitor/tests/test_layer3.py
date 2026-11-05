import datetime as dt
import json
import os
import tempfile
import unittest

from monitor import config, macro, news, positions, run, storage
from monitor.tests.test_layer1 import FakeProvider


def series(values, start="2025-01-01"):
    d0 = dt.date.fromisoformat(start)
    return [((d0 + dt.timedelta(days=i)).isoformat(), v) for i, v in enumerate(values)]


def market(calm=True):
    n = 300
    vix = [25] * (n - 1) + ([13] if calm else [38])
    vix3m = [22] * (n - 1) + ([17] if calm else [30])
    up = [100 + i * 0.1 for i in range(n)]
    down = [130 - i * 0.1 for i in range(n)]
    c = {"^VIX": series(vix), "^VIX3M": series(vix3m),
         "HYG": series(up if calm else down), "TLT": series([90] * n)}
    for t in config.BREADTH_ETFS:
        c[t] = series(up if calm else down)
    return c


class MacroProvider(FakeProvider):
    def __init__(self, calm=True, headlines=None):
        self.c, self.h = market(calm), headlines or []

    def closes(self, t):
        return self.c[t]

    def news(self, t):
        return self.h


class MacroTest(unittest.TestCase):
    def test_deterministic_and_ordered(self):
        a, b = macro.score(market(True)), macro.score(market(True))
        self.assertEqual(a, b)                                  # same data in, same score out
        self.assertEqual(a["label"], "Calm")
        stressed = macro.score(market(False))
        self.assertEqual(stressed["label"], "Stressed")
        self.assertLess(stressed["score"], a["score"])

    def test_component_rules(self):
        self.assertEqual(macro.line(12, 12, 40), 100)
        self.assertEqual(macro.line(40, 12, 40), 0)
        self.assertEqual(macro.line(50, 12, 40), 0)            # clipped
        s, _ = macro.components(market(True))
        self.assertEqual(s["breadth"], 100)                     # every sector ETF above its 200-day average

    def test_weights_must_sum_to_one(self):
        with self.assertRaises(ValueError):
            macro.check_weights({"vix_level": 0.5, "credit": 0.4})

    def test_missing_component_reweights(self):
        c = market(True)
        del c["^VIX3M"]
        r = macro.score(c)
        self.assertIn("term_structure", r["missing"])
        self.assertIsNotNone(r["score"])


class NewsTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.db, self.snaps = os.path.join(self.d, "m.db"), os.path.join(self.d, "s")
        now = dt.datetime.now(dt.timezone.utc)
        self.heads = [{"title": "SpaceX wins NASA contract", "publisher": "Wire", "summary": "",
                       "published": (now - dt.timedelta(hours=5)).isoformat(), "link": "https://x"},
                      {"title": "Old story", "publisher": "Wire", "summary": "",
                       "published": (now - dt.timedelta(days=10)).isoformat(), "link": "https://y"}]
        self.calls = []

    def fake_claude(self, prompt, key):
        self.calls.append(prompt)
        return (json.dumps({"summary": "SpaceX won a NASA contract.", "sentiment": "positive",
                            "drivers": ["NASA contract"],
                            "position_flags": [{"position_id": "SPCX-150C-2027-01-15", "flag": "Contract news"}]}),
                {"input_tokens": 800, "output_tokens": 150})

    def go(self, asof="2026-11-05"):
        return run.run(asof, provider=MacroProvider(True, self.heads), db=self.db, snap_dir=self.snaps,
                       news_caller=self.fake_claude)

    def test_analysis_window_cache_and_cost(self):
        r1 = self.go()
        spcx = [n for n in r1["news"] if n["ticker"] == "SPCX"][0]
        self.assertEqual(spcx["sentiment"], "positive")
        self.assertEqual(len(spcx["headlines"]), 1)             # 10-day-old story is outside the 3-day window
        self.assertAlmostEqual(spcx["cost_usd"], (800 * 0.10 + 150 * 0.50) / 1e6)
        nvda = [n for n in r1["news"] if n["ticker"] == "NVDA"][0]
        self.assertEqual(nvda["position_flags"], [])           # a SpaceX flag never lands on Nvidia
        n_calls = len(self.calls)
        r2 = self.go()                                         # same day again
        self.assertEqual(len(self.calls), n_calls)             # served from cache, not billed again
        self.assertTrue(all(n.get("cached") for n in r2["news"]))
        self.go("2026-11-06")                                  # a new day calls again
        self.assertEqual(len(self.calls), n_calls * 2)
        con = storage.connect(self.db)
        self.assertEqual(con.execute("SELECT COUNT(*) FROM macro").fetchone()[0], 2)

    def test_prompt_has_positions_and_forbids_advice(self):
        self.go()
        p = [c for c in self.calls if "Ticker: SPCX" in c][0]
        self.assertIn("strike 150", p)
        self.assertIn("No buy/sell/hold language", p)
        self.assertIn("Never recommend buying, selling", news.SYSTEM)

    def test_no_headlines_means_no_call(self):
        self.heads = []
        r = self.go()
        self.assertEqual(self.calls, [])
        self.assertTrue(all("No headlines" in n["summary"] for n in r["news"]))

    def test_off_without_api_key(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        book = positions.load()
        con = storage.connect(self.db)
        out = news.run(con, "2026-11-05", book, MacroProvider(True, self.heads))
        self.assertTrue(all(n["status"].startswith("off") for n in out))


if __name__ == "__main__":
    unittest.main()
