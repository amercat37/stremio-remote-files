# app/db/init.py
import sqlite3
from pathlib import Path

DB_PATH = "/data/library.db"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.commit()
    finally:
        conn.close()
