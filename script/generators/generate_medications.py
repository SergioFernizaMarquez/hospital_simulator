# data_generation/generate_medications.py

import psycopg2
from utils.db_config import get_db_connection

# Import your existing symptom & condition mappings
from generate_symptoms_conditions import SYMPTOM_TREATMENTS
from generate_condition_medications import CONDITION_MEDS

# 1) Gather every unique medication name from both mappings
med_names = {
    med for _, med, _ in SYMPTOM_TREATMENTS.values() if med
} | {
    med for meds in CONDITION_MEDS.values() for med, _ in meds
}

# 2) Hard‑coded cost & category info for each medication
#    Major drugs have actual GoodRx‐sourced unit costs; all others default to $10.00
MEDICATION_INFO = {
    # From SYMPTOMS
    "Acyclovir":           ("Antiviral",       0.25,  "Doctor"),  # Zovirax generic as low as $4.38 for 30 tabs → $0.15/tab :contentReference[oaicite:0]{index=0}
    "Acetaminophen":       ("Analgesic",       0.10,  "RN"),
    "Amoxicillin":         ("Antibiotic",      0.50,  "Doctor"),
    "Artificial Tears":    ("Ophthalmic",      5.00,  "RN"),
    "Baclofen":            ("Muscle Relaxant", 1.00,  "Doctor"),
    "Cetirizine":          ("Antihistamine",   0.15,  "Pharmacist"),
    "Clindamycin":         ("Antibiotic",      1.50,  "Doctor"),
    "Dextromethorphan":    ("Antitussive",     0.20,  "Pharmacist"),
    "Diphenhydramine":     ("Antihistamine",   0.10,  "RN"),
    "Guaifenesin":         ("Expectorant",     0.20,  "Pharmacist"),
    "Haloperidol":         ("Antipsychotic",   1.00,  "Doctor"),
    "Ibuprofen":           ("NSAID",           0.03,  "RN"),       # as low as $2 for 70 tabs → $0.03/tab :contentReference[oaicite:1]{index=1}
    "Loperamide":          ("Antidiarrheal",   0.25,  "Pharmacist"),
    "Meclizine":           ("Antiemetic",      0.30,  "RN"),
    "Metformin":           ("Antidiabetic",    0.14,  "Doctor"),  # generic as low as $0.14/tab :contentReference[oaicite:2]{index=2}
    "Naproxen":            ("NSAID",           0.14,  "RN"),       # avg $8.40 for 60 tabs → $0.14/tab :contentReference[oaicite:3]{index=3}
    "Nitrofurantoin":      ("Antibiotic",      0.50,  "Doctor"),
    "Omeprazole":          ("PPI",             0.50,  "RN"),
    "Pantoprazole":        ("PPI",             1.00,  "Pharmacist"),
    "Penicillin VK":       ("Antibiotic",      0.30,  "Doctor"),
    "Pilocarpine":         ("Cholinergic",     1.00,  "Doctor"),
    "Propranolol":         ("Beta Blocker",    0.20,  "Doctor"),
    "Tranexamic Acid":     ("Antifibrinolytic",1.00,  "RN"),
    "Zolpidem":            ("Sedative",        0.50,  "Doctor"),

    # From CONDITIONS
    "Albuterol":           ("Bronchodilator",  0.20,  "RN"),
    "Alendronate":         ("Bisphosphonate",  1.00,  "Doctor"),
    "Allopurinol":         ("Uric Acid Reducer",0.50, "Doctor"),
    "Amlodipine":          ("Antihypertensive",0.20,  "Doctor"),
    "Amoxicillin‑clavulanate":("Antibiotic",   2.00,  "Doctor"),
    "Anastrozole":         ("Antineoplastic", 50.00,  "Doctor"),
    "Atorvastatin":        ("Cholesterol-lowering",0.30,"Doctor"),
    "Azithromycin":        ("Antibiotic",      2.00,  "Doctor"),
    "Bacillus Calmette‑Guérin":("Immunotherapy",500.0,"Doctor"),
    "Bleomycin":           ("Antineoplastic", 75.00,  "Doctor"),
    "Carboplatin":         ("Antineoplastic",100.00,  "Doctor"),
    "Carvedilol":          ("Beta Blocker",    0.50,  "Doctor"),
    "Ceftriaxone":         ("Antibiotic",      2.00,  "Doctor"),
    "Clopidogrel":         ("Antiplatelet",    0.50,  "Doctor"),
    "Cisplatin":           ("Antineoplastic",200.00,  "Doctor"),
    "Clemastine":          ("Antihistamine",   0.50,  "Pharmacist"),
    "Deferoxamine":        ("Chelation Agent",10.00,  "Doctor"),
    "Dextromethorphan":    ("Antitussive",     0.20,  "Pharmacist"),
    "Doxorubicin":         ("Antineoplastic",150.00,  "Doctor"),
    "Empagliflozin":       ("SGLT2 Inhibitor",20.79,  "Doctor"),  # $623.78/30 tabs → $20.79/tab :contentReference[oaicite:4]{index=4}
    "Enoxaparin":          ("Anticoagulant",   3.00,  "Doctor"),
    "Epinephrine":         ("Vasopressor",     5.00,  "RN"),
    "Etoposide":           ("Antineoplastic",100.00,  "Doctor"),
    "Factor VIII Concentrate":("Coagulant",    50.00, "Doctor"),
    "Fluticasone":         ("Steroid",         1.00,  "Doctor"),
    "Furosemide":          ("Diuretic",        0.20,  "Doctor"),
    "Gemcitabine":         ("Antineoplastic",200.00,  "Doctor"),
    "Heparin":             ("Anticoagulant",   1.00,  "Doctor"),
    "Hydrocortisone":      ("Steroid",         0.50,  "Pharmacist"),
    "Hydroxychloroquine":  ("Antimalarial",    1.00,  "Doctor"),
    "Hydroxyurea":         ("Cytoreductive",   2.00,  "Doctor"),
    "Imatinib":            ("Antineoplastic", 50.00,  "Doctor"),
    "Interferon beta‑1a":  ("Immunomodulator",100.00, "Doctor"),
    "Ketoconazole":        ("Antifungal",      2.00,  "Doctor"),
    "Leuprolide":          ("GnRH Agonist",    20.00,  "Doctor"),
    "Levodopa/Carbidopa":  ("Antiparkinsonian",5.00,   "Doctor"),
    "Levetiracetam":       ("Anticonvulsant",  0.15,  "Doctor"),  # $9/60 tabs → $0.15/tab 
    "Lisinopril":          ("Antihypertensive",0.20,   "Doctor"),
    "Mesalamine":          ("Anti-inflammatory",2.00,  "Doctor"),
    "Methimazole":         ("Antithyroid",     1.00,  "Doctor"),
    "Methotrexate":        ("Antirheumatic",   1.00,  "Doctor"),
    "Minoxidil Topical":   ("Vasodilator",     5.00,  "Pharmacist"),
    "Norepinephrine":      ("Vasopressor",     5.00,  "Doctor"),
    "Ondansetron":         ("Antiemetic",      1.00,  "Doctor"),
    "Oral Rehydration Salts":("Rehydration",    0.10,  "RN"),
    "Oxycodone":           ("Opioid",         1.00,  "Doctor"),
    "Pantoprazole":        ("PPI",             1.00,  "Pharmacist"),
    "Pembrolizumab":       ("Immunotherapy", 100.00,  "Doctor"),
    "Penicillin VK":       ("Antibiotic",      0.30,  "Doctor"),
    "Pentoxifylline":      ("Hemorrheologic",  1.00,  "Doctor"),
    "Prednisone":          ("Steroid",         0.50,  "Doctor"),
    "Propranolol":         ("Beta Blocker",    0.20,  "Doctor"),
    "R-CHOP regimen (rituximab)":("Immunotherapy",250.0,"Doctor"),
    "Ropinirole":          ("Antiparkinsonian",2.00,  "Doctor"),
    "Sertraline":          ("Antidepressant",  0.30,  "Doctor"),
    "Sofosbuvir":          ("Antiviral",      40.00,  "Doctor"),
    "Spironolactone":      ("Diuretic",        0.50,  "Doctor"),
    "Sumatriptan":         ("Antimigraine",    1.00,  "Doctor"),
    "Tamoxifen":           ("Antineoplastic",  0.50,  "Doctor"),
    "Tenofovir":           ("Antiviral",       0.60,  "Doctor"),  # $53.98/90 tabs → $0.60/tab :contentReference[oaicite:5]{index=5}
    "Temozolomide":        ("Antineoplastic", 50.00,  "Doctor"),
    "Tetracycline":        ("Antibiotic",      0.50,  "Doctor"),
    "Thyroid hormone (levothyroxine)":("Hormone",0.20,"Doctor"),
    "Tolvaptan":           ("Vasopressin antagonist",5.00,"Doctor"),
    "Tranexamic Acid":     ("Antifibrinolytic",1.00,  "RN"),
    "Velpatasvir":         ("Antiviral",      50.00,  "Doctor"),
    "Vitamin D3":          ("Supplement",      0.10,  "Pharmacist"),
    "Warfarin":            ("Anticoagulant",   0.20,  "Doctor"),
    "Zolpidem":            ("Sedative",        0.50,  "Doctor"),
    "Aspirin":             ("Antiplatelet", 0.05, "Doctor"),   # generic ~$0.05/tab
    "Ibuprofen":           ("NSAID",           0.03,  "RN"),       # ~ $0.03/tablet  
    "Acetaminophen":       ("Analgesic",       0.10,  "RN"),       # ~ $0.10/tablet (Tylenol® generic)  

    # Strong opioids
    "Morphine":         ("Opioid",          1.00,  "Doctor"),   # approx $1.00/dose  
    "Fentanyl":         ("Opioid",          5.00,  "Doctor"),   # patch or injection equivalents  
    "Oxycodone":        ("Opioid",          1.00,  "Doctor"),   # ~ $1.00/tablet  
    "Hydromorphone":    ("Opioid",          2.00,  "Doctor"),   # ~ $2.00/tablet  
    "Hydrocodone":      ("Opioid",          1.00,  "Doctor"),   # ~ $1.00/tablet  
    "Codeine":          ("Opioid",          0.50,  "Doctor"),   # ~ $0.50/tablet  
    "Tramadol":         ("Opioid",          0.50,  "Doctor")    # ~ $0.50/tablet  
}


def insert_medications():
    conn = get_db_connection()
    cur = conn.cursor()
    count = 0

    for name in sorted(med_names):
        category, cost, level = MEDICATION_INFO.get(name, ("Other", 10.00, "Doctor"))
        cur.execute("""
            INSERT INTO medications (name, category, unit_cost, prescription_level)
            VALUES (%s, %s, %s, %s);
        """, (name, category, cost, level))
        count += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Inserted or skipped {count} medications into the table.")

if __name__ == "__main__":
    insert_medications()
