# data_generation/simulator.py

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from generate_arrivals import generate_arrivals
from treatment import schedule_initial_treatments
from health_transition import apply_health_transition
from simulate_inventory import run_daily_inventory_check
from simulate_payroll import run_hourly_payroll

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def simulate_hospital(start_time: datetime, total_hours: int):
    """
    Main simulation loop:
      1. Generate new arrivals
      2. Immediately schedule & execute treatments (meds + procedures)
      3. Run daily inventory check at 06:00
      4. Process hourly payroll
      5. Apply health transitions and discharge patients
    """
    sim_time = start_time
    end_time = start_time + timedelta(hours=total_hours)

    active_patients: List = []

    while sim_time < end_time:
        logging.info(f"-- Simulation hour: {sim_time} --")

        # 1. Arrivals
        new_contexts = generate_arrivals(sim_time)
        active_patients.extend(new_contexts)
        logging.info(f"Admitted {len(new_contexts)} new patients.")

        # 2. Immediate treatments & procedures
        for ctx in new_contexts:
            schedule_initial_treatments(ctx, sim_time)

        # 3. Daily inventory at 06:00
        if sim_time.hour == 6:
            restocked = run_daily_inventory_check(sim_time)
            if restocked:
                logging.info(f"Restocked {restocked} items at 06:00.")

        # 4. Hourly payroll
        paid = run_hourly_payroll(sim_time)
        if paid:
            logging.info(f"Processed payroll for {paid} employees.")

        # 5. Health transitions & discharge
        for ctx in list(active_patients):
            result = apply_health_transition(ctx, sim_time)
            if result is None:
                active_patients.remove(ctx)
                logging.info(f"Patient {ctx.patient_id} discharged with outcome '{ctx.outcome}'.")

        # Advance time
        sim_time += timedelta(hours=1)

    logging.info("Simulation complete.")


if __name__ == '__main__':
    # Run e.g. 1 year (8760 hours)
    start = datetime.utcnow()
    total = 24 * 365
    simulate_hospital(start, total)
