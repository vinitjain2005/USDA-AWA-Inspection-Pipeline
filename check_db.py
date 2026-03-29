from database.sqlite_store import get_connection, fetch_all

conn = get_connection()

rows = fetch_all(conn, "SELECT * FROM violations LIMIT 20")

for r in rows:
    print(dict(r))