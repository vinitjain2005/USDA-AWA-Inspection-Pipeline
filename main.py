from parser.pdf_parser import parse_all_pdfs
from database.sqlite_store import (
    get_connection,
    create_tables,
    insert_facility,
    insert_violation,
)

def run_pipeline():
    conn = get_connection()
    create_tables(conn)

    data = parse_all_pdfs()

    print(f"Parsed rows: {len(data)}")

    inserted_count = 0

    for d in data:
        facility_id = insert_facility(
            conn,
            name=d["facility_name"],
            company=d["company"],
            location=d["location"],
        )

        inserted = insert_violation(
            conn,
            facility_id=facility_id,
            date=d["inspection_date"],
            severity=d["severity"],
            species=d["species"],
            notes=d["inspector_notes"],
        )

        if inserted:
            inserted_count += 1

    print(f"New violation rows inserted: {inserted_count}")

if __name__ == "__main__":
    run_pipeline()
