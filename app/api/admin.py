"""
Admin and installation endpoints for the Stremio Remote Files addon.

This module provides:
- A lightweight admin UI for triggering library scans
- An install page for generating Stremio addon install links

Note: The HTML pages themselves are intentionally unauthenticated.
All destructive or privileged actions require a valid admin token.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3

from scanner import scan_movies, scan_series
from core.config import DB_PATH
from core.auth import require_admin_token

router = APIRouter()

templates = Jinja2Templates(directory="api/templates")


# These pages are intentionally unauthenticated.
# All privileged actions are protected by token checks on POST routes.
@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {"request": request}
    )


@router.post("/admin/scan")
def admin_scan(request: Request):
    require_admin_token(request)

    scan_movies()
    scan_series()

    return {
        "status": "ok",
        "mode": "incremental"
    }


@router.post("/admin/scan/rebuild")
def admin_scan_rebuild(request: Request):
    require_admin_token(request)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM files")
        conn.execute("DELETE FROM episodes")
        conn.execute("DELETE FROM series")
        conn.execute("DELETE FROM movies")
        conn.commit()

    scan_movies()
    scan_series()

    return {
        "status": "ok",
        "mode": "rebuild"
    }


# Configuration / install UI.
#
# These endpoints intentionally return a human-friendly HTML page.
# The same page is used for:
# - initial addon installation
# - the Stremio ⚙️ configure action (internal and external)
#
# Access control for streaming is enforced via tokenized stream endpoints
# and proxy-level checks, not via the configure page itself.
@router.get("/internal/configure", response_class=HTMLResponse)
@router.get("/external/configure", response_class=HTMLResponse)
def configure_page(request: Request):
    return templates.TemplateResponse(
        "configure.html",
        {"request": request}
    )
    