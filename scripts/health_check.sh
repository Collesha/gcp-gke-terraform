#!/usr/bin/env bash

set -u

URL="http://127.0.0.1:5050"
LOG_FILE="health_check.log"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 5 "$URL")

if [ "$HTTP_CODE" = "200" ]; then
    echo "$TIMESTAMP | HEALTHY | HTTP $HTTP_CODE" | tee -a "$LOG_FILE"
else
    echo "$TIMESTAMP | UNHEALTHY | HTTP $HTTP_CODE" | tee -a "$LOG_FILE"

    echo "---- Diagnostic information ----" | tee -a "$LOG_FILE"

    echo "Processes listening on port 5050:" | tee -a "$LOG_FILE"

    lsof -nP -iTCP:5050 -sTCP:LISTEN | tee -a "$LOG_FILE" || true
fi