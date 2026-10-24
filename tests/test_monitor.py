import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "app")
)

import monitor


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class TestMonitor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(
            self.temp_dir.name,
            "test_uptime.db"
        )

        self.db_patch = patch.object(
            monitor,
            "DB_PATH",
            self.db_path
        )
        self.db_patch.start()

        monitor.initialize_database()

    def tearDown(self):
        self.db_patch.stop()
        self.temp_dir.cleanup()

    @patch("monitor.urllib.request.urlopen")
    def test_successful_check(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse()

        result = monitor.check_website(
            "https://example.com"
        )

        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["is_up"], 1)

    @patch("monitor.urllib.request.urlopen")
    def test_failed_check(self, mock_urlopen):
        mock_urlopen.side_effect = URLError(
            "Connection refused"
        )

        result = monitor.check_website(
            "https://example.com"
        )

        self.assertIsNone(result["status_code"])
        self.assertEqual(result["is_up"], 0)

    @patch("monitor.urllib.request.urlopen")
    def test_incident_recovery(self, mock_urlopen):
        mock_urlopen.side_effect = [
            URLError("Connection refused"),
            FakeResponse()
        ]

        monitor.check_website("https://example.com")
        monitor.check_website("https://example.com")

        import sqlite3

        with sqlite3.connect(self.db_path) as connection:
            incident = connection.execute("""
                SELECT started_at, resolved_at
                FROM incidents
                LIMIT 1
            """).fetchone()

        self.assertIsNotNone(incident)
        self.assertIsNotNone(incident[0])
        self.assertIsNotNone(incident[1])


if __name__ == "__main__":
    unittest.main()