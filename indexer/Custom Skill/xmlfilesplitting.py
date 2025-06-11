    
import azure.functions as func
import logging
import json
import os
from azure.storage.blob import BlobServiceClient

from utils.xmlParser import parse_medical_record

apps = func.FunctionApp()

AZURE_STORAGE_CONNECTION_STRING = os.environ["AzureWebJobsStorage"]
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

@apps.blob_trigger(arg_name="myblob", path="medical-xml-data/{name}",
                               connection="AzureWebJobsStorage")
async def BlobTrigger(myblob: func.InputStream):
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

        output_container_name = "outputfiles"

        output_container_client = blob_service_client.get_container_client(output_container_name)
        try:
            output_container_client.create_container()
        except Exception as e:
            if "ContainerAlreadyExists" not in str(e):
                logging.warning(f"Could not create output container {output_container_name}: {e}")

        for i, dept_chunk in enumerate(departments):
            current_chunk_id = f"{original_file_name_without_ext}-{i}"

            output_json_data = {
                "chunk_id": current_chunk_id,
                "patient_id": dept_chunk.get("patient_id"),
                "department_name": dept_chunk.get("department_name"),
                "department_value": dept_chunk.get("department_value"),
                "access": dept_chunk.get("access")
            }

            department_name_for_filename = dept_chunk.get("department_name", "unknown").lower().replace(" ", "-")
            
            output_blob_name = f"{original_file_name_without_ext}-{department_name_for_filename}-{i}.json"
            
            output_blob_client = output_container_client.get_blob_client(output_blob_name)
            
            output_blob_client.upload_blob(json.dumps(output_json_data, indent=2), overwrite=True)
            logging.info(f"Successfully uploaded department chunk: {output_blob_name}")

    except Exception as e:
        logging.error(f"An error occurred while processing {myblob.name}: {str(e)}")
        raise