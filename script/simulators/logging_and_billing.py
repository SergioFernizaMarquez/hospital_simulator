# data_generation/logging_and_billing.py

import psycopg2
from datetime import datetime
from typing import Any
from utils.db_config import get_db_connection

def discharge_patient(ctx: Any, sim_time: datetime) -> None:
    """
    Finalize a patient's stay: update logs, calculate billing, and record charges.

    Args:
        ctx: PatientContext containing at least:
             patient_id, hospital_id, log_id,
             administered_meds (List[int]),
             performed_procedures (List[int]),
             doctor_id, nurse_id,
             diagnosis_time, insurance_id, outcome
        sim_time: Timestamp of discharge
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Update patient_daily_logs with outcome, diagnosis, treatment, prescription
    diagnosis_txt    = ctx.diagnosis_time.isoformat() if getattr(ctx, 'diagnosis_time', None) else None
    treatment_txt    = ','.join(str(pid) for pid in getattr(ctx, 'performed_procedures', [])) or None
    prescription_txt = ','.join(str(mid) for mid in getattr(ctx, 'administered_meds', [])) or None

    cur.execute(
        """
        UPDATE patient_daily_logs
        SET outcome      = %s,
            doctor_id    = %s,
            nurse_id     = %s,
            diagnosis    = %s,
            treatment    = %s,
            prescription = %s,
            simulation_timestamp = %s
        WHERE log_id = %s;
        """,
        (
            ctx.outcome,
            ctx.doctor_id,
            ctx.nurse_id,
            diagnosis_txt,
            treatment_txt,
            prescription_txt,
            sim_time,
            ctx.log_id
        )
    )

    # 2) Sum all medication costs for this patient
    cur.execute(
        """
        SELECT COALESCE(SUM(p.quantity_prescribed * m.unit_cost), 0)
        FROM prescriptions p
        JOIN medications m ON p.medication_id = m.medication_id
        WHERE p.patient_id = %s;
        """,
        (ctx.patient_id,)
    )
    med_cost = cur.fetchone()[0] or 0

    # 3) Sum all procedure costs for performed procedures
    if hasattr(ctx, 'performed_procedures') and ctx.performed_procedures:
        cur.execute(
            """
            SELECT COALESCE(SUM(cost), 0)
            FROM procedures
            WHERE procedure_id = ANY(%s);
            """,
            (ctx.performed_procedures,)
        )
        proc_cost = cur.fetchone()[0] or 0
    else:
        proc_cost = 0

    total_cost = med_cost + proc_cost

    # 4) Insert a new bill record
    cur.execute(
        """
        INSERT INTO billing (patient_id, hospital_id, total_cost, insurance_id)
        VALUES (%s, %s, %s, %s)
        RETURNING bill_id;
        """,
        (
            ctx.patient_id,
            ctx.hospital_id,
            total_cost,
            getattr(ctx, 'insurance_id', None)
        )
    )
    bill_id = cur.fetchone()[0]

    # 5) Link each procedure to the bill
    if hasattr(ctx, 'performed_procedures') and ctx.performed_procedures:
        for pid in ctx.performed_procedures:
            cur.execute(
                """
                INSERT INTO billing_procedures (bill_id, procedure_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING;
                """,
                (bill_id, pid)
            )

    conn.commit()
    cur.close()
    conn.close()

    print(f"[Discharge] Patient {ctx.patient_id} billed ${total_cost:.2f} (Bill ID: {bill_id})")
