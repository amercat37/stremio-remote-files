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


# ---------------------------------------------------------------------------
# Paths / config
# ---------------------------------------------------------------------------

# Root directory for series files (mounted volume)
SERIES_ROOT = Path("/media") / SERIES_DIR_NAME

# SQLite database location
DB_PATH = "/data/library.db"


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Expected season folder format:
#   Season 01
SEASON_PATTERN = re.compile(r"Season\s+(?P<season>\d+)", re.IGNORECASE)

# Episode identity: find SxEx anywhere in filename
EPISODE_SE_PATTERN = re.compile(
    r"""
    S(?P<season>\d{1,2})
    E(?P<episode>\d{1,2})
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Resolution tokens (optional metadata, anywhere in filename)
RESOLUTION_PATTERN = re.compile(
    r"""
    (?P<res>
        240p | 360p | 480p | 576p | 720p | 900p |
        1080p | 1440p | 2160p | 4320p |
        480i | 576i | 1080i |
        2K | 4K | 8K
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_episode_filename(filename: str):
    """
    Extract season, episode, and optional resolution from an episode filename.

    Returns:
        (season_from_file: int, episode: int, resolution: str | None)
        or None if no SxEx pattern is found.
    """
    se_match = EPISODE_SE_PATTERN.search(filename)
    if not se_match:
        return None

    season_from_file = int(se_match.group("season"))
    episode = int(se_match.group("episode"))

    res_match = RESOLUTION_PATTERN.search(filename)
    resolution = res_match.group("res") if res_match else None

    return season_from_file, episode, resolution


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

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

                    parsed = parse_episode_filename(ep_file.name)
                    if not parsed:
                        print(f"[SKIP] Episode file: {ep_file.name}")
                        continue

                    season_from_file, episode_num, resolution = parsed

                    # Optional sanity check (non-fatal)
                    if season_from_file != season_num:
                        print(
                            f"[WARN] Season mismatch: folder={season_num}, "
                            f"filename={season_from_file} ({ep_file.name})"
                        )

                    # Track file as seen for cleanup
                    seen_paths.add(str(ep_file))

                    # 2) Upsert episode (folder season is authoritative)
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
