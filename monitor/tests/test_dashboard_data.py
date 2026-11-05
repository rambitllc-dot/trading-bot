import os
import tempfile
import unittest

from monitor import dashboard_data, run
from monitor.tests.test_layer4 import ChangingProvider, AlertsTest


class DashboardDataTest(unittest.TestCase):
    def test_load_shapes_everything(self):
        t = AlertsTest(); t.setUp()
        t.go("2026-11-04", ChangingProvider(["2027-01-15"], [80, 90, 100, 110, 120], scale=0.9))
        t.go("2026-11-05", ChangingProvider(["2027-01-15"], [80, 90, 100, 105, 110, 120], scale=1.0))
        d = dashboard_data.load(os.path.join(t.d, "m.db"))
        self.assertEqual(d["asof"], "2026-11-05")
        self.assertEqual(d["dates"], ["2026-11-05", "2026-11-04"])
        lad = d["ladders"]["NOK-100C-2027-01-15"]
        self.assertTrue(any(r["held"] and r["strike"] == 100 for r in lad))
        self.assertTrue(any(r["new"] and r["strike"] == 105 for r in lad))    # NEW badge for a newly listed strike
        self.assertTrue(d["theta_stacked"])
        self.assertTrue(all(x["extrinsic"] >= -1e-9 for x in d["extrinsic"]))
        self.assertEqual(d["extrinsic"][-1]["extrinsic"], 0)                  # no time value left at expiry
        self.assertEqual(dashboard_data.load(os.path.join(t.d, "m.db"), "2026-11-04")["asof"], "2026-11-04")

    def test_empty_database(self):
        d = dashboard_data.load(os.path.join(tempfile.mkdtemp(), "empty.db"))
        self.assertIsNone(d["asof"])


if __name__ == "__main__":
    unittest.main()
