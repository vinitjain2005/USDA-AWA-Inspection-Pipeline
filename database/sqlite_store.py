"""SQLite persistence for facilities and violations."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "inspections.db"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            UNIQUE(name, company, location)
        );

        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            severity TEXT NOT NULL,
            species TEXT NOT NULL DEFAULT '',
            notes TEXT,
            UNIQUE(facility_id, date, severity, species, notes)
        );

        CREATE INDEX IF NOT EXISTS idx_violations_facility ON violations(facility_id);
        CREATE INDEX IF NOT EXISTS idx_violations_date ON violations(date);
        CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);
        """
    )
    conn.commit()


def insert_facility(
    conn: sqlite3.Connection,
    name: str,
    company: str = "",
    location: str = "",
) -> int:
    name = name.strip()
    company = (company or "").strip()
    location = (location or "").strip()
    conn.execute(
        """
        INSERT OR IGNORE INTO facilities (name, company, location)
        VALUES (?, ?, ?)
        """,
        (name, company, location),
    )
    row = conn.execute(
        "SELECT id FROM facilities WHERE name = ? AND company = ? AND location = ?",
        (name, company, location),
    ).fetchone()
    if row is None:
        raise RuntimeError("insert_facility failed to resolve id")
    conn.commit()
    return int(row["id"])


def insert_violation(
    conn: sqlite3.Connection,
    facility_id: int,
    date: str,
    severity: str,
    species: str | None,
    notes: str,
) -> bool:
    """
    Insert a violation row. Returns True if a new row was inserted.
    """
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO violations (facility_id, date, severity, species, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            facility_id,
            date.strip(),
            severity.strip(),
            (species or "").strip(),
            (notes or "").strip(),
        ),
    )
    conn.commit()
    return cur.rowcount > 0


def fetch_all(
    conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()
) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params))
