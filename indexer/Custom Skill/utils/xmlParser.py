import xml.etree.ElementTree as ET

def parse_medical_record(xml_content):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_content)

    patient_id = root.findtext("patient-id")

    departments = []
    for dept in root:
        dept_name = dept.tag
        
        # Skip elements that are not departments if needed
        if dept_name in ["patient-id", "description"]:
            continue

        # Get 'access' attribute as list, split by space if present, else empty list
        access_attr = dept.attrib.get("access", "")
        access_list = access_attr.split() if access_attr else []

        # Collect all text values inside the department and its children
        dept_texts = []
        for subelem in dept.iter():
            if subelem.text and subelem.text.strip():
                dept_texts.append(subelem.text.strip())
        dept_value = " ".join(dept_texts)

        departments.append({
            "patient_id": patient_id,
            "department_name": dept_name,
            "department_value": dept_value,
            "access": access_list
        })

    return {"patient_id": patient_id, "departments": departments}

