"""
Authentication and access helpers.

This module centralizes token-based access control used by the
Stremio Remote Files addon.

Security model:
- Internal endpoints are trusted based on network placement.
- External stream resolvers require a stream token and fail closed (empty results).
- Admin actions require a dedicated Bearer token and fail explicitly.
"""

from fastapi import Request, HTTPException
from core.config import ADMIN_SCAN_TOKEN, STREAM_TOKENS


def is_external(request: Request) -> bool:
    """
    Determine whether a request is targeting an external endpoint.

    External endpoints are exposed over HTTPS and require stream token validation.
    """
    return request.url.path.startswith("/external")


def valid_stream_token(request: Request) -> bool:
    """
    Validate the token passed to external Stremio stream resolver endpoints.

    External stream endpoints do not raise errors on auth failure; they return
    empty results instead to satisfy Stremio addon expectations.
    """
    token = request.query_params.get("token")
    return token in STREAM_TOKENS


def require_admin_token(request: Request):
    """
    Enforce admin authorization using a dedicated Bearer token.

    Used by admin POST endpoints where failures should be explicit
    (401/403) rather than silent.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")

    token = auth.removeprefix("Bearer ").strip()
    if token != ADMIN_SCAN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
