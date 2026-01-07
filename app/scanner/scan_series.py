"""
Series filesystem scanner.

This module scans the series directory structure, resolves metadata via TMDB,
and synchronizes series, episodes, and file records into the SQLite database.
"""

from pathlib import Path
import re
import sqlite3

from core.config import SERIES_DIR_NAME
from metadata.tmdb import lookup_series
from db.series_repo import upsert_series, upsert_episode, upsert_episode_file

# Root directory for series files (mounted volume)
SERIES_ROOT = Path("/media") / SERIES_DIR_NAME

# SQLite database location
DB_PATH = "/data/library.db"

# Expected season folder format:
#   Season 01
SEASON_PATTERN = re.compile(r"Season\s+(?P<season>\d+)", re.IGNORECASE)

# Expected episode filename format:
#   S01E02 - Episode Title [1080p].ext
EPISODE_PATTERN = re.compile(
    r"""
    ^S(?P<season>\d{2})           # Season number
    E(?P<episode>\d{2})           # Episode number
    (?:\s*-\s*.+?)?               # Optional episode title
    (?:\s*\[(?P<res>\d+p)\])?     # Optional [1080p]
    \.\w+$                        # File extension
    """,
    re.IGNORECASE | re.VERBOSE,
)


def scan_series():
    """
    Scan the series directory and synchronize database records.

    - Discovers series, seasons, and episode files on disk
    - Looks up series metadata via TMDB
    - Inserts or updates series, episode, and file records
    - Removes database entries for files no longer present
    """
    if not SERIES_ROOT.exists():
        print(f"[WARN] Series directory not found: {SERIES_ROOT}")
        return

    conn = sqlite3.connect(DB_PATH)
    seen_paths = set()

    try:
        for series_dir in SERIES_ROOT.iterdir():
            if not series_dir.is_dir():
                continue

            series_name = series_dir.name
            print(f"[INFO] TMDB lookup: {series_name}")

            meta = lookup_series(series_name)
            if not meta:
                print(f"[WARN] TMDB lookup failed: {series_name}")
                continue

            # 1) Upsert series metadata
            upsert_series(conn, meta)
            series_imdb_id = meta["imdb_id"]

            for season_dir in series_dir.iterdir():
                if not season_dir.is_dir():
                    continue

                season_match = SEASON_PATTERN.match(season_dir.name)
                if not season_match:
                    print(f"[SKIP] Season folder: {season_dir.name}")
                    continue

                season_num = int(season_match.group("season"))

                for ep_file in season_dir.iterdir():
                    if not ep_file.is_file():
                        continue

                    # STRICT match: whole filename must conform
                    ep_match = EPISODE_PATTERN.match(ep_file.name)
                    if not ep_match:
                        print(f"[SKIP] Episode file: {ep_file.name}")
                        continue

                    episode_num = int(ep_match.group("episode"))
                    resolution = ep_match.group("res")  # may be None

                    # Track file as seen for cleanup
                    seen_paths.add(str(ep_file))

                    # 2) Upsert episode
                    episode_id = upsert_episode(
                        conn,
                        series_imdb_id,
                        season_num,
                        episode_num,
                    )

                    # 3) Upsert episode file
                    upsert_episode_file(
                        conn,
                        episode_id=episode_id,
                        path=str(ep_file),
                        resolution=resolution,
                        size=ep_file.stat().st_size,
                    )

        # 4) Delete episode files no longer present on disk
        if seen_paths:
            placeholders = ",".join("?" * len(seen_paths))
            conn.execute(
                f"""
                DELETE FROM files
                WHERE episode_id IS NOT NULL
                  AND path NOT IN ({placeholders})
                """,
                tuple(seen_paths),
            )

        conn.commit()
        print("[OK] Series scan complete")

    finally:
        conn.close()
