"""
Movie database repository helpers.

This module contains write/update helpers for movie metadata and
associated media files stored in the SQLite database.
"""

import json


def upsert_movie(conn, movie):
    """
    Insert a movie into the database if it does not already exist.

    Expects a dict with imdb_id, title, year, poster_url, and genres.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO movies
        (imdb_id, title, year, poster_url, genres)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            movie["imdb_id"],
            movie["title"],
            movie["year"],
            movie["poster_url"],
            json.dumps(movie["genres"]),
        ),
    )


def upsert_movie_file(conn, imdb_id, path, resolution, size):
    """
    Insert or update a movie file entry.

    If the file path already exists, the record is updated and any
    episode association is cleared.
    """
    conn.execute(
        """
        INSERT INTO files (movie_imdb_id, path, resolution, size)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            movie_imdb_id = excluded.movie_imdb_id,
            resolution = excluded.resolution,
            size = excluded.size,
            episode_id = NULL
        """,
        (imdb_id, path, resolution, size),
    )
