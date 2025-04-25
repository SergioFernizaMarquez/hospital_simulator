# data_generation/simulate_inventory.py

import psycopg2
from utils.db_config import get_db_connection
from simulate_restock_inventory import restock_inventory

def run_daily_inventory_check(sim_time):
    """
    At 06:00 each day, check inventory levels and trigger restocking
    for any medication where current_stock < minimum_stock.
    Returns the number of items restocked.
    """
    # Only run at 06:00
    if sim_time.hour != 6:
        return 0

    conn = get_db_connection()
    cur = conn.cursor()
    # 1) find all low-stock entries
    cur.execute("""
        SELECT hospital_id, medication_id, current_stock, minimum_stock
        FROM inventory
        WHERE current_stock < minimum_stock;
    """)
    low_stock_items = cur.fetchall()

    restocked_count = 0
    for hospital_id, medication_id, current_stock, minimum_stock in low_stock_items:
        # 2) pick a supplier for this medication
        cur.execute("""
            SELECT supplier_id
            FROM supplier_medications
            WHERE medication_id = %s
            LIMIT 1;
        """, (medication_id,))
        row = cur.fetchone()
        if row:
            supplier_id = row[0]
        else:
            # no supplier found; skip restock
            continue

        # 3) trigger restock (adds 50000 units and logs payment)
        restock_inventory(
            hospital_id=hospital_id,
            medication_id=medication_id,
            supplier_id=supplier_id,
            quantity=50000
        )
        restocked_count += 1

    cur.close()
    conn.close()
    return restocked_count

if __name__ == "__main__":
    from datetime import datetime
    # Example: simulate check for today at 06:00
    check_time = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    count = run_daily_inventory_check(check_time)
    print(f"Performed inventory check at {check_time}: {count} items restocked.")
