import azure.functions as func
import logging
import json
import os
import uuid

from utils.xmlParser import parse_medical_record
from utils.azure_search_indexer import upload_documents_to_index , generate_embedding  

app = func.FunctionApp()

department_index = os.environ["Azure_Department_index_name"]
description_index = os.environ["Azure_description_index_name"]

@app.blob_trigger(arg_name="myblob", path="medical-xml-data/{name}",
                  connection="AzureWebJobsStorage")
async def BlobTriggerMedicalXml(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob: {myblob.name}")
    logging.info(f"Blob Size: {myblob.length} bytes")

    try:
        xml_content = myblob.read().decode('utf-8')

        original_blob_full_path = myblob.name
        original_blob_name_with_ext = os.path.basename(original_blob_full_path)
        original_file_name_without_ext = os.path.splitext(original_blob_name_with_ext)[0]

        parsed_data = parse_medical_record(xml_content)
        departments = parsed_data.get("departments", [])

        if not isinstance(departments, list):
            logging.error(f"Error: Parsed 'departments' is not a list for blob {myblob.name}")
            return

        logging.info(f"Found {len(departments)} departments in {original_file_name_without_ext}.")

        chunk_documents = []
        description_documents = []

        for i, dept_chunk in enumerate(departments):
            department_name = dept_chunk.get("department_name", "").lower()
            current_chunk_id = f"{original_file_name_without_ext}-{i}"

            if department_name == "description":
                patient_id = dept_chunk.get("patient_id")
                description_value = dept_chunk.get("department_value")
                if patient_id and description_value:
                    description_documents.append({
                        "patient_id": patient_id,
                        "description": description_value
                    })
                continue

            chunk_data = {
                "id": current_chunk_id,
                "patient_id": dept_chunk.get("patient_id"),
                "department_name": dept_chunk.get("department_name"),
                "department_value": dept_chunk.get("department_value"),
                "access": dept_chunk.get("access")
            }

            chunk_documents.append(chunk_data)

        # Upload documents to Azure Cognitive Search indexes
        if chunk_documents:
            upload_documents_to_index(department_index,chunk_documents)
            logging.info(f"Uploaded {len(chunk_documents)} documents to department index '{department_index}'")

        if description_documents:
            doc = description_documents[0]
            description_text = doc.get("description")
            patient_id = doc.get("patient_id")

            if description_text and patient_id:
                embedding_vector = generate_embedding(description_text)

                enriched_doc = {
                    "id": str(uuid.uuid4()),
                    "patient_id": patient_id,
                    "description": description_text,
                    "description_vector": embedding_vector
                }

                upload_documents_to_index(description_index, [enriched_doc])
                logging.info(f"Uploaded 1 document to description index '{description_index}'")


    except Exception as e:
        logging.error(f"An error occurred while processing {myblob.name}: {str(e)}")
        raise
