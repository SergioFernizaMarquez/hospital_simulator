import random
import psycopg2
import json
from utils.db_config import get_db_connection

def fetch_medications():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT medication_id FROM medications;")
    meds = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return meds

def fetch_procedures():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT procedure_id FROM procedures;")
    procs = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return procs

def generate_insurance_providers(n=10):
    meds = fetch_medications()
    procs = fetch_procedures()

    providers = []
    for _ in range(n):
        name = f"{random.choice(['Shield', 'Care', 'Health', 'Prime', 'Unity'])} {random.choice(['Plus', 'Trust', 'First', 'Secure', 'Flex'])}"
        deductible = random.randint(500, 3000)
        premium = round(random.uniform(200, 800), 2)
        oop_max = random.randint(3000, 15000)

        # Copay for a subset of medications
        copay_ids = random.sample(meds, k=random.randint(10, 30))
        copay = {str(med_id): random.randint(25, 100) for med_id in copay_ids}

        # Coinsurance for a subset of procedures
        coins_ids = random.sample(procs, k=random.randint(15, 40))
        coinsurance = {str(proc_id): round(random.uniform(0.75, 1.0), 2) for proc_id in coins_ids}

        providers.append((name, deductible, premium, oop_max, json.dumps(copay), json.dumps(coinsurance)))
    
    return providers

def insert_insurance_providers(providers):
    conn = get_db_connection()
    cur = conn.cursor()
    for p in providers:
        cur.execute("""
            INSERT INTO insurance_providers (
                name, deductible, premium, out_of_pocket_maximum,
                copay, coinsurance
            ) VALUES (%s, %s, %s, %s, %s, %s);
        """, p)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {len(providers)} insurance providers.")

if __name__ == "__main__":
    insurance = generate_insurance_providers(n=15)
    insert_insurance_providers(insurance)
