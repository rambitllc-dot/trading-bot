import json
import os
import tempfile
import unittest
from unittest import mock

from monitor import alerts, config, notifier, run, storage
from monitor.tests.test_layer3 import MacroProvider


class ChangingProvider(MacroProvider):
    """Feed whose chain can grow (new strikes / expiries) and whose prices/IV can change."""
    def __init__(self, expiries, strikes, iv=0.6, scale=1.0, headlines=None):
        super().__init__(True, headlines)
        self.exp, self.strikes, self.iv, self.scale = expiries, strikes, iv, scale

    def expiries(self, t):
        return self.exp

    def chain(self, t, exp):
        rows = []
        for k in self.strikes:
            for kind in ("call", "put"):
                rows.append({"option_type": kind, "strike": float(k), "contract_symbol": f"{t}{exp}{kind}{k}",
                             "bid": 9.9 * self.scale, "ask": 10.1 * self.scale, "last": 10 * self.scale,
                             "iv": self.iv, "volume": 5.0, "open_interest": 50.0})
        return rows


class AlertsTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.pos = os.path.join(self.d, "pos.json")
        json.dump([{"asset_type": "option", "ticker": "NOK", "option_type": "call", "strike": 100,
                    "expiry": "2027-01-15", "entry_price": 5, "contracts": 2, "entry_date": "2026-10-01",
                    "target_price": 10, "stop_price": 2}], open(self.pos, "w"))
        MacroProvider.SPOT["NOK"] = 100.0

    def go(self, asof, provider, caller=None):
        return run.run(asof, positions_file=self.pos, provider=provider, db=os.path.join(self.d, "m.db"),
                       snap_dir=os.path.join(self.d, "s"), news_caller=caller)

    def test_diff_target_and_iv_alerts(self):
        self.go("2026-11-04", ChangingProvider(["2026-12-18", "2027-01-15"], [80, 100, 120], iv=0.5, scale=0.9))
        res = self.go("2026-11-05", ChangingProvider(["2026-12-18", "2027-01-15", "2028-01-21"],
                                                     [80, 100, 110, 120, 200], iv=0.7, scale=1.0))
        kinds = {a["kind"]: a for a in res["alerts"]}
        self.assertIn("new_expiry", kinds)
        self.assertIn("2028-01-21", kinds["new_expiry"]["message"])          # fresh LEAPS expiry
        strikes = {s["strike"] for s in kinds["new_strikes"]["detail"]}
        self.assertEqual(strikes, {110.0})                                    # 200 is outside +/-30% of 100
        self.assertEqual(kinds["target_hit"]["message"][:36], "NOK 100 calls (2027-01-15) hit your ")
        self.assertTrue(kinds["target_hit"]["is_new"])                        # wasn't hit at the prior run
        self.assertIn("iv_change", kinds)                                     # 50% -> 70%
        self.assertEqual(res["alerts"][0]["severity"], "high")                # sorted by severity
        con = storage.connect(os.path.join(self.d, "m.db"))
        self.assertGreater(con.execute("SELECT COUNT(*) FROM alerts WHERE asof='2026-11-05'").fetchone()[0], 3)
        for a in res["alerts"]:
            low = a["message"].lower()
            self.assertFalse(any(w in low for w in (" buy", " sell", "you should", "roll ")), a["message"])

    def test_stop_and_near(self):
        self.go("2026-11-05", ChangingProvider(["2027-01-15"], [100], scale=0.15))   # mark 1.5 < stop 2
        res = self.go("2026-11-06", ChangingProvider(["2027-01-15"], [100], scale=0.92))  # mark 9.2: 84% to target
        kinds = [a["kind"] for a in res["alerts"]]
        self.assertIn("target_near", kinds)
        self.assertNotIn("stop_hit", kinds)

    def test_news_alerts(self):
        import datetime as dt
        heads = [{"title": "Nokia cuts guidance", "publisher": "Wire", "summary": "",
                  "published": dt.datetime.now(dt.timezone.utc).isoformat(), "link": "https://x"}]
        caller = lambda prompt, key: (json.dumps({"summary": "Guidance cut.", "sentiment": "negative",
                                                  "drivers": ["lower 2027 guidance"],
                                                  "position_flags": [{"position_id": "NOK-100C-2027-01-15",
                                                                      "flag": "Earnings call before your expiry"}]}),
                                      {"input_tokens": 500, "output_tokens": 100})
        res = self.go("2026-11-05", ChangingProvider(["2027-01-15"], [100], headlines=heads), caller)
        msgs = {a["kind"]: a["message"] for a in res["alerts"]}
        self.assertIn("driver: lower 2027 guidance", msgs["news_flag"])
        self.assertIn("news_negative", msgs)


class NotifierTest(unittest.TestCase):
    sample = [{"severity": "high", "message": "NOK calls hit your target level"},
              {"severity": "info", "message": "new strikes"}]

    def test_off_by_default(self):
        self.assertFalse(config.NOTIFY_ENABLED)
        self.assertEqual(notifier.maybe_send(self.sample, "2026-11-05"), "off")

    def test_telegram_needs_secrets_and_respects_severity(self):
        with mock.patch.object(config, "NOTIFY_ENABLED", True), mock.patch.dict(os.environ, {}, clear=True):
            self.assertIn("skipped", notifier.maybe_send(self.sample, "2026-11-05"))
        sent = {}
        def fake_post(url, timeout, json):
            sent.update(json); return mock.Mock(ok=True)
        with mock.patch.object(config, "NOTIFY_ENABLED", True), \
             mock.patch.object(config, "NOTIFY_MIN_SEVERITY", "high"), \
             mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "1"}), \
             mock.patch("monitor.notifier.requests.post", side_effect=fake_post):
            self.assertEqual(notifier.maybe_send(self.sample, "2026-11-05"), "sent")
        self.assertIn("hit your target level", sent["text"])
        self.assertNotIn("new strikes", sent["text"])                         # below the severity floor

    def test_imessage_only_on_mac(self):
        with mock.patch.object(config, "NOTIFY_ENABLED", True), mock.patch.object(config, "NOTIFY_CHANNEL", "imessage"), \
             mock.patch("monitor.notifier.platform.system", return_value="Linux"):
            self.assertIn("only works on a Mac", notifier.maybe_send(self.sample, "2026-11-05"))


if __name__ == "__main__":
    unittest.main()
