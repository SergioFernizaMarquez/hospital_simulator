# data_generation/health_transition.py

import random
from datetime import datetime, timedelta
from typing import Optional, List
from utils.db_config import get_db_connection
from triage import PatientContext
from logging_and_billing import discharge_patient

def apply_health_transition(ctx: PatientContext, sim_time: datetime) -> Optional[PatientContext]:
    """
    Apply hourly Markov transition to patient:
      - Enforce automatic discharges (72h undiagnosed, 24h post-diagnosis)
      - Execute any due procedure events
      - Compute transition probabilities with multipliers
      - Randomly determine if patient is cured, dies, or stays admitted
      - Update logs and discharge if terminal
    """
    # 1) Automatic discharge rules
    if ctx.diagnosis_time is None and sim_time - ctx.admission_time >= timedelta(hours=72):
        ctx.outcome = 'Transferred'
        discharge_patient(ctx, sim_time)
        return None
    if ctx.diagnosis_time and sim_time - ctx.diagnosis_time >= timedelta(hours=24):
        ctx.outcome = 'Recovered'
        discharge_patient(ctx, sim_time)
        return None

    # 2) Execute any due procedure events
    for event_time, ev_type, ev_payload in list(ctx.event_queue):
        if ev_type in ('procedure', 'procedure_execution') and event_time <= sim_time:
            # extract procedure_id from payload
            proc_id = ev_payload if isinstance(ev_payload, int) else ev_payload.get('procedure_id')

            # 2a) Log the procedure text in daily logs
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE patient_daily_logs
                SET treatment = COALESCE(treatment || ',', '') || %s
                WHERE log_id = %s;
                """,
                (str(proc_id), ctx.log_id)
            )
            conn.commit()
            cur.close()
            conn.close()

            # 2b) Record it for billing
            if not hasattr(ctx, 'performed_procedures'):
                ctx.performed_procedures = []
            ctx.performed_procedures.append(proc_id)

            # 2c) Set diagnosis time if this was diagnostic
            if proc_id in ctx.condition_required_treatments and ctx.diagnosis_time is None:
                ctx.diagnosis_time = sim_time

            # 2d) Remove the event
            ctx.event_queue.remove((event_time, ev_type, ev_payload))

    # 3) Calculate cure/death probabilities
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT curability, mortality_per_hour FROM conditions WHERE condition_id = %s;",
        (ctx.condition_id,)
    )
    curability, mortality = cur.fetchone()
    cur.close()
    conn.close()

    total_req = len(ctx.condition_required_treatments) + len(ctx.condition_required_meds)
    eff_proc = sum(1 for t in getattr(ctx, 'performed_procedures', []) if t in ctx.condition_required_treatments)
    eff_med  = sum(1 for m in getattr(ctx, 'administered_meds', []) if m in ctx.condition_required_meds)
    eff = eff_proc + eff_med

    cure_mul  = 1 + (eff / total_req) if total_req else 1
    prob_cure = curability * cure_mul
    prob_death= mortality * (1 if eff == 0 else (1 - (eff / total_req)))

    r = random.random()
    if r < prob_cure:
        ctx.outcome = 'Recovered'
        discharge_patient(ctx, sim_time)
        return None
    if r < prob_cure + prob_death:
        ctx.outcome = 'Deceased'
        discharge_patient(ctx, sim_time)
        return None

    # 4) Patient remains admitted
    return ctx
