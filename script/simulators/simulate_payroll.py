# data_generation/simulate_payroll.py

from datetime import timedelta
import psycopg2
from utils.db_config import get_db_connection

# Number of pay periods per year for bi-weekly salaried staff
PAY_PERIODS_PER_YEAR = 26

def run_hourly_payroll(sim_time):
    """
    Issue payroll for any salaried employee whose next_due <= sim_time.
    Logs a fixed bi-weekly payout based on annual salary.
    Returns count of payments made.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1) Fetch and lock due employees
    cur.execute("""
        SELECT p.employee_id, p.salary, s.next_due, s.frequency_h
        FROM employees p
        JOIN payroll_schedule s
          ON p.employee_id = s.employee_id
        WHERE s.next_due <= %s
        FOR UPDATE
    """, (sim_time,))
    due_list = cur.fetchall()

    # 2) Issue payments and update schedule
    for emp_id, annual_salary, due_ts, freq_h in due_list:
        # Salaried: fixed pay = annual_salary / PAY_PERIODS_PER_YEAR
        gross = annual_salary / PAY_PERIODS_PER_YEAR
        # Simple flat deduction example: 20%
        net = float(gross) * 0.80

        # Insert into payroll_logs
        cur.execute("""
            INSERT INTO payroll_logs
              (employee_id, hospital_id, simulation_timestamp,
               gross_salary, net_salary, notes)
            VALUES (%s, NULL, %s, %s, %s, %s)
        """, (emp_id, sim_time, gross, net, "Bi-weekly salaried payout"))

        # Advance schedule
        new_due = due_ts + timedelta(hours=freq_h)
        cur.execute("""
            UPDATE payroll_schedule
            SET last_payment = %s,
                next_due = %s
            WHERE employee_id = %s
        """, (sim_time, new_due, emp_id))

    conn.commit()
    cur.close()
    conn.close()
    return len(due_list)

if __name__ == "__main__":
    from datetime import datetime
    count = run_hourly_payroll(datetime.utcnow())
    print(f"Issued {count} salaries at {datetime.utcnow()}")
