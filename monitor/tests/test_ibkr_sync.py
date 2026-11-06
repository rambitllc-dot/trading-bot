import json
import os
import tempfile
import unittest

from monitor import ibkr_sync, positions

XML = """<FlexQueryResponse queryName="Monitor" type="AF"><FlexStatements count="1">
<FlexStatement accountId="U123" fromDate="20261106" toDate="20261106" whenGenerated="20261107;020000">
<OpenPositions>
 <OpenPosition assetCategory="STK" symbol="CNC" position="4.9002" multiplier="1" costBasisPrice="70.59"
   costBasisMoney="345.905" levelOfDetail="SUMMARY"/>
 <OpenPosition assetCategory="STK" symbol="TXN" position="0.6" multiplier="1" costBasisPrice="273.6"
   costBasisMoney="164.16" levelOfDetail="SUMMARY"/>
 <OpenPosition assetCategory="OPT" symbol="NVDA  270115C00200000" underlyingSymbol="NVDA" putCall="C"
   strike="200" expiry="20270115" position="2" multiplier="100" costBasisMoney="2840" levelOfDetail="SUMMARY"/>
</OpenPositions>
<CashReport><CashReportCurrency currency="BASE_SUMMARY" endingCash="5.21"/></CashReport>
</FlexStatement></FlexStatements></FlexQueryResponse>"""


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(tempfile.mkdtemp(), "positions.json")

    def write(self, book):
        json.dump(book, open(self.path, "w"))

    def test_parse(self):
        date, pos, cash = ibkr_sync.parse(XML)
        self.assertEqual(date, "2026-11-06")
        self.assertEqual(cash, 5.21)
        opt = [p for p in pos if p["asset_type"] == "option"][0]
        self.assertEqual((opt["ticker"], opt["option_type"], opt["strike"], opt["expiry"]),
                         ("NVDA", "call", 200.0, "2027-01-15"))
        self.assertAlmostEqual(opt["entry_price"], 14.20)           # 2840 / (2 x 100) per share

    def test_sync_keeps_your_levels_and_loads(self):
        self.write([{"asset_type": "shares", "ticker": "CNC", "contracts": 4.9, "entry_price": 70.59,
                     "entry_date": "2026-11-06", "stop_price": 60, "target_price": 90},
                    {"asset_type": "shares", "ticker": "MRK", "contracts": 1, "entry_price": 147.71,
                     "entry_date": "2026-11-06"}])
        status = ibkr_sync.sync(self.path, fetcher=lambda t, q: XML)
        self.assertIn("3 position(s) as of 2026-11-06", status)
        book = positions.load(self.path)
        cnc = [p for p in book if p["ticker"] == "CNC"][0]
        self.assertEqual((cnc["stop_price"], cnc["target_price"]), (60, 90))   # your levels kept
        self.assertNotIn("MRK", [p["ticker"] for p in book])                   # sold in IB -> removed
        self.assertEqual([p for p in book if p["asset_type"] == "cash"][0]["contracts"], 5.21)

    def test_waits_for_newer_trades(self):
        self.write([{"asset_type": "shares", "ticker": "XYZ", "contracts": 1, "entry_price": 10,
                     "entry_date": "2026-11-09"}])
        status = ibkr_sync.sync(self.path, fetcher=lambda t, q: XML)
        self.assertIn("waiting", status)
        self.assertEqual(json.load(open(self.path))[0]["ticker"], "XYZ")      # untouched

    def test_off_and_failure_are_harmless(self):
        os.environ.pop("IBKR_FLEX_TOKEN", None)
        self.assertIn("off", ibkr_sync.sync(self.path))
        self.write([{"asset_type": "shares", "ticker": "SPY", "contracts": 1, "entry_price": 700}])
        def boom(t, q):
            raise RuntimeError("network down")
        self.assertIn("kept positions.json", ibkr_sync.sync(self.path, fetcher=boom))
        self.assertEqual(json.load(open(self.path))[0]["ticker"], "SPY")


if __name__ == "__main__":
    unittest.main()
