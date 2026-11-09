import datetime as dt
import unittest
from zoneinfo import ZoneInfo

from monitor import kick

NY = ZoneInfo("America/New_York")


class KickTest(unittest.TestCase):
    def test_starts_late_run_only_when_needed(self):
        mon_1630 = dt.datetime(2026, 11, 9, 16, 30, tzinfo=NY)
        self.assertTrue(kick.needed(mon_1630, "2026-11-06", [])[0])                       # late: start it
        self.assertFalse(kick.needed(mon_1630, "2026-11-09", [])[0])                      # already done
        self.assertFalse(kick.needed(dt.datetime(2026, 11, 9, 15, 0, tzinfo=NY), "2026-11-06", [])[0])  # too early
        self.assertFalse(kick.needed(dt.datetime(2026, 11, 14, 17, 0, tzinfo=NY), "2026-11-13", [])[0])  # Saturday
        recent = [dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=20)]
        self.assertFalse(kick.needed(mon_1630, "2026-11-06", recent)[0])                  # one is already running


if __name__ == "__main__":
    unittest.main()
