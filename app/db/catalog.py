"""
Catalog query helpers.

This module provides database access functions for building Stremio
catalog responses for movies and series.
"""

import json


def get_movie_catalog(conn):
    """
    Return the movie catalog for Stremio.

    Expects an open SQLite connection and returns a list of catalog
    entries sorted by title.
    """
    rows = conn.execute(
        """
        SELECT imdb_id, title, poster_url, genres
        FROM movies
        ORDER BY title
        """
    ).fetchall()

    return [
        {
            "id": row[0],
            "type": "movie",
            "name": row[1],
            "poster": row[2],
            "genres": json.loads(row[3]) if row[3] else [],
        }
        for row in rows
    ]


def get_series_catalog(conn):
    """
    Return the series catalog for Stremio.

    Expects an open SQLite connection and returns a list of catalog
    entries sorted by title.
    """
    rows = conn.execute(
        """
        SELECT imdb_id, title, poster_url, genres
        FROM series
        ORDER BY title
        """
    ).fetchall()

    return [
        {
            "id": row[0],
            "type": "series",
            "name": row[1],
            "poster": row[2],
            "genres": json.loads(row[3]) if row[3] else [],
        }
        for row in rows
    ]
