# data_generation/triage.py

import random
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from utils.db_config import get_db_connection

# configure simple console logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class PatientContext:
    """
    Holds context information for a patient during simulation.
    (attributes as before…)
    """
    def __init__(
        self,
        patient_id: int,
        hospital_id: int,
        admission_time: datetime,
        condition_id: int,
        condition_required_treatments: List[int],
        condition_required_meds: List[int],
        condition_symptoms: List[int],
        present_symptoms: List[Dict[str, Any]],
        doctor_id: int,
        nurse_id: int,
        age: int,
        race: str,
        pre_existing_conditions: Optional[str],
        log_id: int,
        insurance_id: Optional[int]
    ):
        self.patient_id = patient_id
        self.hospital_id = hospital_id
        self.admission_time = admission_time
        self.diagnosis_time: Optional[datetime] = None

        self.condition_id = condition_id
        self.condition_required_treatments = condition_required_treatments
        self.condition_required_meds = condition_required_meds
        self.condition_symptoms = condition_symptoms

        self.present_symptoms = present_symptoms

        self.doctor_id = doctor_id
        self.nurse_id = nurse_id

        self.age = age
        self.race = race
        self.pre_existing_conditions = pre_existing_conditions

        self.log_id = log_id
        self.insurance_id = insurance_id

        # for scheduling & tracking during simulation
        self.event_queue: List[tuple] = []
        self.administered_meds: List[int] = []
        self.performed_procedures: List[int] = []


def admit_patient(hospital_id: int, patient_id: int, sim_time: datetime) -> PatientContext:
    """
    Admit a patient, perform triage, and insert an initial daily‐log.
    Returns a PatientContext for use in the simulation loop.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Fetch demographics
    cur.execute(
        """
        SELECT age, race, pre_existing_conditions
        FROM patients
        WHERE patient_id = %s;
        """,
        (patient_id,)
    )
    age, race, pre_existing_conditions = cur.fetchone()
    logging.info(f"[ADMIT] Patient {patient_id}: age={age}, race={race}")

    # 2) Assign a random insurance provider
    cur.execute(
        "SELECT insurance_id FROM insurance_providers ORDER BY RANDOM() LIMIT 1;"
    )
    insurance_id = cur.fetchone()[0]
    logging.info(f"[ADMIT] Patient {patient_id}: insurance_id={insurance_id}")

    # 3) Pick random condition & raw_symptoms
    cur.execute(
        "SELECT condition_id, possible_symptoms FROM conditions ORDER BY RANDOM() LIMIT 1;"
    )
    condition_id, raw_symptoms = cur.fetchone()
    possible_symptoms = json.loads(raw_symptoms) if isinstance(raw_symptoms, str) else (raw_symptoms or [])
    logging.info(f"[ADMIT] Patient {patient_id}: condition_id={condition_id}, possible_symptoms={len(possible_symptoms)}")

    # 4) Build symptom_entries
    symptom_entries: List[Dict[str, Any]] = []
    for item in possible_symptoms:
        try:
            sid = int(item) if not isinstance(item, dict) else int(item.get("symptom_id", item.get("id")))
        except:
            continue
        cur.execute(
            """
            SELECT severity, procedure_id, medication_id, quantity
            FROM symptoms
            WHERE symptom_id = %s;
            """,
            (sid,)
        )
        row = cur.fetchone()
        if not row:
            continue
        severity, proc_id, med_id, qty = row
        symptom_entries.append({
            "symptom_id": sid,
            "severity": severity,
            "procedure_id": proc_id,
            "medication_id": med_id,
            "quantity": qty
        })
    logging.info(f"[ADMIT] Patient {patient_id}: fetched metadata for {len(symptom_entries)} symptoms")

    # 5) Fetch required treatments & meds
    cur.execute(
        "SELECT procedure_id FROM condition_procedures WHERE condition_id = %s;",
        (condition_id,)
    )
    condition_required_treatments = [r[0] for r in cur.fetchall()]
    cur.execute(
        "SELECT medication_id FROM condition_medications WHERE condition_id = %s;",
        (condition_id,)
    )
    condition_required_meds = [r[0] for r in cur.fetchall()]

    # 6) Handle cases with no symptom metadata
    if not symptom_entries:
        # force a fallback symptom so patient always gets care
        fallback_proc = condition_required_treatments[0] if condition_required_treatments else None
        fallback_med  = condition_required_meds[0]       if condition_required_meds else None
        symptom_entries.append({
            "symptom_id": -1,
            "severity": 1,
            "procedure_id": fallback_proc,
            "medication_id": fallback_med,
            "quantity": 1
        })
        logging.info(f"[ADMIT] Patient {patient_id}: forced fallback symptom (proc={fallback_proc}, med={fallback_med})")

    # 7) Randomly select which symptoms are present
    present_symptoms: List[Dict[str, Any]] = []
    for entry in symptom_entries:
        if random.random() < 0.5:
            present_symptoms.append(entry)
    # ensure at least one
    if not present_symptoms:
        chosen = random.choice(symptom_entries)
        present_symptoms.append(chosen)
        logging.info(f"[ADMIT] Patient {patient_id}: forced present_symptom {chosen}")

    logging.info(f"[ADMIT] Patient {patient_id}: present_symptoms={len(present_symptoms)}")

    # 8) Assign doctor
    cur.execute(
        """
        SELECT e.employee_id
        FROM employees e
        JOIN roles r ON e.role_id = r.role_id
        JOIN employee_hospital eh ON e.employee_id = eh.employee_id
        WHERE eh.hospital_id = %s AND r.title = 'Doctor'
        ORDER BY RANDOM() LIMIT 1;
        """,
        (hospital_id,)
    )
    doctor_id = cur.fetchone()[0]

    # 9) Assign nurse
    cur.execute(
        """
        SELECT e.employee_id
        FROM employees e
        JOIN roles r ON e.role_id = r.role_id
        JOIN employee_hospital eh ON e.employee_id = eh.employee_id
        WHERE eh.hospital_id = %s AND r.title = 'RN'
        ORDER BY RANDOM() LIMIT 1;
        """,
        (hospital_id,)
    )
    nurse_id = cur.fetchone()[0]

    # 10) Insert initial daily log
    cur.execute(
        """
        INSERT INTO patient_daily_logs
          (patient_id, hospital_id, simulation_timestamp,
           diagnosis, treatment, prescription,
           outcome, doctor_id, nurse_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING log_id;
        """,
        (
            patient_id, hospital_id, sim_time,
            None, None, None,
            'Admitted', doctor_id, nurse_id
        )
    )
    log_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"[ADMIT] Patient {patient_id}: log_id={log_id}")

    # 11) Return context
    return PatientContext(
        patient_id,
        hospital_id,
        sim_time,
        condition_id,
        condition_required_treatments,
        condition_required_meds,
        [e["symptom_id"] for e in symptom_entries],
        present_symptoms,
        doctor_id,
        nurse_id,
        age,
        race,
        pre_existing_conditions,
        log_id,
        insurance_id
    )
