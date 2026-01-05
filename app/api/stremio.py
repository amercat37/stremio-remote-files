"""
Public Stremio addon endpoints.

This module exposes:
- catalogs (movies, series)
- stream resolvers for movies and episodes
- addon manifests (internal and external)

Security model:
- Internal endpoints are trusted (LAN / VPN).
- External endpoints require a valid token and silently return empty results
  when access is unauthorized, per Stremio addon expectations.
"""

from fastapi import APIRouter, Request
from urllib.parse import quote
from pathlib import Path
import sqlite3

from db.catalog import get_movie_catalog, get_series_catalog
from core.config import (
    DB_PATH,
    MEDIA_BASE_URL_INTERNAL,
    MEDIA_BASE_URL_EXTERNAL,
)
from core.auth import is_external, valid_stream_token

router = APIRouter()


# ------------------------------------------------------------
# CATALOGS
# ------------------------------------------------------------

@router.get("/internal/catalog/movie/remote-files.json")
@router.get("/external/catalog/movie/remote-files.json")
def catalog_movies():
    with sqlite3.connect(DB_PATH) as conn:
        return {"metas": get_movie_catalog(conn)}


@router.get("/internal/catalog/series/remote-files.json")
@router.get("/external/catalog/series/remote-files.json")
def catalog_series():
    with sqlite3.connect(DB_PATH) as conn:
        return {"metas": get_series_catalog(conn)}


# ------------------------------------------------------------
# STREAM: MOVIE
# ------------------------------------------------------------

@router.get("/internal/stream/movie/{imdb_id}.json")
@router.get("/external/stream/movie/{imdb_id}.json")
def stream_movie(imdb_id: str, request: Request):
    external = is_external(request)

    # External requests fail closed with an empty stream list
    if external and not valid_stream_token(request):
        return {"streams": []}

    base_url = MEDIA_BASE_URL_EXTERNAL if external else MEDIA_BASE_URL_INTERNAL
    provider_name = "Remote Files (External)" if external else "Remote Files (Internal)"

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT path, resolution, size
            FROM files
            WHERE movie_imdb_id = ?
            """,
            (imdb_id,),
        ).fetchall()

    streams = []

    for path, resolution, size in rows:
        # percent-encode each path segment
        safe_path = "/".join(quote(p) for p in path.split("/"))
        url = f"{base_url}{safe_path.replace('/media', '')}"

        res = resolution or ""

        filename = Path(path).name
        size_gb = round(size / (1024 ** 3), 1)

        title = f"{filename}\n💾 {size_gb} GB"

        streams.append(
            {
                "name": f"{provider_name} {res}".strip(),
                "title": title,
                "url": url,
                "availability": "local",
                "behaviorHints": {
                    "notWebReady": False,
                    "confidence": 1,
                },
            }
        )

    return {"streams": streams}


# ------------------------------------------------------------
# STREAM: SERIES / EPISODE
# episode_id format: ttXXXXXX:S:E
# ------------------------------------------------------------

@router.get("/internal/stream/series/{episode_id}.json")
@router.get("/external/stream/series/{episode_id}.json")
def stream_episode(episode_id: str, request: Request):
    external = is_external(request)

    # External requests fail closed with an empty stream list
    if external and not valid_stream_token(request):
        return {"streams": []}

    try:
        series_imdb_id, season, episode = episode_id.split(":")
        season = int(season)
        episode = int(episode)
    except ValueError:
        return {"streams": []}

    base_url = MEDIA_BASE_URL_EXTERNAL if external else MEDIA_BASE_URL_INTERNAL
    provider_name = "Remote Files (External)" if external else "Remote Files (Internal)"

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
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

    streams = []

    for path, resolution, size in rows:
        # percent-encode each path segment
        safe_path = "/".join(quote(p) for p in path.split("/"))
        url = f"{base_url}{safe_path.replace('/media', '')}"

        res = resolution or ""

        filename = Path(path).name
        size_gb = round(size / (1024 ** 3), 1)

        title = f"{filename}\n💾 {size_gb} GB"

        streams.append(
            {
                "name": f"{provider_name} {res}".strip(),
                "title": title,
                "url": url,
                "behaviorHints": {
                    "notWebReady": False,
                    "bingeGroup": series_imdb_id,
                },
            }
        )

    return {"streams": streams}


# ------------------------------------------------------------
# MANIFESTS
# ------------------------------------------------------------

@router.get("/internal/manifest.json")
def manifest_internal():
    return {
        "id": "org.remote-files.internal",
        "name": "Remote Files (Internal)",
        "version": "1.1.2",
        "description": "Browse and play your own media over LAN or VPN",
        "behaviorHints": {
            "configurable": True,
            "configurationRequired": False,
        },
        "resources": [
            "catalog",
            {
                "name": "stream",
                "types": ["movie", "series"],
                "idPrefixes": ["tt"],
            },
        ],
        "types": ["movie", "series"],
        "catalogs": [
            {
                "type": "movie",
                "id": "remote-files",
                "name": "Remote Files",
            },
            {
                "type": "series",
                "id": "remote-files",
                "name": "Remote Files",
            },
        ],
    }



@router.get("/external/manifest.json")
def manifest_external():
    return {
        "id": "org.remote-files.external",
        "name": "Remote Files (External)",
        "version": "1.1.2",
        "description": "Browse and play your own media over the internet using HTTPS",
        "behaviorHints": {
            "configurable": True,
            "configurationRequired": False,
        },
        "resources": [
            "catalog",
            {
                "name": "stream",
                "types": ["movie", "series"],
                "idPrefixes": ["tt"],
            },
        ],
        "types": ["movie", "series"],
        "catalogs": [],
    }
