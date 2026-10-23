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

    result = "UP" if is_up else "DOWN"

    print(
        f"[{timestamp}] {result} | "
        f"HTTP {status_code} | "
        f"{response_ms} ms | {url}"
        + (f" | {error}" if error else ""),
        flush=True
    )


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
