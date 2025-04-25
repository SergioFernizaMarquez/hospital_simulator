# data_generation/generate_condition_procedures.py

import psycopg2
from utils.db_config import get_db_connection

# Your 100 conditions
CONDITIONS = [
    "Type 2 Diabetes Mellitus", "Alzheimer’s Disease", "Parkinson’s Disease",
    "Stroke (Cerebrovascular Accident)", "Coronary Artery Disease",
    "Myocardial Infarction", "Congestive Heart Failure", "Atrial Fibrillation",
    "Chronic Kidney Disease", "Acute Kidney Injury",
    "Chronic Obstructive Pulmonary Disease (COPD)", "Asthma (Chronic)",
    "Cirrhosis", "Hepatitis B", "Hepatitis C", "Osteoarthritis",
    "Rheumatoid Arthritis", "Psoriatic Arthritis", "Ankylosing Spondylitis",
    "Osteoporosis", "Fibromyalgia", "Systemic Lupus Erythematosus",
    "Multiple Sclerosis", "Epilepsy", "Migraine", "Breast Cancer", "Lung Cancer",
    "Colorectal Cancer", "Prostate Cancer", "Pancreatic Cancer", "Leukemia",
    "Lymphoma", "Melanoma", "Brain Tumor", "Bladder Cancer", "Thyroid Cancer",
    "Kidney Cancer", "Sarcoma", "Ovarian Cancer", "Cervical Cancer",
    "Testicular Cancer", "Osteosarcoma", "Hip Fracture", "Femur Fracture",
    "Wrist Fracture", "Rotator Cuff Tear", "ACL Tear", "Meniscus Tear",
    "Achilles Tendon Rupture", "Carpal Tunnel Syndrome",
    "Tennis Elbow (Lateral Epicondylitis)", "Plantar Fasciitis", "Herniated Disc",
    "Sciatica", "Concussion", "Traumatic Brain Injury", "Spinal Cord Injury",
    "Second-Degree Burn", "Third-Degree Burn", "Frostbite", "Hypothermia",
    "Heat Stroke", "Dehydration", "Sepsis", "Septic Shock", "Anaphylaxis",
    "Hypovolemic Shock", "Cardiogenic Shock", "Toxic Shock Syndrome",
    "Sickle Cell Disease", "Iron Deficiency Anemia", "Hemophilia", "Thalassemia",
    "Vitamin D Deficiency", "Hypothyroidism", "Hyperthyroidism",
    "Cushing’s Syndrome", "Addison’s Disease", "Polycystic Ovary Syndrome",
    "Atherosclerosis", "Deep Vein Thrombosis", "Pulmonary Embolism",
    "Varicose Veins", "Peripheral Arterial Disease", "Chronic Sinusitis",
    "Crohn’s Disease", "Ulcerative Colitis", "Irritable Bowel Syndrome",
    "Diverticulitis", "Appendicitis", "Endometriosis",
    "Polycystic Kidney Disease", "Glaucoma", "Cataracts",
    "Macular Degeneration", "Otitis Media (Chronic)",
    "Tonsillitis (Chronic/Recurrent)", "Benign Prostatic Hyperplasia",
    "Varicocele", "Buboes"
]

# Only true procedures/interventions—no imaging or lab panels
CONDITION_SURGERIES = {
    "Type 2 Diabetes Mellitus":                [],  # medical management only
    "Alzheimer’s Disease":                     [],  
    "Parkinson’s Disease":                     ["Deep Brain Stimulation"],
    "Stroke (Cerebrovascular Accident)":       ["Mechanical Thrombectomy"],
    "Coronary Artery Disease":                 ["Coronary Artery Bypass Graft"],
    "Myocardial Infarction":                   ["Percutaneous Coronary Intervention"],
    "Congestive Heart Failure":                ["Heart Transplant"],
    "Atrial Fibrillation":                     ["Catheter Ablation"],
    "Chronic Kidney Disease":                  ["Kidney Transplant"],
    "Acute Kidney Injury":                     [],  
    "Chronic Obstructive Pulmonary Disease (COPD)": ["Lung Transplant"],
    "Asthma (Chronic)":                        ["Bronchial Thermoplasty"],
    "Cirrhosis":                               ["Liver Transplant"],
    "Hepatitis B":                             [],  
    "Hepatitis C":                             [],  
    "Osteoarthritis":                          ["Total Knee Replacement","Total Hip Replacement"],
    "Rheumatoid Arthritis":                    ["Synovectomy"],
    "Psoriatic Arthritis":                     ["Joint Replacement"],
    "Ankylosing Spondylitis":                  [],  
    "Osteoporosis":                            ["Vertebroplasty"],
    "Fibromyalgia":                            [],  
    "Systemic Lupus Erythematosus":            [],  
    "Multiple Sclerosis":                      [],  
    "Epilepsy":                                ["Temporal Lobe Resection"],
    "Migraine":                                ["Occipital Nerve Stimulation"],
    "Breast Cancer":                           ["Mastectomy","Lumpectomy"],
    "Lung Cancer":                             ["Lobectomy","Pneumonectomy"],
    "Colorectal Cancer":                       ["Colectomy"],
    "Prostate Cancer":                         ["Prostatectomy"],
    "Pancreatic Cancer":                       ["Whipple Procedure"],
    "Leukemia":                                ["Bone Marrow Transplant"],
    "Lymphoma":                                [],  
    "Melanoma":                                ["Wide Local Excision"],
    "Brain Tumor":                             ["Craniotomy"],
    "Bladder Cancer":                          ["Cystectomy"],
    "Thyroid Cancer":                          ["Thyroidectomy"],
    "Kidney Cancer":                           ["Nephrectomy"],
    "Sarcoma":                                 ["Wide Local Resection"],
    "Ovarian Cancer":                          ["Oophorectomy"],
    "Cervical Cancer":                         ["Hysterectomy"],
    "Testicular Cancer":                       ["Orchiectomy"],
    "Osteosarcoma":                            ["Limb-Salvage Surgery"],
    "Hip Fracture":                            ["Hip Pinning","Hip Hemiarthroplasty"],
    "Femur Fracture":                          ["Intramedullary Nailing"],
    "Wrist Fracture":                          ["Open Reduction & Internal Fixation"],
    "Rotator Cuff Tear":                       ["Rotator Cuff Repair"],
    "ACL Tear":                                ["ACL Reconstruction"],
    "Meniscus Tear":                           ["Arthroscopic Meniscectomy"],
    "Achilles Tendon Rupture":                 ["Achilles Repair"],
    "Carpal Tunnel Syndrome":                  ["Carpal Tunnel Release"],
    "Tennis Elbow (Lateral Epicondylitis)":    ["Epicondylar Debridement"],
    "Plantar Fasciitis":                       ["Fasciotomy"],
    "Herniated Disc":                          ["Discectomy"],
    "Sciatica":                                [],  
    "Concussion":                              [],  
    "Traumatic Brain Injury":                  [],  
    "Spinal Cord Injury":                      [],  
    "Second-Degree Burn":                      ["Skin Grafting"],
    "Third-Degree Burn":                       ["Skin Grafting"],
    "Frostbite":                               ["Escharotomy"],
    "Hypothermia":                             [],  
    "Heat Stroke":                             [],  
    "Dehydration":                             [],  
    "Sepsis":                                  [],  
    "Septic Shock":                            [],  
    "Anaphylaxis":                             [],  
    "Hypovolemic Shock":                       [],  
    "Cardiogenic Shock":                       [],  
    "Toxic Shock Syndrome":                    [],  
    "Sickle Cell Disease":                     ["Splenectomy"],
    "Iron Deficiency Anemia":                  [],  
    "Hemophilia":                              [],  
    "Thalassemia":                             [],  
    "Vitamin D Deficiency":                    [],  
    "Hypothyroidism":                          [],  
    "Hyperthyroidism":                         ["Thyroidectomy"],
    "Cushing’s Syndrome":                      ["Adrenalectomy"],
    "Addison’s Disease":                       [],  
    "Polycystic Ovary Syndrome":               ["Ovarian Drilling"],
    "Atherosclerosis":                         ["Endarterectomy"],
    "Deep Vein Thrombosis":                    ["IVC Filter Placement"],
    "Pulmonary Embolism":                      ["Thrombectomy"],
    "Varicose Veins":                          ["Vein Stripping"],
    "Peripheral Arterial Disease":             ["Bypass Surgery"],
    "Chronic Sinusitis":                       ["Functional Endoscopic Sinus Surgery"],
    "Crohn’s Disease":                         ["Resection"],
    "Ulcerative Colitis":                      ["Colectomy"],
    "Irritable Bowel Syndrome":                [],  
    "Diverticulitis":                          ["Colectomy"],
    "Appendicitis":                            ["Appendectomy"],
    "Endometriosis":                           ["Laparoscopic Excision"],
    "Polycystic Kidney Disease":               [],  
    "Glaucoma":                                ["Trabeculectomy"],
    "Cataracts":                               ["Phacoemulsification"],
    "Macular Degeneration":                    [],  
    "Otitis Media (Chronic)":                  ["Myringotomy"],
    "Tonsillitis (Chronic/Recurrent)":         ["Tonsillectomy"],
    "Benign Prostatic Hyperplasia":            ["Transurethral Resection of Prostate"],
    "Varicocele":                              ["Varicocelectomy"],
    "Buboes":                                  ["Incision and Drainage"]
}

def fetch_condition_ids():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT condition_id, name FROM conditions;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return {name: cid for cid, name in data}

def fetch_procedure_ids(proc_list):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT procedure_id, name FROM procedures WHERE name = ANY(%s);",
        (proc_list,)
    )
    data = cur.fetchall()
    cur.close()
    conn.close()
    return {name: pid for pid, name in data}

def insert_condition_procedures():
    cond_map = fetch_condition_ids()
    all_procs = list({p for procs in CONDITION_SURGERIES.values() for p in procs})
    proc_map = fetch_procedure_ids(all_procs)

    conn = get_db_connection()
    cur = conn.cursor()
    inserted = 0

    for cond, surgeries in CONDITION_SURGERIES.items():
        cid = cond_map.get(cond)
        if not cid or not surgeries:
            continue  # skip if no condition ID or empty list
        for proc_name in surgeries:
            pid = proc_map.get(proc_name)
            if pid:
                cur.execute("""
                    INSERT INTO condition_procedures (condition_id, procedure_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                """, (cid, pid))
                inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Inserted {inserted} condition–procedure mappings.")

if __name__ == "__main__":
    insert_condition_procedures()
