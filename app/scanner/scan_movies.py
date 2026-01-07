"""
Movie filesystem scanner.

This module scans the movies directory, resolves metadata via TMDB,
and synchronizes movie and file records into the SQLite database.
"""

from pathlib import Path
import re
import sqlite3

from core.config import MOVIES_DIR_NAME
from metadata.tmdb import lookup_movie
from db.movie_repo import upsert_movie, upsert_movie_file

# Root directory for movie files (mounted volume)
MOVIES_ROOT = Path("/media") / MOVIES_DIR_NAME

# SQLite database location
DB_PATH = "/data/library.db"

# Expected filename format:
#   Movie Title (YYYY) [1080p].ext
MOVIE_PATTERN = re.compile(
    r"""
    ^(?P<title>.+?)            # Movie title
    \s*\( (?P<year>\d{4}) \)   # Year in parentheses
    (?:\s*\[(?P<res>\d+p)\])?  # Optional [1080p]
    \.\w+$                     # File extension
    """,
    re.VERBOSE | re.IGNORECASE,
)


def scan_movies():
    """
    Scan the movie directory and synchronize database records.

    - Discovers movie files on disk
    - Looks up metadata via TMDB
    - Inserts or updates movie and file records
    - Removes database entries for files no longer present
    """
    if not MOVIES_ROOT.exists():
        print(f"[WARN] Movies directory not found: {MOVIES_ROOT}")
        return

    conn = sqlite3.connect(DB_PATH)
    seen_paths = set()

    try:
        for path in MOVIES_ROOT.iterdir():
            if not path.is_file():
                continue

            match = MOVIE_PATTERN.match(path.name)
            if not match:
                print(f"[SKIP] Unrecognized movie filename: {path.name}")
                continue

            data = match.groupdict()

            title = data["title"]
            year = int(data["year"])
            resolution = data.get("res")

            print(f"[INFO] TMDB lookup: {title} ({year})")

            meta = lookup_movie(title, year)

            if not meta:
                print(f"[WARN] TMDB lookup failed: {title}")
                continue

            # Track file as seen for cleanup
            seen_paths.add(str(path))

            # 1) Upsert movie metadata
            upsert_movie(conn, meta)

            # 2) Upsert file record
            upsert_movie_file(
                conn,
                imdb_id=meta["imdb_id"],
                path=str(path),
                resolution=resolution,
                size=path.stat().st_size,
            )

        # 3) Delete movie files no longer present on disk
        if seen_paths:
            placeholders = ",".join("?" * len(seen_paths))
            conn.execute(
                f"""
                DELETE FROM files
                WHERE movie_imdb_id IS NOT NULL
                  AND path NOT IN ({placeholders})
                """,
                tuple(seen_paths),
            )

        conn.commit()
        print("[OK] Movie scan complete")

    finally:
        conn.close()
