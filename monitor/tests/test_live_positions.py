import datetime as dt
import json
import os
import tempfile
import unittest
from unittest import mock

from monitor import config, ibkr_sync, live_positions
from monitor.tests.test_ib_trader import FakeIB


class LivePositionsTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "positions.json")
        json.dump([{"asset_type": "shares", "ticker": "CNC", "contracts": 4.9, "entry_price": 70.59,
                    "entry_date": "2026-11-06", "stop_price": 66.0, "target_price": None},
                   {"asset_type": "shares", "ticker": "MRNA", "contracts": 0.6, "entry_price": 260.21,
                    "entry_date": "2026-11-06"},
                   {"asset_type": "cash", "amount": 5.21}], open(self.path, "w"))
        self.p = [mock.patch.object(config, "POSITIONS_FILE", self.path),
                  mock.patch.object(live_positions, "META_FILE", os.path.join(self.d, "positions_meta.json"))]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_app_trade_is_picked_up_and_pushed_once(self):
        ib = FakeIB({"CNC": 70.0, "TGT": 161.0}, cash=8.67,
                    holdings={"CNC": [4.9, 70.59], "TGT": [0.9, 161.48]})          # MRNA sold, TGT bought in the app
        ib.cash = 8.67
        pushed = []
        now = dt.datetime(2026, 11, 11, 10, 0)
        with mock.patch.object(live_positions, "save_and_push",
                               side_effect=lambda book, n: (pushed.append(book) or json.dump(book, open(self.path, "w"))
                                                            or (True, "pushed"))):
            msg = live_positions.sync(ib, now, {})
            again = live_positions.sync(ib, now, {})
        self.assertIn("TGT 0.9", msg)
        self.assertIsNone(again)                                            # unchanged: no second push
        book = {p.get("ticker"): p for p in pushed[0]}
        self.assertNotIn("MRNA", book)
        self.assertEqual(book["TGT"]["entry_date"], "2026-11-11")         # new: bought today
        self.assertEqual(book["CNC"]["entry_date"], "2026-11-06")         # kept
        self.assertEqual(book["CNC"]["stop_price"], 66.0)                  # your own level kept

    def test_push_failure_warns_once_a_day(self):
        ib = FakeIB({"CNC": 70.0}, cash=100.0, holdings={"CNC": [4.9, 70.59]})
        state, now = {}, dt.datetime(2026, 11, 11, 10, 0)
        with mock.patch.object(live_positions, "save_and_push", return_value=(False, "auth failed")):
            self.assertTrue(live_positions.sync(ib, now, state).startswith("WARN"))
            self.assertIsNone(live_positions.sync(ib, now, state))

    def test_evening_report_does_not_overwrite_newer_live_holdings(self):
        json.dump({"date": "2026-11-11"}, open(os.path.join(self.d, "positions_meta.json"), "w"))
        xml = ('<FlexQueryResponse><FlexStatements><FlexStatement toDate="20261110"><OpenPositions>'
               '<OpenPosition assetCategory="STK" symbol="MRNA" position="0.6" multiplier="1" costBasisMoney="156" '
               'levelOfDetail="SUMMARY"/></OpenPositions></FlexStatement></FlexStatements></FlexQueryResponse>')
        msg = ibkr_sync.sync(self.path, fetcher=lambda t, q: xml)
        self.assertIn("live from the Mac", msg)
        self.assertIn("MRNA", json.dumps(json.load(open(self.path))))     # untouched (still the old file here)


if __name__ == "__main__":
    unittest.main()
