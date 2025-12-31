"""
Stream query helpers.

This module provides read-only database helpers for resolving
media files used by Stremio stream endpoints.
"""


def get_movie_files(conn, imdb_id):
    """
    Return all media files associated with a movie.

    Expects an open SQLite connection and a movie IMDb ID.
    """
    return conn.execute(
        """
        SELECT path, resolution, size
        FROM files
        WHERE movie_imdb_id = ?
        """,
        (imdb_id,),
    ).fetchall()


def get_episode_files(conn, series_imdb_id, season, episode):
    """
    Return all media files associated with a specific episode.

    Episodes are identified by series IMDb ID, season, and episode number.
    """
    return conn.execute(
        """
        SELECT f.path, f.resolution, f.size
        FROM episodes e
        JOIN files f ON f.episode_id = e.id
        WHERE e.series_imdb_id = ?
          AND e.season = ?
          AND e.episode = ?
        """,
        (series_imdb_id, season, episode),
    ).fetchall()
