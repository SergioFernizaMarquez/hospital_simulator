from generate_hospitals import generate_hospital_data, UNIQUE_HOSPITAL_NAMES, insert_hospitals
from generate_roles import insert_roles
from generate_employees import fetch_hospitals, generate_staff_for_hospital, insert_employees
from generate_medications import insert_medications
from generate_suppliers import fetch_medication_ids, generate_suppliers, insert_suppliers, assign_supplier_medications
from generate_patients import insert_patients
from generate_procedures import insert_procedures
from generate_insurance_providers import generate_insurance_providers, insert_insurance_providers
from generate_symptoms_conditions import insert_symptoms, insert_conditions
from generate_condition_procedures import insert_condition_procedures
from generate_condition_medications import insert_condition_medications
from generate_inventory import insert_inventory

def run_all():
    print("🚀 Running full database population pipeline...")

    # # 1. Core static tables
    # print("\n🏥 Hospitals...")
    hospital_rows = generate_hospital_data(UNIQUE_HOSPITAL_NAMES)
    insert_hospitals(hospital_rows)

    # print("👩‍⚕️ Roles...")
    insert_roles()

    # 2. Medical vocab (used in later mappings)
    print("💊 Medications...")
    insert_medications()

    print("🔬 Procedures...")
    insert_procedures()

    # 3. Staff (needs hospitals + roles)
    print("👨‍⚕️ Employees...")
    hospitals = fetch_hospitals()
    all_employees = []
    for hospital_id, num_beds in hospitals:
        staff = generate_staff_for_hospital(hospital_id, num_beds)
        all_employees.extend(staff)
    insert_employees(all_employees)

    # 4. Suppliers (needs meds)
    print("🏭 Suppliers...")
    medication_ids = fetch_medication_ids()
    suppliers = generate_suppliers()
    supplier_ids = insert_suppliers(suppliers)
    assign_supplier_medications(supplier_ids, medication_ids)

    # 5. Insurance (needs meds and procedures)
    print("📄 Insurance providers...")
    insurance = generate_insurance_providers(n=15)
    insert_insurance_providers(insurance)

    # 6. Patients (standalone)
    print("🧍 Patients...")
    insert_patients(total=100000)

    # 7. Symptoms and Conditions
    print("🩺 Symptoms and Conditions...")
    insert_symptoms()
    insert_conditions()

    print("📌 Condition-Procedures...")
    insert_condition_procedures()

    print("📌 Condition-Medications...")
    insert_condition_medications()

    print(f"✅ Insert inventory records for all hospital-medication pairs.")
    insert_inventory()

    print("\n✅ All data generation completed successfully!")

if __name__ == "__main__":
    run_all()
