import unittest
from datetime import datetime, timedelta, timezone

from app.dashboard import get_monitoring_status


class TestDashboardStatus(unittest.TestCase):

    def setUp(self):
        self.now = datetime.now(timezone.utc)

    def test_recent_successful_check(self):
        timestamp = (self.now - timedelta(seconds=10)).isoformat()

        result = get_monitoring_status(
            True,
            timestamp,
            now=self.now
        )

        self.assertEqual(result, "UP")

    def test_recent_failed_check(self):
        timestamp = (self.now - timedelta(seconds=10)).isoformat()

        result = get_monitoring_status(
            False,
            timestamp,
            now=self.now
        )

        self.assertEqual(result, "DOWN")

    def test_stale_successful_check(self):
        timestamp = (self.now - timedelta(seconds=120)).isoformat()

        result = get_monitoring_status(
            True,
            timestamp,
            now=self.now
        )

        self.assertEqual(result, "STALE")

    def test_stale_failed_check(self):
        timestamp = (self.now - timedelta(seconds=120)).isoformat()

        result = get_monitoring_status(
            False,
            timestamp,
            now=self.now
        )

        self.assertEqual(result, "STALE")


if __name__ == "__main__":
    unittest.main()