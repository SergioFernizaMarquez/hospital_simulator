# data_generation/simulate_restock_inventory.py

import psycopg2
import random
from datetime import datetime
from decimal import Decimal
from utils.db_config import get_db_connection


def restock_inventory(hospital_id: int, medication_id: int, supplier_id: int, quantity: int):
    """
    Adds `quantity` units of `medication_id` to the inventory at `hospital_id`,
    records any supply anomalies (~5%), and logs the payment.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    sim_ts = datetime.utcnow()

    # 1) Fetch unit cost from medications
    cur.execute(
        "SELECT unit_cost FROM medications WHERE medication_id = %s;",
        (medication_id,)
    )
    expected_unit_price = cur.fetchone()[0]  # Decimal

    # defaults: no anomaly
    qty_mult   = Decimal('1.0')
    price_mult = Decimal('1.0')

    # 2) Create a supply order record
    cur.execute(
        """
        INSERT INTO supply_orders (hospital_id, simulation_timestamp)
        VALUES (%s, %s)
        RETURNING order_id;
        """,
        (hospital_id, sim_ts)
    )
    order_id = cur.fetchone()[0]

    # 3) Randomly inject supply anomalies (~5%)
    if random.random() < 0.05:
        qty_mult   = Decimal(str(random.choice([0.9, 1.1])))
        price_mult = Decimal(str(random.choice([0.9, 1.1])))
        received_qty    = int(quantity * float(qty_mult))
        paid_unit_price = expected_unit_price * price_mult

        # build anomaly description
        anomaly_types = []
        anomaly_types.append('Under-delivery' if qty_mult < 1 else 'Over-delivery')
        anomaly_types.append('Underpayment'    if price_mult < 1 else 'Overpayment')
        anomaly_type = ', '.join(anomaly_types)

        # record in supply_anomalies (use simulation_timestamp col)
        cur.execute(
            """
            INSERT INTO supply_anomalies
              (order_id, medication_id, anomaly_type,
               expected_quantity, received_quantity,
               expected_unit_price, paid_unit_price,
               notes, simulation_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                order_id,
                medication_id,
                anomaly_type,
                quantity,
                received_qty,
                expected_unit_price,
                paid_unit_price,
                'Auto-detected supply anomaly',
                sim_ts
            )
        )
        actual_qty        = received_qty
        actual_paid_price = paid_unit_price
    else:
        actual_qty        = quantity
        actual_paid_price = expected_unit_price

    # 4) Update inventory levels
    cur.execute(
        """
        UPDATE inventory
        SET current_stock = current_stock + %s
        WHERE hospital_id = %s AND medication_id = %s;
        """,
        (actual_qty, hospital_id, medication_id)
    )

    # 5) Log the payment
    payment_amount = actual_qty * actual_paid_price
    cur.execute(
        """
        INSERT INTO payments
          (hospital_id, supplier_id, amount, simulation_timestamp, description)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (hospital_id, supplier_id, payment_amount, sim_ts, 'Inventory restock')
    )

    conn.commit()
    cur.close()
    conn.close()
