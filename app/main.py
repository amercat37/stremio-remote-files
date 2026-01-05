"""
Application entry point.

This module creates the FastAPI app, initializes the database on startup,
and wires together the API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.init import init_db
from api.stremio import router as stremio_router
from api.admin import router as admin_router
from api.auth import router as auth_router
from scanner import scan_movies, scan_series

app = FastAPI()

# Stremio desktop/web clients require permissive CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
)


@app.on_event("startup")
def startup():
    """
    Initialize the database schema at application startup.
    """
    init_db()

    # Initial library scan (runs once on startup)
    scan_movies()
    scan_series()


# Public Stremio addon endpoints
app.include_router(stremio_router)

# Admin and install endpoints
app.include_router(admin_router)

# Auth endpoints
app.include_router(auth_router)