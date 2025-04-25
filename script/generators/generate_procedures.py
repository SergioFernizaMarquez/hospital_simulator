# data_generation/generate_procedures.py

import psycopg2
from utils.db_config import get_db_connection

# 1) Import your existing mappings
from generate_symptoms_conditions import SYMPTOM_TREATMENTS
from generate_condition_procedures import CONDITION_SURGERIES

# 2) Extract all unique procedure names
symptom_procs = {
    proc for proc, _, _ in SYMPTOM_TREATMENTS.values() 
    if proc is not None
}
condition_procs = {
    proc for procs in CONDITION_SURGERIES.values() 
    for proc in procs
}
ALL_PROCEDURES = sorted(symptom_procs.union(condition_procs))

# 3) Manually map each procedure to (type, average_cost_usd)
#    Costs pulled from national‐average sources:
#    - Chest X‑ray ~$280 :contentReference[oaicite:0]{index=0}
#    - MRI Brain ~$1,325 :contentReference[oaicite:1]{index=1}
#    - Abdominal Ultrasound ~$305 :contentReference[oaicite:2]{index=2}
#    - CT Head ~$235 :contentReference[oaicite:3]{index=3}
#    - CBC Panel ~$33 :contentReference[oaicite:4]{index=4}
#    (…and so on for each procedure)
PROCEDURE_INFO = {
    "Chest X-ray":                   ("Imaging",        280.00),
    "MRI Brain (without contrast)":  ("Imaging",       1325.00),
    "Abdominal Ultrasound":          ("Imaging",        305.00),
    "CT Head (non-contrast)":        ("Imaging",        235.00),
    "Fasting Blood Glucose Test":    ("Lab Test",        50.00),
    "Psychiatric Evaluation":        ("Evaluation",     150.00),
    "MRI Spine":                     ("Imaging",       1325.00),
    "Upper Endoscopy":               ("Endoscopy",      4000.00),
    "Hemoglobin A1c":                ("Lab Test",        61.00),
    "CBC & Coagulation Panel":       ("Lab Test",        95.00),  # CBC ~$33 + Coag ~$7 :contentReference[oaicite:5]{index=5}
    "Slit Lamp Exam":                ("Exam",           150.00),
    "Thyroid Function Test":         ("Lab Test",        76.00),
    "Laryngoscopy":                  ("Endoscopy",      1200.00),
    "Cognitive Assessment":          ("Evaluation",     200.00),
    "Stool Culture":                 ("Lab Test",        75.00),
    "Dix-Hallpike Maneuver":         ("Exam",            80.00),
    "Salivary Flow Test":            ("Lab Test",       100.00),
    "Urinalysis":                    ("Lab Test",        35.00),
    "Otoscopy":                      ("Exam",           100.00),
    "Blood Cultures":                ("Lab Test",       150.00),
    "Allergy Skin Test":             ("Lab Test",       100.00),
    "Throat Swab":                   ("Lab Test",       100.00),
    "Neurologic Exam":               ("Exam",           120.00),
    "X-ray Joint":                   ("Imaging",        300.00),
    "Colonoscopy":                   ("Endoscopy",     3100.00),
    "Skin Exam":                     ("Exam",           100.00),
    "Dermatologic Exam":             ("Exam",           120.00),
    "Barium Swallow":                ("Imaging",        800.00),
    "Liver Function Tests":          ("Lab Test",        48.00),
    "Psychiatric Evaluation":        ("Evaluation",     150.00),

    # Oncology Surgeries
    "Mastectomy":                        ("Surgery", 35000.00),  # avg $15K–$55K :contentReference[oaicite:0]{index=0}  
    "Lumpectomy":                        ("Surgery", 15000.00),  # avg $10K–$20K :contentReference[oaicite:1]{index=1}  
    "Lobectomy":                         ("Surgery", 30000.00),  # median ~$22K–$27K; use $30K :contentReference[oaicite:2]{index=2}  
    "Pneumonectomy":                     ("Surgery",100000.00),  # avg $70K–$150K :contentReference[oaicite:3]{index=3}  
    "Colectomy":                         ("Surgery", 40000.00),  # avg $36K–$44K :contentReference[oaicite:4]{index=4}  
    "Prostatectomy":                     ("Surgery", 20000.00),  # avg $11K–$15K (robotic) :contentReference[oaicite:5]{index=5}  
    "Whipple Procedure":                 ("Surgery",150000.00),  # avg ~$120K–$205K :contentReference[oaicite:6]{index=6}  
    "Bone Marrow Transplant":            ("Surgery",350000.00),  # autologous avg ~$200K–$500K :contentReference[oaicite:7]{index=7}  
    "Craniotomy":                        ("Surgery", 60000.00),  # open brain surgery avg ~$60K :contentReference[oaicite:8]{index=8}  
    "Cystectomy":                        ("Surgery", 40000.00),  # bladder removal avg ~$40K :contentReference[oaicite:9]{index=9}  
    "Thyroidectomy":                     ("Surgery", 15000.00),  # avg $10K–$20K :contentReference[oaicite:10]{index=10}  
    "Nephrectomy":                       ("Surgery", 35000.00),  # kidney removal avg ~$35K :contentReference[oaicite:11]{index=11}  
    "Wide Local Excision":               ("Surgery", 12000.00),  # melanoma excision avg ~$12K :contentReference[oaicite:12]{index=12}  
    "Oophorectomy":                      ("Surgery", 20000.00),  # avg $15K–$25K :contentReference[oaicite:13]{index=13}  
    "Hysterectomy":                      ("Surgery", 18000.00),  # avg $15K–$20K :contentReference[oaicite:14]{index=14}  
    "Orchiectomy":                       ("Surgery", 10000.00),  # avg $8K–$12K :contentReference[oaicite:15]{index=15}  
    "Limb-Salvage Surgery":              ("Surgery", 50000.00),  # sarcoma resection avg ~$50K :contentReference[oaicite:16]{index=16}  

    # Orthopedic & Trauma
    "Hip Pinning":                       ("Surgery", 25000.00),  # avg ~$25K :contentReference[oaicite:17]{index=17}  
    "Hip Hemiarthroplasty":              ("Surgery", 30000.00),  # avg ~$30K :contentReference[oaicite:18]{index=18}  
    "Intramedullary Nailing":            ("Surgery", 20000.00),  # femur rod insertion avg ~$20K :contentReference[oaicite:19]{index=19}  
    "Open Reduction & Internal Fixation":("Surgery", 15000.00),  # wrist ORIF avg ~$15K :contentReference[oaicite:20]{index=20}  
    "Rotator Cuff Repair":               ("Surgery", 18000.00),  # avg ~$18K :contentReference[oaicite:21]{index=21}  
    "ACL Reconstruction":                ("Surgery", 21000.00),  # avg ~$21K :contentReference[oaicite:22]{index=22}  
    "Arthroscopic Meniscectomy":         ("Surgery", 12000.00),  # avg ~$12K :contentReference[oaicite:23]{index=23}  
    "Achilles Repair":                   ("Surgery", 15000.00),  # avg ~$15K :contentReference[oaicite:24]{index=24}  
    "Carpal Tunnel Release":             ("Surgery",  8000.00),  # avg ~$8K :contentReference[oaicite:25]{index=25}  
    "Epicondylar Debridement":           ("Surgery", 10000.00),  # tennis elbow debridement avg ~$10K :contentReference[oaicite:26]{index=26}  
    "Fasciotomy":                        ("Surgery", 12000.00),  # plantar fasciitis release avg ~$12K :contentReference[oaicite:27]{index=27}  
    "Discectomy":                        ("Surgery", 25000.00),  # herniated disc removal avg ~$25K :contentReference[oaicite:28]{index=28}  

    # Burns & Skin
    "Skin Grafting":                     ("Surgery", 20000.00),  # avg ~$20K :contentReference[oaicite:29]{index=29}  
    "Escharotomy":                       ("Surgery", 15000.00),  # avg ~$15K :contentReference[oaicite:30]{index=30}  

    # Miscellaneous
    "Deep Brain Stimulation":            ("Surgery", 60000.00),  # DBS avg ~$60K :contentReference[oaicite:31]{index=31}  
    "Mechanical Thrombectomy":           ("Surgery", 50000.00),  # stroke thrombectomy avg ~$50K :contentReference[oaicite:32]{index=32}  
    "Coronary Artery Bypass Graft":      ("Surgery",146000.00),  # CABG avg ~$146K :contentReference[oaicite:33]{index=33}  
    "Percutaneous Coronary Intervention":("Surgery", 45000.00),  # PCI avg ~$45K :contentReference[oaicite:34]{index=34}  
    "Heart Transplant":                  ("Surgery",1000000.00),  # avg ~$1M :contentReference[oaicite:35]{index=35}  
    "Catheter Ablation":                 ("Surgery", 20000.00),  # AFib ablation avg ~$20K :contentReference[oaicite:36]{index=36}  
    "Kidney Transplant":                 ("Surgery", 700000.00),  # avg ~$700K :contentReference[oaicite:37]{index=37}  
    "Lung Transplant":                   ("Surgery", 700000.00),  # avg ~$700K :contentReference[oaicite:38]{index=38}  
    "Bronchial Thermoplasty":            ("Surgery", 25000.00),  # avg ~$25K :contentReference[oaicite:39]{index=39}  
    "Liver Transplant":                  ("Surgery", 600000.00),  # avg ~$600K :contentReference[oaicite:40]{index=40}  
    "Total Knee Replacement":            ("Surgery", 40000.00),  # avg ~$40K :contentReference[oaicite:41]{index=41}  
    "Total Hip Replacement":             ("Surgery", 39000.00),  # avg ~$39K :contentReference[oaicite:42]{index=42}  
    "Synovectomy":                       ("Surgery", 15000.00),  # avg ~$15K :contentReference[oaicite:43]{index=43}  
    "Temporal Lobe Resection":           ("Surgery", 50000.00),  # avg ~$50K :contentReference[oaicite:44]{index=44}  
    "Occipital Nerve Stimulation":       ("Surgery", 20000.00),  # avg ~$20K :contentReference[oaicite:45]{index=45}  
}

# (Keep the rest of your insert_procedures() logic unchanged.)


def insert_procedures():
    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0

    for name in ALL_PROCEDURES:
        proc_type, cost = PROCEDURE_INFO.get(name, ("Other", 100.00))
        cur.execute("""
            INSERT INTO procedures (name, type, cost)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (name, proc_type, cost))
        inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Inserted or skipped {inserted} procedures into the table.")

if __name__ == "__main__":
    insert_procedures()
