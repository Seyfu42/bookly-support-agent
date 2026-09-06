"""Durable session storage.

SQLite, deliberately. Redis or Postgres is what this would be in production, and
the interface here is narrow enough that swapping it is a afternoon's work -- but
SQLite ships inside Python, so `git clone && uv run` gives you a working,
persistent agent with no server to install and no container to start. For a demo
that someone else has to run, that matters more than picking the "real" database.

The whole conversation is stored as one JSON blob per session. That is the right
shape here: we always read and write a whole conversation, never query across
them. If this needed analytics over turns, the trace would become its own table.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "bookly_sessions.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL,
    turn_count  INTEGER NOT NULL DEFAULT 0,
    escalated   INTEGER NOT NULL DEFAULT 0,
    payload     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    # WAL lets the web process read while another writes, which matters the
    # moment there is more than one uvicorn worker.
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def load(session_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT payload FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def save(session_id: str, payload: dict[str, Any], *, turn_count: int,
         escalated: bool) -> None:
    now = time.time()
    blob = json.dumps(payload, default=str)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, created_at, updated_at, turn_count,
                                  escalated, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                updated_at = excluded.updated_at,
                turn_count = excluded.turn_count,
                escalated  = excluded.escalated,
                payload    = excluded.payload
            """,
            (session_id, now, now, turn_count, int(escalated), blob),
        )


def delete(session_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))


def stats() -> dict[str, Any]:
    """Small operational view -- used by the CLI and handy in a demo."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS sessions,
                   COALESCE(SUM(turn_count), 0) AS turns,
                   COALESCE(SUM(escalated), 0)  AS escalated
            FROM sessions
            """
        ).fetchone()
    return {"sessions": row["sessions"], "turns": row["turns"],
            "escalated": row["escalated"], "db": str(DB_PATH)}
