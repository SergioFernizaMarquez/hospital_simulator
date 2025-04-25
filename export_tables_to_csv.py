# export_tables_to_csv.py

import os
import pandas as pd
from data_generation.utils.db_config import get_db_connection

# List all your schema tables here
tables = [
    "hospitals", "roles", "employees", "employee_hospital",
    "patients", "patient_daily_logs", "medications", "prescriptions",
    "insurance_providers", "procedures", "billing", "billing_procedures",
    "inventory", "suppliers", "supplier_medications", "supply_orders",
    "supply_order_items", "payments", "payroll_logs", "supply_anomalies",
    "prescription_anomalies", "high_risk_patients", "symptoms", "conditions",
    "condition_procedures", "condition_medications", "payroll_schedule"
]

# Create an output directory named "csv_exports" in your project root
output_dir = os.path.join(os.getcwd(), "csv_exports")
os.makedirs(output_dir, exist_ok=True)

# Connect to PostgreSQL
conn = get_db_connection()

for table in tables:
    # Read the entire table into a DataFrame
    df = pd.read_sql_query(f"SELECT * FROM {table};", conn)
    # Write to CSV (no index column)
    csv_path = os.path.join(output_dir, f"{table}.csv")
    df.to_csv(csv_path, index=False)
    print(f"Exported {table} → {csv_path}")

conn.close()


