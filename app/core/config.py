"""
Application configuration.

This module centralizes environment-based configuration for the
Stremio Remote Files addon, including database paths, media base URLs,
and access tokens.
"""

import os

# SQLite database location (mounted volume)
DB_PATH = "/data/library.db"

# Base URLs for serving media
MEDIA_BASE_URL_INTERNAL = os.getenv("MEDIA_BASE_URL_INTERNAL")
MEDIA_BASE_URL_EXTERNAL = os.getenv("MEDIA_BASE_URL_EXTERNAL")

# These must be provided at startup; fail fast if missing
if not MEDIA_BASE_URL_INTERNAL or not MEDIA_BASE_URL_EXTERNAL:
    raise RuntimeError(
        "MEDIA_BASE_URL_INTERNAL and MEDIA_BASE_URL_EXTERNAL must be set"
    )

# Stream provider display names shown in Stremio
STREAM_PROVIDER_NAME_INTERNAL = os.getenv(
    "STREAM_PROVIDER_NAME_INTERNAL",
    "Remote Files (Internal)",
)

STREAM_PROVIDER_NAME_EXTERNAL = os.getenv(
    "STREAM_PROVIDER_NAME_EXTERNAL",
    "Remote Files (External)",
)

# Stream resolver tokens (external playback)
RAW_STREAM_TOKENS = os.getenv("STREAM_TOKENS", "")
STREAM_TOKENS = {t.strip() for t in RAW_STREAM_TOKENS.split(",") if t.strip()}

# Admin scan token (admin actions only)
ADMIN_SCAN_TOKEN = os.getenv("ADMIN_SCAN_TOKEN")

# Media subfolder names under /media
MOVIES_DIR_NAME = os.getenv("MOVIES_DIR_NAME", "movies")
SERIES_DIR_NAME = os.getenv("SERIES_DIR_NAME", "series")
