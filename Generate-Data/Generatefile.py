import random
import xml.etree.ElementTree as ET
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

chronic_conditions = ["Hypertension", "Diabetes", "Asthma", "COPD", "Hyperlipidemia"]
medications = [
    {"name": "Losartan", "dose": "50mg", "frequency": "Once daily"},
    {"name": "Metformin", "dose": "500mg", "frequency": "Twice daily"},
    {"name": "Albuterol", "dose": "90mcg", "frequency": "As needed"},
    {"name": "Atorvastatin", "dose": "20mg", "frequency": "Once daily"},
    {"name": "Lisinopril", "dose": "10mg", "frequency": "Once daily"}
]

def generate_record(patient_id):
    name = fake.name()
    dob = fake.date_of_birth(minimum_age=30, maximum_age=80)
    condition = random.choice(chronic_conditions)
    med = random.choice(medications)
    diagnosis_date = fake.date_between(start_date='-2y', end_date='today')
    follow_up_date = diagnosis_date + timedelta(days=30)
    lab_date = diagnosis_date
    cholesterol = random.randint(180, 250)
    bp = f"{random.randint(130, 160)}/{random.randint(80, 100)}"

    record = ET.Element("record")
    ET.SubElement(record, "patient-id").text = f"{patient_id:03d}"

    description = ET.SubElement(record, "description", access="doctor nurse")
    description.text = (
        f"{name} is a {datetime.now().year - dob.year}-year-old "
        f"{fake.random_element(elements=('male', 'female'))} with a history of {condition}. "
        "Presents with symptoms that require evaluation. Lab results and medications updated accordingly. "
        "Follow-up in one month."
    )

    demographics = ET.SubElement(record, "demographics", access="admin")
    ET.SubElement(demographics, "name").text = name
    ET.SubElement(demographics, "dob").text = dob.isoformat()
    ET.SubElement(demographics, "gender").text = fake.random_element(elements=("Male", "Female"))
    address = ET.SubElement(demographics, "address")
    ET.SubElement(address, "street").text = fake.street_address()
    ET.SubElement(address, "city").text = fake.city()
    ET.SubElement(address, "state").text = fake.state_abbr()
    ET.SubElement(address, "zip").text = fake.zipcode()
    contact = ET.SubElement(demographics, "contact")
    ET.SubElement(contact, "phone").text = fake.phone_number()
    ET.SubElement(contact, "email").text = fake.email()
    emergency_contact = ET.SubElement(demographics, "emergency-contact")
    ET.SubElement(emergency_contact, "name").text = fake.name()
    ET.SubElement(emergency_contact, "relation").text = fake.random_element(elements=["Spouse", "Parent", "Sibling", "Friend"])
    ET.SubElement(emergency_contact, "phone").text = fake.phone_number()

    medical_history = ET.SubElement(record, "medical-history", access="doctor nurse")
    ET.SubElement(medical_history, "allergies").text = fake.random_element(elements=["None", "Penicillin", "Sulfa drugs", "Aspirin"])
    ET.SubElement(medical_history, "chronic-conditions").text = condition
    ET.SubElement(medical_history, "past-surgeries").text = fake.sentence(nb_words=3)

    diagnosis = ET.SubElement(record, "diagnosis", access="doctor")
    ET.SubElement(diagnosis, "condition", code="I10").text = condition
    ET.SubElement(diagnosis, "diagnosis-date").text = diagnosis_date.isoformat()

    treatment = ET.SubElement(record, "treatment", access="doctor nurse")
    ET.SubElement(treatment, "treatment-plan").text = f"Start {med['name']} {med['dose']}"
    ET.SubElement(treatment, "follow-up").text = follow_up_date.isoformat()
    medications_elem = ET.SubElement(treatment, "medications")
    medication = ET.SubElement(medications_elem, "medication")
    ET.SubElement(medication, "name").text = med["name"]
    ET.SubElement(medication, "dose").text = med["dose"]
    ET.SubElement(medication, "frequency").text = med["frequency"]

    lab_results = ET.SubElement(record, "lab-results", access="doctor nurse")
    lab_test1 = ET.SubElement(lab_results, "lab-test")
    ET.SubElement(lab_test1, "name").text = "Blood Pressure"
    ET.SubElement(lab_test1, "value").text = bp
    ET.SubElement(lab_test1, "date").text = lab_date.isoformat()
    lab_test2 = ET.SubElement(lab_results, "lab-test")
    ET.SubElement(lab_test2, "name").text = "Cholesterol"
    ET.SubElement(lab_test2, "value").text = f"{cholesterol} mg/dL"
    ET.SubElement(lab_test2, "date").text = lab_date.isoformat()

    billing = ET.SubElement(record, "billing", access="insurance admin")
    ET.SubElement(billing, "total").text = str(random.randint(300, 500))
    ET.SubElement(billing, "insurance-provider").text = fake.company()
    itemized_charges = ET.SubElement(billing, "itemized-charges")
    for desc, amt in [("Consultation", 150), ("Lab Tests", 200)]:
        charge = ET.SubElement(itemized_charges, "charge")
        ET.SubElement(charge, "description").text = desc
        ET.SubElement(charge, "amount").text = str(amt)

    return ET.tostring(record, encoding="unicode")

# Generate and save 5 records
for i in range(1, 11):
    with open(f"patient_record_{i}.xml", "w", encoding="utf-8") as f:
        f.write(generate_record(i))
