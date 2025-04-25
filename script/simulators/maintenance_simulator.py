# data_generation/maintenance_simulator.py

import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from utils.db_config import get_db_connection
from simulate_inventory import run_daily_inventory_check
from simulate_payroll import run_hourly_payroll

# configure logging for debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def run_maintenance(start_date: datetime, days: int):
    """
    For each simulated day:
      1) At 00:00, reduce every inventory.current_stock by 10–35%
      2) At 06:00, call run_daily_inventory_check (triggers restock if needed)
      3) At 12:00, call run_hourly_payroll
    """
    for day_offset in range(days):
        # this day at midnight
        day = (start_date + timedelta(days=day_offset)).replace(hour=0, minute=0, second=0, microsecond=0)

        # 1) Reduce stock
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT inventory_id, current_stock, minimum_stock FROM inventory;")
        rows = cur.fetchall()
        for inventory_id, current_stock, minimum_stock in rows:
            pct = random.uniform(0.10, 0.35)
            reduce_amt = int(current_stock * pct)
            new_stock = max(current_stock - reduce_amt, 0)
            cur.execute(
                "UPDATE inventory SET current_stock = %s WHERE inventory_id = %s;",
                (new_stock, inventory_id)
            )
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"[MAINT] {day.date()}: reduced inventory by 10–35%")

        # 2) Restock check at 06:00
        inv_time = day + timedelta(hours=6)
        restocked = run_daily_inventory_check(inv_time)
        logging.info(f"[MAINT] {inv_time}: restocked {restocked} items")

        # 3) Payroll at 12:00
        pay_time = day + timedelta(hours=12)
        paid = run_hourly_payroll(pay_time)
        if paid:
            logging.info(f"[MAINT] {pay_time}: processed payroll for {paid} employees")
        else:
            logging.info(f"[MAINT] {pay_time}: no payroll due")

if __name__ == "__main__":
    # Example: run maintenance from April 25 for 14 days
    START = datetime(2025, 4, 25)
    DAYS  = 14
    run_maintenance(START, DAYS)
