"""Query the inspections SQLite database from the command line."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.sqlite_store import DEFAULT_DB, create_tables, fetch_all, get_connection


def cmd_critical(conn: sqlite3.Connection, company=None, state=None, years=None) -> None:
    rows = fetch_all(
        conn,
        """
        SELECT v.id, f.name, v.date, v.severity, v.species, substr(v.notes, 1, 200) AS notes_preview
        FROM violations v
        JOIN facilities f ON f.id = v.facility_id
        WHERE lower(v.severity) LIKE '%critical%'
          AND lower(v.severity) NOT LIKE '%non%'
        ORDER BY v.date DESC
        """,
    )
    _print_rows(rows)


def cmd_critical(conn: sqlite3.Connection, company=None, state=None, years=None) -> None:
    query = """
    SELECT v.id, f.name, f.company, f.location, v.date, v.severity, v.species,
           substr(v.notes, 1, 200) AS notes_preview
    FROM violations v
    JOIN facilities f ON f.id = v.facility_id
    WHERE lower(v.severity) LIKE '%critical%'
      AND lower(v.severity) NOT LIKE '%non%'
    """

    params = []

    # 🔹 Company OR Facility name filter
    if company:
        query += " AND (lower(f.company) LIKE ? OR lower(f.name) LIKE ?)"
        params.append(f"%{company.lower()}%")
        params.append(f"%{company.lower()}%")

    # 🔹 State / location filter
    if state:
        query += " AND lower(f.location) LIKE ?"
        params.append(f"%{state.lower()}%")

    # 🔹 Year filter (based on last N years)
    if years:
        from datetime import datetime
        current_year = datetime.now().year
        min_year = current_year - years
        query += " AND substr(v.date, -4) >= ?"
        params.append(str(min_year))

    query += " ORDER BY v.date DESC"

    rows = fetch_all(conn, query, tuple(params))
    _print_rows(rows)


def cmd_species(conn: sqlite3.Connection, species: str) -> None:
    like = f"%{species.strip()}%"
    rows = fetch_all(
        conn,
        """
        SELECT v.id, f.name, v.date, v.severity, v.species, substr(v.notes, 1, 200)
        FROM violations v
        JOIN facilities f ON f.id = v.facility_id
        WHERE v.species LIKE ?
        ORDER BY v.date DESC
        """,
        (like,),
    )
    _print_rows(rows)


def cmd_date_range(conn: sqlite3.Connection, start: str, end: str) -> None:
    rows = fetch_all(
        conn,
        """
        SELECT v.id, f.name, v.date, v.severity, v.species, substr(v.notes, 1, 200)
        FROM violations v
        JOIN facilities f ON f.id = v.facility_id
        WHERE v.date BETWEEN ? AND ?
        ORDER BY v.date DESC
        """,
        (start, end),
    )
    _print_rows(rows)


def _print_rows(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("(no rows)")
        return
    keys = rows[0].keys()
    print("\t".join(keys))
    for r in rows:
        print("\t".join(str(r[k]) for k in keys))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="USDA inspection SQLite queries")
    p.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to SQLite file",
    )
    sub = p.add_subparsers(dest="command", required=True)

    cp = sub.add_parser("critical", help="List violations flagged as critical")
    cp.add_argument("--company", help="Filter by company")
    cp.add_argument("--state", help="Filter by location/state")
    cp.add_argument("--years", type=int, help="Last N years")

    rp = sub.add_parser("repeats", help="Facilities with repeated violations")
    rp.add_argument(
        "--min",
        type=int,
        default=2,
        metavar="N",
        help="Minimum violation count per facility (default: 2)",
    )

    sp = sub.add_parser("species", help="Filter by species substring")
    sp.add_argument("name", help="Species text to match (SQL LIKE)")

    dr = sub.add_parser("daterange", help="Filter by inspection date (string compare)")
    dr.add_argument("start", help="Start date (same format as stored dates)")
    dr.add_argument("end", help="End date (inclusive)")

    return p


def main() -> None:
    args = build_parser().parse_args()
    conn = get_connection(args.db)
    create_tables(conn)

    if args.command == "critical":
        cmd_critical(conn, args.company, args.state, args.years)
    elif args.command == "repeats":
        cmd_repeats(conn, args.min)
    elif args.command == "species":
        cmd_species(conn, args.name)
    elif args.command == "daterange":
        cmd_date_range(conn, args.start, args.end)


if __name__ == "__main__":
    main()
