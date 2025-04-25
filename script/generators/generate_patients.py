import random
import psycopg2
from faker import Faker
from utils.db_config import get_db_connection

fake = Faker()

# Blood types with realistic population distribution (approximate)
BLOOD_TYPES = [
    ("O+", 37), ("A+", 36), ("B+", 9), ("O-", 6), 
    ("A-", 6), ("AB+", 3), ("B-", 2), ("AB-", 1)
]

# Behavior flags – each has an independent 2% chance
BEHAVIOR_FLAGS = ["drug_seeker", "violent", "suicidal", "drug_user", "inappropriate"]

EYE_COLORS = ["Brown", "Blue", "Green", "Hazel", "Gray", "Amber"]
HAIR_COLORS = ["Black", "Brown", "Blonde", "Red", "Gray", "White"]
RACES = ["White", "Black", "Hispanic", "Asian", "Native American", "Pacific Islander", "Other"]

PRE_EXISTING_CONDITIONS = [
    "Hypertension", "Diabetes", "Asthma", "COPD", "Cancer",
    "Heart Disease", "HIV/AIDS", "Sickle Cell", "Obesity", 
    "Arthritis", "Epilepsy", "Depression", "Kidney Disease"
]

# Generate 1000 first and 1000 last names to reuse
FIRST_NAMES = list({fake.first_name() for _ in range(2000)})[:1000]
LAST_NAMES = list({fake.last_name() for _ in range(2000)})[:1000]

def pick_weighted_blood_type():
    pool = []
    for blood_type, freq in BLOOD_TYPES:
        pool.extend([blood_type] * freq)
    return random.choice(pool)

def generate_patient():
    full_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    age = random.randint(0, 100)
    gender = random.choice(["Male", "Female", "Other"])
    bmi = round(random.uniform(15.0, 40.0), 1)
    weight = round(random.uniform(40, 150), 1)  # kg
    height = round(random.uniform(140, 210), 1)  # cm
    eye_color = random.choice(EYE_COLORS)
    hair_color = random.choice(HAIR_COLORS)
    race = random.choice(RACES)
    blood_type = pick_weighted_blood_type()

    # 33% chance of pre-existing condition
    pre_existing_condition = random.choice(PRE_EXISTING_CONDITIONS) if random.random() < 0.33 else None

    # Each flag has a 2% chance of being True
    flags = {flag: random.random() < 0.02 for flag in BEHAVIOR_FLAGS}

    return (
        full_name, age, gender, blood_type, pre_existing_condition, bmi, weight,
        height, eye_color, hair_color, race,
        flags["drug_seeker"], flags["violent"], flags["suicidal"],
        flags["drug_user"], flags["inappropriate"]
    )

def insert_patients(batch_size=1000, total=100000):
    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0

    insert_query = """
        INSERT INTO patients (
            full_name, age, gender, blood_type, pre_existing_conditions, bmi, weight,
            height, eye_color, hair_color, race,
            drug_seeker, violent, suicidal, drug_user, inappropriate
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    while inserted < total:
        batch = [generate_patient() for _ in range(min(batch_size, total - inserted))]
        cur.executemany(insert_query, batch)
        conn.commit()
        inserted += len(batch)
        print(f"{inserted} patients inserted...")

    cur.close()
    conn.close()
    print("All patients inserted successfully.")

if __name__ == "__main__":
    insert_patients()
