# data_generation/generate_inventory.py

import psycopg2
from utils.db_config import get_db_connection

def fetch_hospital_ids():
    """Fetch all hospital IDs from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT hospital_id FROM hospitals;")
    hospital_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return hospital_ids

def fetch_medication_ids():
    """Fetch all medication IDs from the database."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT medication_id FROM medications;")
    medication_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return medication_ids

def insert_inventory():
    """
    Generate inventory entries for every hospital-medication pair
    with current_stock=100000 and minimum_stock=50000.
    """
    hospital_ids = fetch_hospital_ids()
    medication_ids = fetch_medication_ids()

    conn = get_db_connection()
    cur = conn.cursor()

    # Prepare all records
    records = [
        (hid, mid, 100000, 50000)
        for hid in hospital_ids
        for mid in medication_ids
    ]

    # Bulk insert
    cur.executemany("""
        INSERT INTO inventory (hospital_id, medication_id, current_stock, minimum_stock)
        VALUES (%s, %s, %s, %s);
    """, records)

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Inserted inventory records for {len(records)} hospital-medication pairs.")

if __name__ == "__main__":
    insert_inventory()

