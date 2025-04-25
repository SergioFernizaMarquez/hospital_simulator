-- Table: hospitals
CREATE TABLE hospitals (
    hospital_id SERIAL PRIMARY KEY,
    name TEXT,
    location TEXT,
    num_beds INTEGER
);

-- Table: roles
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    title TEXT UNIQUE,
    can_prescribe BOOLEAN DEFAULT FALSE
);

-- Table: employees
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    role_id INTEGER REFERENCES roles(role_id) ON DELETE SET NULL,
    specialty TEXT,
    salary NUMERIC,
    payroll_num BYTEA,
    ssn BYTEA,
    phone_number TEXT,
    integrity_score NUMERIC CHECK (integrity_score >= 0 AND integrity_score <= 1)
);

CREATE INDEX idx_employees_role_id ON employees(role_id);

-- Table: employee_hospital
CREATE TABLE employee_hospital (
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    PRIMARY KEY (employee_id, hospital_id)
);

-- Table: patients
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    full_name TEXT,
    age INTEGER,
    gender TEXT,
    blood_type TEXT,
    pre_existing_conditions TEXT,
    bmi NUMERIC,
    weight NUMERIC,
    height NUMERIC,
    eye_color TEXT,
    hair_color TEXT,
    race TEXT,
    drug_seeker BOOLEAN,
    violent BOOLEAN,
    suicidal BOOLEAN,
    drug_user BOOLEAN,
    inappropriate BOOLEAN
);


CREATE TABLE patient_daily_logs (
    log_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL,
    simulation_timestamp TIMESTAMP,
    diagnosis TEXT,
    treatment TEXT,
    prescription TEXT,
    outcome TEXT, -- e.g. 'Recovered', 'Admitted', 'Transferred', 'Deceased'
    doctor_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    nurse_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL
);

-- Table: medications
CREATE TABLE medications (
    medication_id SERIAL PRIMARY KEY,
    name TEXT,
    category TEXT,
    unit_cost NUMERIC,
    prescription_level TEXT
);

-- Table: prescriptions
CREATE TABLE prescriptions (
    prescription_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE SET NULL,
    quantity_prescribed INTEGER,
    simulation_timestamp TIMESTAMP,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL
);

CREATE INDEX idx_prescriptions_patient ON prescriptions(patient_id);
CREATE INDEX idx_prescriptions_sim_time ON prescriptions(simulation_timestamp);

-- Table: insurance_providers
CREATE TABLE insurance_providers (
    insurance_id SERIAL PRIMARY KEY,
    name TEXT,
    deductible NUMERIC,
    premium NUMERIC,
    copay JSONB,
    coinsurance JSONB,
    out_of_pocket_maximum NUMERIC
);

-- Table: procedures
CREATE TABLE procedures (
    procedure_id SERIAL PRIMARY KEY,
    name TEXT,
    type TEXT,
    cost NUMERIC
);

-- Table: billing
CREATE TABLE billing (
    bill_id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE SET NULL,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL,
    total_cost NUMERIC,
    insurance_id INTEGER REFERENCES insurance_providers(insurance_id) ON DELETE SET NULL
);

-- Table: billing_procedures
CREATE TABLE billing_procedures (
    bill_id INTEGER REFERENCES billing(bill_id) ON DELETE CASCADE,
    procedure_id INTEGER REFERENCES procedures(procedure_id) ON DELETE CASCADE,
    PRIMARY KEY (bill_id, procedure_id)
);

-- Table: inventory
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE CASCADE,
    current_stock INTEGER,
    minimum_stock INTEGER
);

CREATE INDEX idx_inventory_hospital_med ON inventory(hospital_id, medication_id);

-- Table: suppliers
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    name TEXT,
    contact_name TEXT,
    phone TEXT,
    email TEXT,
    address TEXT
);

-- Table: supplier_medications
CREATE TABLE supplier_medications (
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE CASCADE,
    PRIMARY KEY (supplier_id, medication_id)
);

-- Table: supply_orders
CREATE TABLE supply_orders (
    order_id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL,
    simulation_timestamp TIMESTAMP,
    delivery_date TIMESTAMP,
    status TEXT
);

CREATE INDEX idx_supply_orders_sim_time ON supply_orders(simulation_timestamp);

-- Table: supply_order_items
CREATE TABLE supply_order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES supply_orders(order_id) ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE SET NULL,
    quantity_ordered INTEGER,
    unit_price NUMERIC
);

-- Table: payments
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL,
    supplier_id INTEGER REFERENCES suppliers(supplier_id) ON DELETE SET NULL,
    amount NUMERIC,
    simulation_timestamp TIMESTAMP,
    description TEXT
);

CREATE INDEX idx_payments_sim_time ON payments(simulation_timestamp);

-- Table: payroll_logs
CREATE TABLE payroll_logs (
    payroll_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL,
    simulation_timestamp TIMESTAMP,
    gross_salary NUMERIC,
    net_salary NUMERIC,
    notes TEXT
);

CREATE INDEX idx_payroll_sim_time ON payroll_logs(simulation_timestamp);

-- Table: supply_anomalies
CREATE TABLE supply_anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES supply_orders(order_id) ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE SET NULL,
    anomaly_type TEXT,
    expected_quantity INTEGER,
    received_quantity INTEGER,
    expected_unit_price NUMERIC,
    paid_unit_price NUMERIC,
    notes TEXT,
    simulation_timestamp TIMESTAMP
);

CREATE INDEX idx_supply_anomalies_sim_time ON supply_anomalies(simulation_timestamp);

-- Table: prescription_anomalies
CREATE TABLE prescription_anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    prescription_id INTEGER REFERENCES prescriptions(prescription_id) ON DELETE CASCADE,
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE SET NULL,
    anomaly_type TEXT,
    prescribed_quantity INTEGER,
    standard_quantity INTEGER,
    notes TEXT,
    simulation_timestamp TIMESTAMP
);

CREATE INDEX idx_prescription_anomalies_sim_time ON prescription_anomalies(simulation_timestamp);

-- Table: high_risk_patients
CREATE TABLE high_risk_patients (
    patient_id INTEGER REFERENCES patients(patient_id) ON DELETE CASCADE,
    risk_flags TEXT[],
    reason TEXT,
    flagged_by INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    hospital_id INTEGER REFERENCES hospitals(hospital_id) ON DELETE SET NULL,
    simulation_timestamp TIMESTAMP,
    PRIMARY KEY (patient_id, simulation_timestamp)
);

CREATE INDEX idx_high_risk_patients_sim_time ON high_risk_patients(simulation_timestamp);

-- Table: symptoms (now with mortality_per_hour; no curability)
CREATE TABLE symptoms (
    symptom_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    severity INTEGER NOT NULL CHECK (severity BETWEEN 1 AND 5),
    procedure_id INTEGER REFERENCES procedures(procedure_id) ON DELETE SET NULL,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 0
);

-- Table: conditions (with mortality, curability, diagnosis probability, detectors, possible symptoms)
CREATE TABLE conditions (
    condition_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    mortality_per_hour REAL NOT NULL,        -- baseline hourly death risk
    curability REAL NOT NULL CHECK (curability BETWEEN 0 AND 1),
    detector_treatments JSONB NOT NULL,
    possible_symptoms JSONB NOT NULL
);

CREATE TABLE condition_procedures (
    condition_id INTEGER REFERENCES conditions(condition_id)   ON DELETE CASCADE,
    procedure_id INTEGER REFERENCES procedures(procedure_id)   ON DELETE CASCADE,
    PRIMARY KEY (condition_id, procedure_id)
);

CREATE TABLE condition_medications (
    condition_id  INTEGER REFERENCES conditions(condition_id)   ON DELETE CASCADE,
    medication_id INTEGER REFERENCES medications(medication_id) ON DELETE CASCADE,
    quantity      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (condition_id, medication_id)
);

-- Add this to your hdb_structure.sql (or run it via psql)
CREATE TABLE payroll_schedule (
    employee_id    INTEGER PRIMARY KEY
                   REFERENCES employees(employee_id) ON DELETE CASCADE,
    last_payment   TIMESTAMP,
    next_due       TIMESTAMP NOT NULL,
    frequency_h    INTEGER NOT NULL DEFAULT 336  -- 14 days × 24h
);

INSERT INTO payroll_schedule (employee_id, next_due)
SELECT employee_id, '2025-04-25 12:00:00'::timestamp
FROM employees
ON CONFLICT (employee_id) DO UPDATE
  SET next_due = EXCLUDED.next_due;