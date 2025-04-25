import random
from datetime import datetime
from typing import List
from utils.db_config import get_db_connection
from triage import admit_patient, PatientContext


def generate_arrivals(sim_time: datetime) -> List[PatientContext]:
    """
    For each hospital, generate new patient arrivals each hour and admit them.

    Arrival count per hospital = num_beds * random.uniform(0.01, 0.03)
    Each arriving patient is chosen at random from the patients table.
    Calls admit_patient(...) to perform triage and logging.

    Returns:
        List[PatientContext]: contexts for newly admitted patients.
    """
    contexts: List[PatientContext] = []
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all hospitals and their bed capacities
    cur.execute("SELECT hospital_id, num_beds FROM hospitals;")
    hospitals = cur.fetchall()  # List of tuples (hospital_id, num_beds)

    for hospital_id, num_beds in hospitals:
        # Determine number of arrivals: between 1% and 3% of beds
        pct = random.uniform(0.01, 0.03)
        count = max(1, int(num_beds * pct))

        # Fetch `count` random patients
        cur.execute(
            "SELECT patient_id FROM patients ORDER BY RANDOM() LIMIT %s;",
            (count,)
        )
        patient_rows = cur.fetchall()  # List of tuples [(patient_id,), ...]

        for (patient_id,) in patient_rows:
            # Admit and triage patient, obtaining a simulation context
            ctx = admit_patient(
                hospital_id=hospital_id,
                patient_id=patient_id,
                sim_time=sim_time
            )
            contexts.append(ctx)

    cur.close()
    conn.close()
    return contexts


if __name__ == "__main__":
    # Quick test: generate for current hour
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    new = generate_arrivals(now)
    print(f"Admitted {len(new)} patients at {now}.")
