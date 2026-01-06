#!/usr/bin/env bash
set -e

# ------------------------------------------------------------
# Load env file
# Priority:
#   1) Positional arg (e.g. ./external.sh .env)
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

: "${MEDIA_BASE_URL_EXTERNAL:?Missing MEDIA_BASE_URL_EXTERNAL}"
: "${STREAM_TOKENS:?Missing STREAM_TOKENS}"
: "${ADMIN_SCAN_TOKEN:?Missing ADMIN_SCAN_TOKEN}"

BASE="$MEDIA_BASE_URL_EXTERNAL"
STREAM_TOKEN="$(echo "$STREAM_TOKENS" | awk '{print $1}')"
BAD_TOKEN="invalid-token"

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
echo "================ MANIFESTS (EXTERNAL) ================"
check "External manifest" 200 \
  "$BASE/external/manifest.json"

echo
echo "================ CATALOGS (EXTERNAL) ================"
check "Movie catalog (good token)" 200 \
  "$BASE/external/catalog/movie/remote-files.json?token=$STREAM_TOKEN"
check "Movie catalog (bad token)" 200 \
  "$BASE/external/catalog/movie/remote-files.json?token=$BAD_TOKEN"
check "Movie catalog (no token)" 200 \
  "$BASE/external/catalog/movie/remote-files.json"

check "Series catalog (good token)" 200 \
  "$BASE/external/catalog/series/remote-files.json?token=$STREAM_TOKEN"
check "Series catalog (bad token)" 200 \
  "$BASE/external/catalog/series/remote-files.json?token=$BAD_TOKEN"
check "Series catalog (no token)" 200 \
  "$BASE/external/catalog/series/remote-files.json"

echo
echo "================ STREAM RESOLVERS (EXTERNAL) ================"
check "Movie stream (good token)" 200 \
  "$BASE/external/stream/movie/tt0486655.json?token=$STREAM_TOKEN"
check "Movie stream (bad token)" 200 \
  "$BASE/external/stream/movie/tt0486655.json?token=$BAD_TOKEN"
check "Movie stream (no token)" 200 \
  "$BASE/external/stream/movie/tt0486655.json"

check "Series stream (good token)" 200 \
  "$BASE/external/stream/series/tt0206512:1:1.json?token=$STREAM_TOKEN"
check "Series stream (bad token)" 200 \
  "$BASE/external/stream/series/tt0206512:1:1.json?token=$BAD_TOKEN"
check "Series stream (no token)" 200 \
  "$BASE/external/stream/series/tt0206512:1:1.json"

echo
echo "================ MEDIA FILES (EXTERNAL) ================"

check "Movie file (good token, range)" 206 \
  -H "Authorization: Bearer $STREAM_TOKEN" \
  -H "Range: bytes=0-1" \
  "$BASE/movies/Stardust%20(2007).mp4"

check "Movie file (bad token)" 401 \
  -H "Authorization: Bearer $BAD_TOKEN" \
  -H "Range: bytes=0-1" \
  "$BASE/movies/Stardust%20(2007).mp4"

check "Movie file (no token)" 401 \
  -H "Range: bytes=0-1" \
  "$BASE/movies/Stardust%20(2007).mp4"

check "Series file (good token, range)" 206 \
  -H "Authorization: Bearer $STREAM_TOKEN" \
  -H "Range: bytes=0-1" \
  "$BASE/series/Destinos%20-%20An%20Introduction%20to%20Spanish/Season%2001/S01E01%20-%20La%20carta.mp4"

check "Series file (bad token)" 401 \
  -H "Authorization: Bearer $BAD_TOKEN" \
  -H "Range: bytes=0-1" \
  "$BASE/series/Destinos%20-%20An%20Introduction%20to%20Spanish/Season%2001/S01E01%20-%20La%20carta.mp4"

check "Series file (no token)" 401 \
  -H "Range: bytes=0-1" \
  "$BASE/series/Destinos%20-%20An%20Introduction%20to%20Spanish/Season%2001/S01E01%20-%20La%20carta.mp4"

echo
echo "================ ADMIN (EXTERNAL) ================"
check "Admin UI" 200 \
  "$BASE/admin"

check "Admin scan (no token)" 401 \
  -X POST "$BASE/admin/scan"

check "Admin scan (bad token)" 403 \
  -X POST "$BASE/admin/scan" \
  -H "Authorization: Bearer $BAD_TOKEN"

check "Admin scan (good token)" 200 \
  -X POST "$BASE/admin/scan" \
  -H "Authorization: Bearer $ADMIN_SCAN_TOKEN"

echo
echo "================ CONFIG PAGES (EXTERNAL) ================"
check "Configure page" 200 \
  "$BASE/external/configure"

echo
echo "🎉 EXTERNAL TESTS COMPLETED"
