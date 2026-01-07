#!/bin/sh
set -e

if [ -z "$SCAN_CRON" ]; then
  echo "[ERROR] SCAN_CRON is not set"
  exit 1
fi

if [ -z "$ADMIN_SCAN_TOKEN" ]; then
  echo "[ERROR] ADMIN_SCAN_TOKEN is not set"
  exit 1
fi

# Write cron job
echo "$SCAN_CRON curl -fsS -X POST \
  -H \"Authorization: Bearer $ADMIN_SCAN_TOKEN\" \
  http://stremio-remote-files-api:7000/admin/scan \
  || echo \"[WARN] Scan failed\"" > /etc/crontabs/root

echo "[INFO] Scan cron scheduled: $SCAN_CRON"
echo "[INFO] Starting cron..."

# Run cron in foreground
crond -f -l 8
