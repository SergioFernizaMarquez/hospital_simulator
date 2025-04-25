import random
import psycopg2
from faker import Faker
from utils.db_config import get_db_connection
from utils.encryption import encrypt_data

fake = Faker()

# Staff ratios based on WHO + U.S. standards
STAFF_RATIOS = {
    "Doctor": (1/5),
    "RN": (1/1.5),
    "Nurse Assistant": (1/4.5),
    "Technician": (1/15),
    "Pharmacist": (1/75),
    "Admin": (1/2.5),
    "Maintenance": (1/7.5),
    "Security": (1/30),
    "Therapist": (1/15),
    "IT Support": (1/30)
}

# 12 most common doctor specialties
SPECIALTIES = [
    "Internal Medicine", "Family Medicine", "Pediatrics", "Emergency Medicine",
    "Psychiatry", "Anesthesiology", "General Surgery", "Cardiology",
    "Orthopedics", "Dermatology", "Obstetrics and Gynecology", "Neurology"
]

# Load 500 unique first and last names
FIRST_NAMES = list({fake.first_name() for _ in range(1000)})[:500]
LAST_NAMES = list({fake.last_name() for _ in range(1000)})[:500]

def generate_staff_for_hospital(hospital_id, num_beds):
    employees = []
    for role, ratio in STAFF_RATIOS.items():
        count = max(1, int(num_beds * ratio))
        for _ in range(count):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            full_name = f"{first} {last}"
            specialty = random.choice(SPECIALTIES) if role == "Doctor" else None
            salary = round(random.uniform(45000, 300000), 2)
            payroll_num = encrypt_data(fake.bothify(text='PAYROLL-####-####'))
            ssn = encrypt_data(fake.ssn())
            phone = fake.phone_number()

            # 5% get random integrity score, 95% set to 0
            integrity_score = round(random.uniform(0, 1), 2) if random.random() < 0.05 else 0

            employees.append((
                full_name, role, specialty, salary,
                payroll_num, ssn, phone, integrity_score, hospital_id
            ))
    return employees

def insert_employees(employees):
    conn = get_db_connection()
    cur = conn.cursor()

    # Insert into roles table if not already present
    role_titles = set(e[1] for e in employees)
    for title in role_titles:
        cur.execute("""
            INSERT INTO roles (title, can_prescribe)
            VALUES (%s, %s)
            ON CONFLICT (title) DO NOTHING;
        """, (title, title in ["Doctor", "RN", "Pharmacist"]))

    # Insert employees and map to hospitals
    for emp in employees:
        cur.execute("""
            INSERT INTO employees (full_name, role_id, specialty, salary, payroll_num, ssn, phone_number, integrity_score)
            VALUES (
                %s,
                (SELECT role_id FROM roles WHERE title = %s),
                %s, %s, %s, %s, %s, %s
            ) RETURNING employee_id;
        """, emp[:8])
        employee_id = cur.fetchone()[0]

        # Associate with hospital
        cur.execute("""
            INSERT INTO employee_hospital (employee_id, hospital_id)
            VALUES (%s, %s);
        """, (employee_id, emp[8]))

    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(employees)} employees inserted successfully.")

def fetch_hospitals():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT hospital_id, num_beds FROM hospitals;")
    hospitals = cur.fetchall()
    cur.close()
    conn.close()
    return hospitals

if __name__ == "__main__":
    all_employees = []
    for hospital_id, num_beds in fetch_hospitals():
        hospital_emps = generate_staff_for_hospital(hospital_id, num_beds)
        all_employees.extend(hospital_emps)

    insert_employees(all_employees)
