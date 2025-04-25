import psycopg2
from utils.db_config import get_db_connection

# All staff roles in the system
ROLES = [
    "Doctor",
    "RN",
    "Nurse Assistant",
    "Technician",
    "Pharmacist",
    "Admin",
    "Maintenance",
    "Security",
    "Therapist",
    "IT Support"
]

# Roles that are allowed to prescribe medications
PRESCRIBERS = {"Doctor", "RN", "Pharmacist"}

def insert_roles():
    conn = get_db_connection()
    cur = conn.cursor()

    for role in ROLES:
        can_prescribe = role in PRESCRIBERS
        cur.execute("""
            INSERT INTO roles (title, can_prescribe)
            VALUES (%s, %s)
            ON CONFLICT (title) DO NOTHING;
        """, (role, can_prescribe))

    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(ROLES)} roles inserted successfully.")

if __name__ == "__main__":
    insert_roles()
