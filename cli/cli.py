import argparse
from database.sqlite_store import get_connection

def get_critical(conn):
    rows = conn.execute("""
        SELECT DISTINCT f.name, f.location, v.date, v.severity
        FROM violations v
        JOIN facilities f ON v.facility_id = f.id
        WHERE v.severity = 'Critical'
    """).fetchall()
    return rows


def get_repeat(conn):
    rows = conn.execute("""
        SELECT f.name, COUNT(*) as count
        FROM violations v
        JOIN facilities f ON v.facility_id = f.id
        GROUP BY f.name
        HAVING count > 1
    """).fetchall()
    return rows


def get_by_species(conn, species):
    rows = conn.execute("""
        SELECT f.name, v.date, v.severity, v.species
        FROM violations v
        JOIN facilities f ON v.facility_id = f.id
        WHERE LOWER(v.species) LIKE ?
        OR LOWER(v.notes) LIKE ?
    """, (f"%{species.lower()}%", f"%{species.lower()}%")).fetchall()

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--critical", action="store_true")
    parser.add_argument("--repeat", action="store_true")
    parser.add_argument("--species", type=str)

    args = parser.parse_args()

    conn = get_connection()

    if args.critical:
        results = get_critical(conn)
    elif args.repeat:
        results = get_repeat(conn)
    elif args.species:
        results = get_by_species(conn, args.species)
    else:
        print("No valid argument provided")
        return

    for row in results:
        print(dict(row))


if __name__ == "__main__":
    main()