import random
import psycopg2
from faker import Faker
from utils.db_config import get_db_connection

fake = Faker()

def fetch_medication_ids():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT medication_id FROM medications;")
    meds = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return meds

def generate_suppliers(n=30):
    suppliers = []
    for _ in range(n):
        name = fake.company() + " Pharmaceuticals"
        contact = fake.name()
        email = fake.company_email()
        phone = fake.phone_number()
        address = fake.address().replace("\n", ", ")
        suppliers.append((name, contact, phone, email, address))
    return suppliers

def insert_suppliers(suppliers):
    conn = get_db_connection()
    cur = conn.cursor()
    supplier_ids = []
    for supplier in suppliers:
        cur.execute("""
            INSERT INTO suppliers (name, contact_name, phone, email, address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING supplier_id;
        """, supplier)
        supplier_ids.append(cur.fetchone()[0])
    conn.commit()
    cur.close()
    conn.close()
    return supplier_ids

def assign_supplier_medications(supplier_ids, medication_ids):
    conn = get_db_connection()
    cur = conn.cursor()
    assigned_pairs = set()
    for supplier_id in supplier_ids:
        meds = random.sample(medication_ids, k=random.randint(10, 50))
        for med_id in meds:
            if (supplier_id, med_id) not in assigned_pairs:
                assigned_pairs.add((supplier_id, med_id))
                cur.execute("""
                    INSERT INTO supplier_medications (supplier_id, medication_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                """, (supplier_id, med_id))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Assigned medications to {len(supplier_ids)} suppliers.")

if __name__ == "__main__":
    medication_ids = fetch_medication_ids()
    suppliers = generate_suppliers(n=30)
    supplier_ids = insert_suppliers(suppliers)
    assign_supplier_medications(supplier_ids, medication_ids)
