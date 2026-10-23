import os
import sqlite3
from flask import Flask, render_template_string

app = Flask(__name__)

DB_PATH = os.getenv("DB_PATH", "uptime.db")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Cloud Service Reliability Monitor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f6f9;
            color: #202938;
            margin: 0;
            padding: 40px;
        }
        .container {
            max-width: 1000px;
            margin: auto;
        }
        h1 { margin-bottom: 5px; }
        .subtitle { color: #667085; margin-bottom: 30px; }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card, .table-container {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .label { color: #667085; font-size: 14px; }
        .value {
            font-size: 26px;
            font-weight: bold;
            margin-top: 10px;
        }
        .up { color: #16803c; }
        .down { color: #c62828; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        th { color: #667085; }
        .table-container { overflow-x: auto; }
    </style>
</head>
<body>
<div class="container">
    <h1>Cloud Service Reliability Monitor</h1>
    <p class="subtitle">Website availability and performance monitoring</p>

    <div class="cards">
    {% for site in sites %}
    <div class="card">
        <div class="label">{{ site.url }}</div>

        <div class="value {{ 'up' if site.latest_status else 'down' }}">
            {{ 'Operational' if site.latest_status else 'Down' }}
        </div>

        <p><strong>Availability:</strong> {{ site.uptime }}%</p>

        <p>
            <strong>Average Response:</strong>
            {{ site.average_response }} ms
        </p>

        <p>
            <strong>Total Checks:</strong>
            {{ site.total_checks }}
        </p>

        <p>
            <strong>Last Checked:</strong>
            {{ site.last_checked }}
        </p>
    </div>
    {% endfor %}
</div>

    <div class="table-container">
        <h2>Recent Monitoring History</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp (UTC)</th>
                    <th>Website</th>
                    <th>HTTP Status</th>
                    <th>Response Time</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for row in rows %}
                <tr>
                    <td>{{ row[0] }}</td>
                    <td>{{ row[1] }}</td>
                    <td>{{ row[2] if row[2] is not none else 'N/A' }}</td>
                    <td>{{ row[3] }} ms</td>
                    <td class="{{ 'up' if row[4] else 'down' }}">
                        {{ 'UP' if row[4] else 'DOWN' }}
                    </td>
                </tr>
                {% else %}
                <tr><td colspan="5">No monitoring data yet.</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    with sqlite3.connect(DB_PATH) as connection:

        websites = connection.execute("""
            SELECT
                url,
                COUNT(*) AS total_checks,
                SUM(is_up) AS successful_checks,
                ROUND(AVG(response_ms), 2) AS average_response
            FROM checks
            GROUP BY url
            ORDER BY url
        """).fetchall()

        latest_checks = connection.execute("""
            SELECT
                c.url,
                c.timestamp,
                c.status_code,
                c.response_ms,
                c.is_up
            FROM checks c
            WHERE c.id = (
                SELECT MAX(c2.id)
                FROM checks c2
                WHERE c2.url = c.url
            )
        """).fetchall()

        history = connection.execute("""
            SELECT timestamp, url, status_code, response_ms, is_up
            FROM checks
            ORDER BY id DESC
            LIMIT 20
        """).fetchall()

    latest_by_url = {
        row[0]: row for row in latest_checks
    }

    monitored_sites = []

    for url, total, successful, avg_response in websites:
        latest = latest_by_url[url]

        monitored_sites.append({
            "url": url,
            "total_checks": total,
            "uptime": round((successful / total) * 100, 2),
            "average_response": avg_response,
            "latest_status": bool(latest[4]),
            "last_checked": latest[1]
        })

    return render_template_string(
        HTML,
        sites=monitored_sites,
        rows=history
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
