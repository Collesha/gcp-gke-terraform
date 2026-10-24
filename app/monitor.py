import os
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

URLS = [
    url.strip()
    for url in os.getenv(
        "MONITOR_URLS",
        "https://collesha.xyz,https://example.com"
    ).split(",")
    if url.strip()
]
INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))
DB_PATH = os.getenv("DB_PATH", "uptime.db")


def initialize_database():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                url TEXT NOT NULL,
                status_code INTEGER,
                response_ms REAL,
                is_up INTEGER NOT NULL,
                error TEXT
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                started_at TEXT NOT NULL,
                resolved_at TEXT,
                duration_seconds REAL
        )
        """)


def check_website(url):
    start = time.monotonic()
    status_code = None
    error = None

    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "CloudReliabilityMonitor/1.0"}
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            status_code = response.status

    except urllib.error.HTTPError as exc:
        status_code = exc.code
        error = str(exc)

    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        error = str(exc)

    response_ms = round((time.monotonic() - start) * 1000, 2)
    is_up = int(status_code is not None and 200 <= status_code < 400)

    timestamp = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            INSERT INTO checks
            (timestamp, url, status_code, response_ms, is_up, error)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            timestamp,
            url,
            status_code,
            response_ms,
            is_up,
            error
        ))
        open_incident = connection.execute("""
            SELECT id, started_at
            FROM incidents
            WHERE url = ? AND resolved_at IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (url,)).fetchone()

        if not is_up and open_incident is None:
            connection.execute("""
                INSERT INTO incidents (url, started_at)
                VALUES (?, ?)
            """, (url, timestamp))
            print(f"INCIDENT OPENED: {url}", flush=True)

        elif is_up and open_incident is not None:
            started_at = datetime.fromisoformat(open_incident[1])
            resolved_at = datetime.fromisoformat(timestamp)

            duration = (
                resolved_at - started_at
            ).total_seconds()

            connection.execute("""
                UPDATE incidents
                SET resolved_at = ?, duration_seconds = ?
                WHERE id = ?
            """, (
                timestamp,
                duration,
                open_incident[0]
            ))

            print(
                f"INCIDENT RESOLVED: {url} "
                f"after {duration:.1f} seconds",
                flush=True
            )

    result = "UP" if is_up else "DOWN"

    print(
        f"[{timestamp}] {result} | "
        f"HTTP {status_code} | "
        f"{response_ms} ms | {url}"
        + (f" | {error}" if error else ""),
        flush=True
    )
    return {
        "url": url,
        "status_code": status_code,
        "response_ms": response_ms,
        "is_up": is_up,
        "error": error
    }


def main():
    if INTERVAL <= 0:
        raise ValueError("CHECK_INTERVAL must be positive")

    initialize_database()

    print(f"Monitoring {len(URLS)} websites every {INTERVAL} seconds...")

    try:
        while True:
            for url in URLS:
                check_website(url)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    main()
