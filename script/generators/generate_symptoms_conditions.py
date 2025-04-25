# data_generation/generate_symptoms_conditions.py

import random
import json
import psycopg2
from utils.db_config import get_db_connection

# 1) SYMPTOMS + their standard diagnostic & therapeutic mappings
SYMPTOM_LIST = [
    "Encephalitis", "Acid reflux", "Polyphagia", "Psychosis", "Back pain",
    "Stomach pain", "Bleeding", "Blurred vision", "Sweating", "Bruising",
    "Chest pain", "Chills", "Choking sensation", "Delirium", "Cough",
    "Diarrhea", "Dizziness", "Dry mouth", "Blood in urine", "Earache",
    "Fatigue", "Fever", "Flushing", "Headache", "Heart palpitations",
    "Hearing loss", "Hives", "Hoarseness", "Itching", "Joint pain",
    "Loss of appetite", "Memory loss", "Mood swings", "Muscle weakness",
    "Nausea", "Gangrene", "fluid in genitals", "Numbness", "Palpitations",
    "Paralysis", "Rash", "Red eyes", "Runny nose", "Seizures",
    "Shortness of breath", "Skin lesions", "Slurred speech", "Sneezing",
    "Sore throat", "Spasms", "Swelling", "Tachycardia", "Inflammation",
    "Tremor", "Trouble swallowing", "Ulcers", "Urinary pain", "Urticaria",
    "Vomiting", "High blood pressure", "Weight loss", "Wheezing", "Weakness",
    "Yellow skin", "Chest tightness", "Cold sweats", "Confusion",
    "Hot flashes", "Paleness", "Ringing in ears", "Excessive thirst",
    "Dry cough", "Aphasia", "Lightheadedness", "Orthopnea",
    "Paresthesia", "Phlegm production", "Restlessness", "Bloody stool",
    "Tingling", "Vision loss", "Voice changes", "Water retention",
    "Internal bleeding", "Zoster lesions", "Blisters", "Coma",
    "Burning sensation", "Cold intolerance", "Dry skin", "Fainting",
    "Low blood pressure", "Hair loss", "Hypersalivation", "Insomnia",
    "Gastroenteritis", "Abcesses", "Jaundice", "Meningitis", "Buboes",
    "Pneumonia"
]

# Mapping symptom → (procedure_name, medication_name, daily_qty)
SYMPTOM_TREATMENTS = {
    # (procedure, medication, qty)
    "Encephalitis": ("MRI Brain (without contrast)", "Acyclovir", 21),
    "Acid reflux": ("Upper Endoscopy", "Omeprazole", 1),
    "Polyphagia": ("Fasting Blood Glucose Test", "Metformin", 2),
    "Psychosis": ("Psychiatric Evaluation", "Risperidone", 2),
    "Back pain": ("MRI Spine", "Ibuprofen", 3),
    "Stomach pain": ("Abdominal Ultrasound", "Pantoprazole", 1),
    "Bleeding": ("CBC & Coagulation Panel", "Tranexamic Acid", 3),
    "Blurred vision": ("Slit Lamp Exam", "Artificial Tears", 4),
    "Sweating": ("Thyroid Function Test", "Propranolol", 3),
    "Bruising": ("CBC & Coagulation Panel", None, 0),
    "Chest pain": ("EKG (Electrocardiogram)", "Aspirin", 1),
    "Chills": ("Blood Cultures", "Acetaminophen", 4),
    "Choking sensation": ("Laryngoscopy", None, 0),
    "Delirium": ("Cognitive Assessment", "Haloperidol", 4),
    "Cough": ("Chest X-ray", "Dextromethorphan", 4),
    "Diarrhea": ("Stool Culture", "Loperamide", 4),
    "Dizziness": ("Dix-Hallpike Maneuver", "Meclizine", 3),
    "Dry mouth": ("Salivary Flow Test", "Pilocarpine", 3),
    "Blood in urine": ("Urinalysis", None, 0),
    "Earache": ("Otoscopy", "Amoxicillin", 3),
    "Fatigue": ("TSH Test", None, 0),
    "Fever": ("Physical Exam & Temp Check", "Acetaminophen", 4),
    "Flushing": ("Plasma Catecholamines", None, 0),
    "Headache": ("CT Head", "Ibuprofen", 3),
    "Heart palpitations": ("EKG", "Propranolol", 2),
    "Hearing loss": ("Audiometry", None, 0),
    "Hives": ("Allergy Skin Test", "Diphenhydramine", 4),
    "Hoarseness": ("Laryngoscopy", "Omeprazole", 1),
    "Itching": ("Skin Allergy Test", "Cetirizine", 1),
    "Joint pain": ("X-ray Joint", "Naproxen", 2),
    "Loss of appetite": ("Upper Endoscopy", None, 0),
    "Memory loss": ("MRI Brain (without contrast)", "Donepezil", 1),
    "Mood swings": ("Psychiatric Evaluation", "Sertraline", 1),
    "Muscle weakness": ("EMG", None, 0),
    "Nausea": ("Abdominal Ultrasound", "Ondansetron", 2),
    "Gangrene": ("Vascular Doppler Ultrasound", None, 0),
    "fluid in genitals": ("Scrotal Ultrasound", None, 0),
    "Numbness": ("Nerve Conduction Study", "Gabapentin", 3),
    "Palpitations": ("EKG", "Propranolol", 2),
    "Paralysis": ("MRI Spine", None, 0),
    "Rash": ("Skin Biopsy", "Hydrocortisone Cream", 2),
    "Red eyes": ("Slit Lamp Exam", "Artificial Tears", 4),
    "Runny nose": ("Rhinoscopy", "Loratadine", 1),
    "Seizures": ("EEG (Electroencephalogram)", "Levetiracetam", 2),
    "Shortness of breath": ("Pulmonary Function Test", "Albuterol", 2),
    "Skin lesions": ("Skin Biopsy", None, 0),
    "Slurred speech": ("CT Head", None, 0),
    "Sneezing": ("Allergy Skin Test", "Cetirizine", 1),
    "Sore throat": ("Throat Swab", "Penicillin VK", 4),
    "Spasms": ("Neurologic Exam", "Baclofen", 3),
    "Swelling": ("Ultrasound", None, 0),
    "Tachycardia": ("EKG", "Metoprolol", 2),
    "Inflammation": ("CRP Test", "Ibuprofen", 3),
    "Tremor": ("Neurologic Exam", "Propranolol", 3),
    "Trouble swallowing": ("Barium Swallow", None, 0),
    "Ulcers": ("Endoscopy", "Omeprazole", 1),
    "Urinary pain": ("Urinalysis", "Nitrofurantoin", 2),
    "Urticaria": ("Allergy Skin Test", "Cetirizine", 1),
    "Vomiting": ("Abdominal Ultrasound", "Ondansetron", 2),
    "High blood pressure": ("Blood Pressure Measurement", "Lisinopril", 1),
    "Weight loss": ("TSH Test", None, 0),
    "Wheezing": ("Pulmonary Function Test", "Albuterol", 2),
    "Weakness": ("EMG", None, 0),
    "Yellow skin": ("Liver Function Tests", None, 0),
    "Chest tightness": ("EKG", "Aspirin", 1),
    "Cold sweats": ("Blood Glucose Test", None, 0),
    "Confusion": ("CT Head", None, 0),
    "Hot flashes": ("Hormone Panel", None, 0),
    "Paleness": ("CBC", "Iron Supplement", 1),
    "Ringing in ears": ("Audiometry", None, 0),
    "Excessive thirst": ("Blood Glucose Test", None, 0),
    "Dry cough": ("Chest X-ray", "Dextromethorphan", 4),
    "Aphasia": ("CT Head", None, 0),
    "Lightheadedness": ("Blood Pressure Measurement", None, 0),
    "Orthopnea": ("EKG", "Furosemide", 1),
    "Paresthesia": ("Nerve Conduction Study", "Gabapentin", 3),
    "Phlegm production": ("Chest X-ray", "Guaifenesin", 4),
    "Restlessness": ("Psychiatric Evaluation", None, 0),
    "Bloody stool": ("Colonoscopy", None, 0),
    "Tingling": ("Nerve Conduction Study", "Gabapentin", 3),
    "Vision loss": ("Fundoscopy", None, 0),
    "Voice changes": ("Laryngoscopy", None, 0),
    "Water retention": ("Kidney Function Tests", "Spironolactone", 1),
    "Internal bleeding": ("CT Scan", None, 0),
    "Zoster lesions": ("Skin Exam", "Acyclovir", 5),
    "Blisters": ("Dermatologic Exam", "Topical Acyclovir", 2),
    "Coma": ("CT Head", None, 0),
    "Burning sensation": ("Neurologic Exam", "Gabapentin", 3),
    "Cold intolerance": ("TSH Test", "Levothyroxine", 1),
    "Dry skin": ("Skin Exam", "Emollient Cream", 3),
    "Fainting": ("Tilt Table Test", None, 0),
    "Low blood pressure": ("Blood Pressure Measurement", "Fludrocortisone", 1),
    "Hair loss": ("Hormone Panel", "Minoxidil Topical", 2),
    "Hypersalivation": ("Salivary Gland Imaging", "Atropine Drops", 3),
    "Insomnia": ("Sleep Study", "Zolpidem", 1),
    "Gastroenteritis": ("Stool Culture", "Oral Rehydration Salts", 4),
    "Abcesses": ("Ultrasound", "Clindamycin", 4),
    "Jaundice": ("Liver Function Tests", None, 0),
    "Meningitis": ("Lumbar Puncture", "Ceftriaxone", 1),
    "Buboes": ("Lymph Node Biopsy", "Doxycycline", 2),
    "Pneumonia": ("Chest X-ray", "Azithromycin", 1)
}

# 2) CONDITIONS + dynamic mapping
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

# Helpers for condition mapping
DETECTOR_LOOKUP = {
    "Diabetes":       ["Hemoglobin A1c", "Fasting Blood Glucose Test"],
    "Neuro":          ["MRI Brain (without contrast)", "CT Head", "EEG (Electroencephalogram)"],
    "Cardio":         ["EKG", "Echocardiogram", "Stress Test"],
    "Respiratory":    ["Pulmonary Function Test", "Chest X-ray", "CT Chest"],
    "Liver":          ["Liver Function Tests", "Ultrasound (Abdominal)"],
    "Kidney":         ["Serum Creatinine", "Ultrasound (Kidney)"],
    "Musculoskeletal":["X-ray Joint", "MRI Joint", "Bone Density Scan"],
    "Cancer":         ["CT Scan", "PET Scan", "Biopsy"],
    "Infectious":     ["Blood Cultures", "Stool Culture", "Urinalysis"],
    "Shock":          ["Blood Gas (ABG)", "Lactate Level", "CBC"],
    "Autoimmune":     ["ANA Panel", "Rheumatoid Factor", "CRP"],
    "GI":             ["Endoscopy", "Colonoscopy", "Stool Occult Blood Test"],
    "Endocrine":      ["TSH Test", "Hormone Panel", "Cortisol Level"],
    "Trauma":         ["X-ray", "CT Scan", "MRI"]
}

CATEGORY_STATS = {
    "Diabetes":    (0.000003, 0.85 / 24),
    "Neuro":       (0.00002, 0.05 / 24),
    "Cardio":      (0.00025, 0.50 / 24),
    "Respiratory": (0.00017, 0.30 / 24),
    "Liver":       (0.00014, 0.20 / 24),
    "Kidney":      (0.00011, 0.35 / 24),
    "Musculoskeletal": (0.00001,1.00 / 24),
    "Cancer":      (0.00050, 0.40 / 24),
    "Infectious":  (0.00020, 0.60 / 24),
    "Shock":       (0.00100, 0.25 / 24),
    "Autoimmune":  (0.00002, 0.60 / 24),
    "GI":          (0.00005, 0.70 / 24),
    "Endocrine":   (0.00001, 0.90 / 24),
    "Trauma":      (0.00030, 0.50 / 24)
}
DEFAULT_STATS = (0.0001, 0.50 / 24)

def make_condition_details():
    details = {}
    for cond in CONDITIONS:
        # categorize
        if "Diabetes" in cond:
            cat="Diabetes"
        elif any(k in cond for k in ["Alzheimer","Parkinson","Stroke","Epilepsy","Migraine"]):
            cat="Neuro"
        elif any(k in cond for k in ["Heart","Cardio","Myocardial","Atrial","Coronary","Failure"]):
            cat="Cardio"
        elif any(k in cond for k in ["COPD","Asthma"]):
            cat="Respiratory"
        elif any(k in cond for k in ["Cirrhosis","Hepatitis"]):
            cat="Liver"
        elif any(k in cond for k in ["Kidney","Renal"]):
            cat="Kidney"
        elif any(k in cond for k in ["Fracture","Burn","Injury","Trauma"]):
            cat="Trauma"
        elif any(k in cond for k in ["Arthritis","Osteo","Fibromyalgia"]):
            cat="Musculoskeletal"
        elif any(k in cond for k in ["Cancer","Leukemia","Lymphoma","Melanoma","Sarcoma","Tumor"]):
            cat="Cancer"
        elif any(k in cond for k in ["Sepsis","Shock","Anaphylaxis","Dehydration"]):
            cat="Shock"
        elif any(k in cond for k in ["Autoimmune","Lupus"]):
            cat="Autoimmune"
        elif any(k in cond for k in ["Colitis","Irritable","Diverticulitis","Appendicitis","Endometriosis","Gastro"]):
            cat="GI"
        elif any(k in cond for k in ["Thyroidism","Cushing","Addison","Polycystic"]):
            cat="Endocrine"
        elif any(k in cond for k in ["Infection","Buboes"]):
            cat="Infectious"
        else:
            cat="DEFAULT"

        mort, cure = CATEGORY_STATS.get(cat, DEFAULT_STATS)
        cur_per_hour = cure / 24
        detectors = random.sample(DETECTOR_LOOKUP.get(cat, []), k=min(2,len(DETECTOR_LOOKUP.get(cat,[]))))
        symptoms = [{"name": s, "severity": random.randint(2,5)} for s in random.sample(SYMPTOM_LIST, k=3)]

        details[cond] = {
            "mortality_per_hour": mort,
            "curability": cur_per_hour,
            "detector_treatments": detectors,
            "possible_symptoms": symptoms
        }
    return details

def insert_symptoms():
    conn = get_db_connection()
    cur = conn.cursor()
    total = 0

    for name in SYMPTOM_LIST:
        proc, med, qty = SYMPTOM_TREATMENTS.get(name, (None, None, 0))

        # lookup IDs
        proc_id = None
        if proc:
            cur.execute("SELECT procedure_id FROM procedures WHERE name = %s;", (proc,))
            row = cur.fetchone()
            proc_id = row[0] if row else None

        med_id = None
        if med:
            cur.execute("SELECT medication_id FROM medications WHERE name = %s;", (med,))
            row = cur.fetchone()
            med_id = row[0] if row else None

        for sev in range(1, 6):
            cur.execute("""
                INSERT INTO symptoms (name, severity, procedure_id, medication_id, quantity)
                VALUES (%s, %s, %s, %s, %s);
            """, (name, sev, proc_id, med_id, qty))
            total += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {total} symptom entries.")

def insert_conditions():
    conn = get_db_connection()
    cur = conn.cursor()
    details = make_condition_details()
    total = 0

    for name, d in details.items():
        cur.execute("""
            INSERT INTO conditions
              (name, mortality_per_hour, curability, detector_treatments, possible_symptoms)
            VALUES (%s, %s, %s, %s, %s);
        """, (
            name,
            d["mortality_per_hour"],
            d["curability"],
            json.dumps(d["detector_treatments"]),
            json.dumps(d["possible_symptoms"])
        ))
        total += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {total} condition entries.")

if __name__ == "__main__":
    insert_symptoms()
    insert_conditions()
