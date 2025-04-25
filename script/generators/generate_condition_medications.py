# data_generation/generate_condition_medications.py

import psycopg2
from utils.db_config import get_db_connection

# Your 100 conditions mapped to first-line medications and daily doses
CONDITION_MEDS = {
    "Type 2 Diabetes Mellitus": [
        ("Metformin", 2000),
        ("Empagliflozin", 10)
    ],
    "Alzheimer’s Disease": [
        ("Donepezil", 10),
        ("Memantine", 20)
    ],
    "Parkinson’s Disease": [
        ("Levodopa/Carbidopa", 800),
        ("Ropinirole", 8)
    ],
    "Stroke (Cerebrovascular Accident)": [
        ("Aspirin", 325),
        ("Clopidogrel", 75)
    ],
    "Coronary Artery Disease": [
        ("Aspirin", 81),
        ("Atorvastatin", 40)
    ],
    "Myocardial Infarction": [
        ("Aspirin", 81),
        ("Clopidogrel", 75)
    ],
    "Congestive Heart Failure": [
        ("Furosemide", 40),
        ("Carvedilol", 25)
    ],
    "Atrial Fibrillation": [
        ("Warfarin", 5),
        ("Metoprolol", 100)
    ],
    "Chronic Kidney Disease": [
        ("Lisinopril", 20)
    ],
    "Acute Kidney Injury": [
        # managed supportively; no specific med mapping
    ],
    "Chronic Obstructive Pulmonary Disease (COPD)": [
        ("Tiotropium", 18),
        ("Albuterol", 8)
    ],
    "Asthma (Chronic)": [
        ("Fluticasone", 500),
        ("Albuterol", 8)
    ],
    "Cirrhosis": [
        ("Spironolactone", 100),
        ("Propranolol", 80)
    ],
    "Hepatitis B": [
        ("Tenofovir", 300)
    ],
    "Hepatitis C": [
        ("Sofosbuvir", 400),
        ("Velpatasvir", 100)
    ],
    "Osteoarthritis": [
        ("Ibuprofen", 2400)
    ],
    "Rheumatoid Arthritis": [
        ("Methotrexate", 25),
        ("Prednisone", 10)
    ],
    "Psoriatic Arthritis": [
        ("Methotrexate", 25)
    ],
    "Ankylosing Spondylitis": [
        ("Indomethacin", 150)
    ],
    "Osteoporosis": [
        ("Alendronate", 70),
        ("Calcitriol", 0.25)
    ],
    "Fibromyalgia": [
        ("Pregabalin", 450)
    ],
    "Systemic Lupus Erythematosus": [
        ("Hydroxychloroquine", 400),
        ("Prednisone", 10)
    ],
    "Multiple Sclerosis": [
        ("Interferon beta‑1a", 30)
    ],
    "Epilepsy": [
        ("Levetiracetam", 3000)
    ],
    "Migraine": [
        ("Propranolol", 160),
        ("Sumatriptan", 100)
    ],
    "Breast Cancer": [
        ("Tamoxifen", 20)
    ],
    "Lung Cancer": [
        ("Cisplatin", 75),
        ("Pemetrexed", 500)
    ],
    "Colorectal Cancer": [
        ("5‑Fluorouracil", 2400)
    ],
    "Prostate Cancer": [
        ("Leuprolide", 7.5)
    ],
    "Pancreatic Cancer": [
        ("Gemcitabine", 1000)
    ],
    "Leukemia": [
        ("Imatinib", 400)
    ],
    "Lymphoma": [
        ("R‑CHOP regimen (rituximab)", 375)
    ],
    "Melanoma": [
        ("Pembrolizumab", 200)
    ],
    "Brain Tumor": [
        ("Temozolomide", 200)
    ],
    "Bladder Cancer": [
        ("Bacillus Calmette‑Guérin", 81)
    ],
    "Thyroid Cancer": [
        ("Levothyroxine", 150)
    ],
    "Kidney Cancer": [
        ("Sunitinib", 50)
    ],
    "Sarcoma": [
        ("Doxorubicin", 75)
    ],
    "Ovarian Cancer": [
        ("Carboplatin", 600),
        ("Paclitaxel", 175)
    ],
    "Cervical Cancer": [
        ("Cisplatin", 50)
    ],
    "Testicular Cancer": [
        ("Bleomycin", 30),
        ("Etoposide", 100)
    ],
    "Osteosarcoma": [
        ("High‑dose Methotrexate", 12)
    ],
    "Hip Fracture": [
        ("Enoxaparin", 40)
    ],
    "Femur Fracture": [
        ("Enoxaparin", 40)
    ],
    "Wrist Fracture": [
        ("Ibuprofen", 2400)
    ],
    "Rotator Cuff Tear": [
        ("Ibuprofen", 2400)
    ],
    "ACL Tear": [
        ("Ibuprofen", 2400)
    ],
    "Meniscus Tear": [
        ("Ibuprofen", 2400)
    ],
    "Achilles Tendon Rupture": [
        ("Ibuprofen", 2400)
    ],
    "Carpal Tunnel Syndrome": [
        ("Ibuprofen", 2400)
    ],
    "Tennis Elbow (Lateral Epicondylitis)": [
        ("Ibuprofen", 2400)
    ],
    "Plantar Fasciitis": [
        ("Ibuprofen", 2400)
    ],
    "Herniated Disc": [
        ("Ibuprofen", 2400)
    ],
    "Sciatica": [
        ("Ibuprofen", 2400)
    ],
    "Concussion": [
        ("Acetaminophen", 3000)
    ],
    "Traumatic Brain Injury": [
        ("Acetaminophen", 3000)
    ],
    "Spinal Cord Injury": [
        ("Prednisone", 10)
    ],
    "Second-Degree Burn": [
        ("Silver Sulfadiazine Cream", 1)
    ],
    "Third-Degree Burn": [
        ("Silver Sulfadiazine Cream", 1)
    ],
    "Frostbite": [
        ("Ibuprofen", 2400)
    ],
    "Hypothermia": [
        ("Warm IV Fluids", 2)
    ],
    "Heat Stroke": [
        ("Cool IV Fluids", 2)
    ],
    "Dehydration": [
        ("Oral Rehydration Salts", 4)
    ],
    "Sepsis": [
        ("Broad‑spectrum Antibiotic", 7)
    ],
    "Septic Shock": [
        ("Norepinephrine", 0.1)
    ],
    "Anaphylaxis": [
        ("Epinephrine", 0.3)
    ],
    "Hypovolemic Shock": [
        ("IV Crystalloids", 2)
    ],
    "Cardiogenic Shock": [
        ("Dobutamine", 5)
    ],
    "Toxic Shock Syndrome": [
        ("Clindamycin", 4)
    ],
    "Sickle Cell Disease": [
        ("Hydroxyurea", 15)
    ],
    "Iron Deficiency Anemia": [
        ("Iron Sulfate", 325)
    ],
    "Hemophilia": [
        ("Factor VIII Concentrate", 50)
    ],
    "Thalassemia": [
        ("Deferoxamine", 40)
    ],
    "Vitamin D Deficiency": [
        ("Vitamin D3", 2000)
    ],
    "Hypothyroidism": [
        ("Levothyroxine", 150)
    ],
    "Hyperthyroidism": [
        ("Methimazole", 30)
    ],
    "Cushing’s Syndrome": [
        ("Ketoconazole", 400)
    ],
    "Addison’s Disease": [
        ("Hydrocortisone", 20)
    ],
    "Polycystic Ovary Syndrome": [
        ("Clomiphene Citrate", 50)
    ],
    "Atherosclerosis": [
        ("Atorvastatin", 40)
    ],
    "Deep Vein Thrombosis": [
        ("Heparin", 10)
    ],
    "Pulmonary Embolism": [
        ("Enoxaparin", 1)
    ],
    "Varicose Veins": [
        ("Compression Stockings", 0)
    ],
    "Peripheral Arterial Disease": [
        ("Pentoxifylline", 400)
    ],
    "Chronic Sinusitis": [
        ("Amoxicillin‑clavulanate", 1000)
    ],
    "Crohn’s Disease": [
        ("Mesalamine", 4000)
    ],
    "Ulcerative Colitis": [
        ("Mesalamine", 4000)
    ],
    "Irritable Bowel Syndrome": [
        ("Hyoscyamine", 0.125)
    ],
    "Diverticulitis": [
        ("Metronidazole", 1500)
    ],
    "Appendicitis": [
        ("Immediate Appendectomy Meds Only", 0)
    ],
    "Endometriosis": [
        ("Leuprolide", 7.5)
    ],
    "Polycystic Kidney Disease": [
        ("Tolvaptan", 120)
    ],
    "Glaucoma": [
        ("Latanoprost", 0.005)
    ],
    "Cataracts": [
        ("None (Surgery Only)", 0)
    ],
    "Macular Degeneration": [
        ("Ranibizumab", 0.5)
    ],
    "Otitis Media (Chronic)": [
        ("Amoxicillin", 1500)
    ],
    "Tonsillitis (Chronic/Recurrent)": [
        ("Penicillin VK", 3000)
    ],
    "Benign Prostatic Hyperplasia": [
        ("Tamsulosin", 0.4)
    ],
    "Varicocele": [
        ("NSAIDs", 2400)
    ],
    "Buboes": [
        ("Doxycycline", 200)
    ]
}

def fetch_condition_ids():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT condition_id, name FROM conditions;")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return {name: cid for cid, name in results}

def fetch_medication_ids():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT medication_id, name FROM medications;")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return {name: mid for mid, name in results}

def insert_condition_medications():
    cond_map = fetch_condition_ids()
    med_map = fetch_medication_ids()

    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0

    for cond, meds in CONDITION_MEDS.items():
        cid = cond_map.get(cond)
        if not cid or not meds:
            continue
        for med_name, qty in meds:
            mid = med_map.get(med_name)
            if mid:
                cur.execute("""
                    INSERT INTO condition_medications (condition_id, medication_id, quantity)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (cid, mid, qty))
                inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Inserted {inserted} condition–medication mappings.")

if __name__ == "__main__":
    insert_condition_medications()
