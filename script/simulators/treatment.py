# data_generation/treatment.py

import random
import logging
from datetime import timedelta
from typing import Any
from utils.db_config import get_db_connection
from triage import PatientContext

# configure simple console logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def schedule_initial_treatments(ctx: PatientContext, sim_time) -> None:
    """
    For each symptom:
      1) Immediately prescribe symptom medications, with anomaly logic
      2) Immediately execute any procedure for that symptom
         – if it’s part of the condition’s required treatments, mark diagnosis
         – then auto‐prescribe all condition_required_meds
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # ensure lists exist
    ctx.administered_meds    = getattr(ctx, 'administered_meds', [])
    ctx.performed_procedures = getattr(ctx, 'performed_procedures', [])

    for symptom in ctx.present_symptoms:
        proc_id = symptom.get('procedure_id')
        med_id  = symptom.get('medication_id')
        std_qty = symptom.get('quantity', 0)

        # ——————— 1) Prescribe med with anomaly ———————
        if med_id and std_qty > 0:
            # pick prescribing employee (always doctor for simplicity)
            prescriber = ctx.doctor_id

            # fetch integrity score
            cur.execute(
                "SELECT integrity_score FROM employees WHERE employee_id = %s;",
                (prescriber,)
            )
            integrity = cur.fetchone()[0] or 0.0

            # determine final quantity
            if random.random() < integrity:
                # anomaly: overprescribe double
                pres_qty = std_qty * 2
                anomaly = True
            else:
                pres_qty = std_qty
                anomaly = False

            # insert prescription and get its id
            cur.execute(
                """
                INSERT INTO prescriptions
                  (patient_id, employee_id, medication_id, quantity_prescribed, simulation_timestamp, hospital_id)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING prescription_id;
                """,
                (ctx.patient_id, prescriber, med_id, pres_qty, sim_time, ctx.hospital_id)
            )
            pres_id = cur.fetchone()[0]
            ctx.administered_meds.append(med_id)
            logging.info(f"[TREAT] Patient {ctx.patient_id}: prescribed med {med_id} qty={pres_qty} (std={std_qty})")

            if anomaly:
                # record an overprescription anomaly
                cur.execute(
                    """
                    INSERT INTO prescription_anomalies
                      (prescription_id, employee_id, medication_id,
                       anomaly_type, prescribed_quantity, standard_quantity,
                       notes, simulation_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        pres_id, prescriber, med_id,
                        'overprescribe', pres_qty, std_qty,
                        None, sim_time
                    )
                )
                logging.info(f"[ANOMALY] Patient {ctx.patient_id}: anomaly recorded for presc {pres_id}")

        # ——————— 2) Execute procedure immediately ———————
        if proc_id:
            # log procedure in daily‐log
            cur.execute(
                """
                UPDATE patient_daily_logs
                SET treatment = COALESCE(treatment || ',', '') || %s
                WHERE log_id = %s;
                """,
                (str(proc_id), ctx.log_id)
            )
            ctx.performed_procedures.append(proc_id)
            logging.info(f"[TREAT] Patient {ctx.patient_id}: executed procedure {proc_id}")

            # if this was diagnostic, mark diagnosis and auto‐prescribe condition meds
            if proc_id in ctx.condition_required_treatments and ctx.diagnosis_time is None:
                ctx.diagnosis_time = sim_time
                logging.info(f"[TREAT] Patient {ctx.patient_id}: diagnosed at {sim_time}")

                # auto‐prescribe all condition meds
                for cond_med in ctx.condition_required_meds:
                    # standard qty = 1 for simplicity
                    cur.execute(
                        """
                        INSERT INTO prescriptions
                          (patient_id, employee_id, medication_id, quantity_prescribed, simulation_timestamp, hospital_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING prescription_id;
                        """,
                        (ctx.patient_id, ctx.doctor_id, cond_med, 1, sim_time, ctx.hospital_id)
                    )
                    cond_pres_id = cur.fetchone()[0]
                    ctx.administered_meds.append(cond_med)
                    logging.info(f"[TREAT] Patient {ctx.patient_id}: auto‐prescribed condition med {cond_med}")

    conn.commit()
    cur.close()
    conn.close()
