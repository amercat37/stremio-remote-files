"""
Series database repository helpers.

This module contains write/update helpers for series, episodes,
and associated media files stored in the SQLite database.
"""

import json


def upsert_series(conn, series):
    """
    Insert a series into the database if it does not already exist.

    Expects a dict with imdb_id, title, poster_url, and genres.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO series
        (imdb_id, title, poster_url, genres)
        VALUES (?, ?, ?, ?)
        """,
        (
            series["imdb_id"],
            series["title"],
            series["poster_url"],
            json.dumps(series["genres"]),
        ),
    )


def upsert_episode(conn, series_imdb_id, season, episode):
    """
    Insert an episode if it does not already exist and return its ID.

    Episodes are uniquely identified by (series_imdb_id, season, episode).
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO episodes
        (series_imdb_id, season, episode)
        VALUES (?, ?, ?)
        """,
        (series_imdb_id, season, episode),
    )

    # Fetch and return the episode primary key
    row = conn.execute(
        """
        SELECT id FROM episodes
        WHERE series_imdb_id = ? AND season = ? AND episode = ?
        """,
        (series_imdb_id, season, episode),
    ).fetchone()

    return row[0]


def upsert_episode_file(conn, episode_id, path, resolution, size):
    """
    Insert or update a media file associated with an episode.

    The file path is treated as the natural key.
    """
    conn.execute(
        """
        INSERT INTO files (episode_id, path, resolution, size)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            episode_id = excluded.episode_id,
            resolution = excluded.resolution,
            size = excluded.size
        """,
        (episode_id, path, resolution, size),
    )
