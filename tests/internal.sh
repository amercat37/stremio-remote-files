#!/usr/bin/env bash
set -e

# ------------------------------------------------------------
# Load env file
# Priority:
#   1) Positional arg (e.g. ./internal.sh .env_testing)
#   2) Default ../.env_testing
# ------------------------------------------------------------

ENV_FILE="../${1:-.env_testing}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ Env file not found: $ENV_FILE"
  exit 1
fi

echo "Using ENV_FILE=$ENV_FILE"

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip blank lines and comments
  [[ "$line" =~ ^[[:space:]]*$ ]] && continue
  [[ "$line" =~ ^[[:space:]]*# ]] && continue

  # Only accept KEY=VALUE
  if [[ "$line" =~ ^([A-Z_][A-Z0-9_]*)=(.*)$ ]]; then
    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    export "$key=$value"
  fi
done < "$ENV_FILE"

# ------------------------------------------------------------
# Required variables
# ------------------------------------------------------------

: "${MEDIA_BASE_URL_INTERNAL:?Missing MEDIA_BASE_URL_INTERNAL}"
: "${ADMIN_SCAN_TOKEN:?Missing ADMIN_SCAN_TOKEN}"

BASE="$MEDIA_BASE_URL_INTERNAL"

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

pass() { echo "✅ PASS: $1"; }
fail() { echo "❌ FAIL: $1 (expected $2, got $3)"; }

check() {
  name="$1"
  expected="$2"
  shift 2
  code=$(curl -k -s -o /dev/null -w "%{http_code}" "$@")
  if [[ "$code" == "$expected" ]]; then
    pass "$name"
  else
    fail "$name" "$expected" "$code"
  fi
}

# ------------------------------------------------------------
# Tests
# ------------------------------------------------------------

echo
echo "================ MANIFESTS (INTERNAL) ================"
check "Internal manifest" 200 \
  "$BASE/internal/manifest.json"

echo
echo "================ CATALOGS (INTERNAL) ================"
check "Movie catalog" 200 \
  "$BASE/internal/catalog/movie/remote-files.json"
check "Series catalog" 200 \
  "$BASE/internal/catalog/series/remote-files.json"

echo
echo "================ STREAM RESOLVERS (INTERNAL) ================"
check "Movie stream" 200 \
  "$BASE/internal/stream/movie/tt0486655.json"
check "Series stream" 200 \
  "$BASE/internal/stream/series/tt0206512:1:1.json"

echo
echo "================ MEDIA FILES (INTERNAL) ================"

check "Movie file (range)" 206 \
  -H "Range: bytes=0-1" \
  "$BASE/movies/Stardust%20(2007).mp4"

check "Series file (range)" 206 \
  -H "Range: bytes=0-1" \
  "$BASE/series/Destinos%20-%20An%20Introduction%20to%20Spanish/Season%2001/S01E01%20-%20La%20carta.mp4"

echo
echo "================ ADMIN (INTERNAL) ================"
check "Admin UI" 200 \
  "$BASE/admin"

check "Admin scan" 200 \
  -X POST "$BASE/admin/scan" \
  -H "Authorization: Bearer $ADMIN_SCAN_TOKEN"

check "Admin rebuild" 200 \
  -X POST "$BASE/admin/scan/rebuild" \
  -H "Authorization: Bearer $ADMIN_SCAN_TOKEN"

echo
echo "================ CONFIG PAGES (INTERNAL) ================"
check "Configure page" 200 \
  "$BASE/internal/configure"

echo
echo "🎉 INTERNAL TESTS COMPLETED"
