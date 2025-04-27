# Hospital Simulation & Analytics: Summary of Work

In this file i'll go over the project explaining the design decisions, implementation steps, analytical techniques, and high level findings from our hospital operations simulation and subsequent data analysis.

---

## 1. Database Schema Design

- **Normalization & Extensibility**  
  Core entities (patients, employees, hospitals, conditions, symptoms, medications) each live in their own tables. Many to many relationships (e.g. `condition_medications`, `condition_procedures`) use join tables to maintain data integrity and allow easy extension.

- **Logging & Auditing**  
  Every event from admission, prescription, procedure, billing, payment, supply order, anomalis timestamped in its own table. This granularity supports both debugging and rich time-series analysis.

---

## 2. Data Generation & Anomaly Simulation

We built a set of Python modules under `data_generation/` to create realistic operational data:

1. **Arrival & Triage** (`generate_arrivals.py`, `triage.py`)  
   Patients receive randomized demographics, insurance, and conditions. Possible symptoms are pulled from the `symptoms` table, “present” symptoms are sampled, staff are assigned, and admissions logged.

2. **Treatment Execution** (`treatment.py`)  
   Medications are prescribed immediately; procedures are queued or executed. Each prescription hits the `prescriptions` table; procedures update the patient context.

3. **Health Transitions** (`health_transition.py`)  
   Based on administered meds/procedures, patients recover, transfer, or expire. Outcomes are written back to daily logs and generate billing entries in `billing`.

4. **Inventory & Supply** (`simulate_inventory.py`, `simulate_restock_inventory.py`)  
   Daily usage reduces stock reduced meds anywhere between 10% and 35%. When levels dip below threshold, we auto restock and inject supply anomalies, logged to `supply_anomalies`. Restock payments land in `payments`.

5. **Payroll Processing** (`simulate_payroll.py`)  
   Employee salaries run on schedule, recorded in `payroll_logs`. One midday run paid over 23000 employees.

**Anomaly Injection Strategies**  
- **Prescription**: Providers with integrity higher than 0 have a chance to overprescribe.  
- **Supply**: 5% of orders randomly are under/over deliver or under/over pay.

---

## 3. Simulation Execution

- **Full Simulator** (`simulator.py`)  
  Advances simulated time hourly: admits patients, schedules treatments, applies health transitions, bills, adjusts inventory, and runs payroll events. Over weeks, it logged over 70000 patient interactions.

- **Maintenance Simulator** (`maintenance_simulator.py`)  
  A lightweight daily runner: decrements inventory, restocks at 06:00, processes payroll at 12:00 without replaying patient traffic.

---

## 4. Analysis & Research

Using CSV exports of every table, we created Jupyter notebooks for EDA, visualization, forecasting, and fraud detection:

1. **Cost & Demand Metrics**  
   - **Daily & Monthly Trends**: Side by side restock vs. payroll vs. revenue shows dynamic forecasting can cut ordering costs by over 15%.  
   - **Medication Demand vs. Fulfillment**: Visualized top daily demand meds, spotting peaks during admission surges.

2. **Inventory Ordering Strategies**  
   - **Flat 20% Cushion** vs. **Dynamic Forecast** (linear regression + ±RMSE) over 14 days dynamic saved over 18% across all meds.

3. **Fraud Detection**  
   - **Prescription Anomalies**: Top 10 overprescribers by count and cost; 1254 anomalies cost with over $30000 in lost revenue.  
   - **Supply Anomalies**: Identified meds with frequent under/over deliveries and payment discrepancies.

4. **Patient Outcomes**  
   - **Overall**: About 85% recovered, 10% were transferred and 5% were deceased.  
   - **By Hospital**: Significant mortality variance highlighted facilities for deeper quality review.  
   - **By Condition & Demographics**: Stacked charts by diagnosis, race, age group guided targeted care improvements.

5. **Revenue Forecasting**  
   - Linear regression on monthly revenue, forecasting 12 months with widening ±RMSE·√horizon intervals.

---

## 5. Techniques & Tools Used

- **Python** for simulation and analysis  
- **PostgreSQL** for robust event storage and referential integrity  
- **pandas & matplotlib** for data wrangling and visualization  
- **scikit-learn** for linear regression forecasting  
- **In-memory event queues** to schedule future procedures and billing

---

## 6. High-Level Findings

1. **Dynamic ordering** saved over 18% on medication restock costs.  
2. **Overprescribing** Approximately 1.5% of prescriptions are overprescriptions.  
3. **Outcome variability** across hospitals and demographics indicates equity and quality gaps.  
4. **Forecasting with widening uncertainty** offers actionable planning windows for revenue and inventory.

---

This project shows an end to end pipeline from schema design and event simulation to advanced analytics and forecasting offering a template for complex operational data workflows in healthcare and beyond.
