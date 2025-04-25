import random
import sys
import psycopg2
from faker import Faker
from utils.db_config import get_db_connection

fake = Faker()

# 25 unique hospital names
UNIQUE_HOSPITAL_NAMES = [
    "Aurora Medical Center", "Beacon Hill Hospital", "Blue Ridge Medical",
    "Canyon Creek Hospital", "Clearview Regional", "Crestwood Health System",
    "Evergreen Valley Hospital", "Fairview Medical Plaza", "Golden State Hospital",
    "Harmony General", "Highland Mercy", "Lakeside Medical", "Maplewood Health Center",
    "Midland Memorial", "Northshore Hospital", "Oak Hill Regional", "Pinecrest Hospital",
    "Riverside Medical", "Sierra Vista Medical Center", "Silverlake Hospital",
    "Summit View Hospital", "Sunset Heights Medical", "Tranquil Valley Health",
    "Unity Medical Network", "Willowbrook Medical"
]

def generate_hospital_data(names):
    hospitals = []
    for name in names:
        location = fake.address().replace("\n", ", ")
        # Use Gaussian distribution for realistic bed sizes (mean=500, std=300)
        num_beds = int(random.gauss(mu=500, sigma=300))
        num_beds = max(100, min(num_beds, 1500))  # Clamp to [100, 1500]
        hospitals.append((name, location, num_beds))
    return hospitals

def insert_hospitals(hospitals):
    conn = get_db_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO hospitals (name, location, num_beds)
        VALUES (%s, %s, %s);
    """
    cur.executemany(query, hospitals)
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(hospitals)} hospitals inserted successfully.")

if __name__ == "__main__":
    # Optional: allow dynamic count via command line
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 25

    if n > len(UNIQUE_HOSPITAL_NAMES):
        print(f"Only {len(UNIQUE_HOSPITAL_NAMES)} unique hospital names available.")
        n = len(UNIQUE_HOSPITAL_NAMES)

    selected_names = UNIQUE_HOSPITAL_NAMES[:n]
    hospital_data = generate_hospital_data(selected_names)
    insert_hospitals(hospital_data)
