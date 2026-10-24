import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from app import dashboard as dashboard_module

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

        
class TestDashboardIntegration(unittest.TestCase):

    def test_dashboard_displays_stale_status(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_uptime.db")

            with sqlite3.connect(db_path) as connection:
                connection.execute("""
                    CREATE TABLE checks (
                        id INTEGER PRIMARY KEY,
                        timestamp TEXT,
                        url TEXT,
                        status_code INTEGER,
                        response_ms REAL,
                        is_up INTEGER
                    )
                """)

                connection.execute("""
                    CREATE TABLE incidents (
                        id INTEGER PRIMARY KEY,
                        url TEXT,
                        started_at TEXT,
                        resolved_at TEXT,
                        duration_seconds REAL
                    )
                """)

                connection.execute("""
                    INSERT INTO checks (
                        timestamp, url, status_code,
                        response_ms, is_up
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    "2026-01-01T12:00:00+00:00",
                    "https://example.com",
                    200,
                    120.5,
                    1
                ))

                connection.commit()

            with patch.object(dashboard_module, "DB_PATH", db_path):
                client = dashboard_module.app.test_client()
                response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Stale", response.data)

if __name__ == "__main__":
    unittest.main()