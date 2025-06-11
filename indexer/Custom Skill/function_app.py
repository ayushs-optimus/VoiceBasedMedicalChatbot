import azure.functions as func
import logging
import json
import uuid
from utils.xmlParser import parse_medical_record

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="ParseXmlHttpTrigger")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
             "Please pass a JSON body",
             status_code=400
        )

    # Prepare the overall response structure for Azure AI Search
    output_values = []

    for record in req_body.get("values", []):
        record_id = record.get("recordId")
        xml_content = record.get("data", {}).get("document")

        if not record_id:
            logging.warning("Skipping record with missing recordId.")
            continue
        if not xml_content:
            logging.warning(f"Skipping record {record_id} with missing document content.")
            output_values.append({
                "recordId": record_id,
                "data": {},
                "errors": [{"message": "Missing 'document' field in data."}],
                "warnings": []
            })
            continue

        try:
            parsed_data = parse_medical_record(xml_content)
            departments = parsed_data.get("departments", [])

            if not isinstance(departments, list):
                raise ValueError("Parsed 'departments' is not a list")

            # Initialize the structure for the single output record for this input record_id
            current_record_output = {
                "recordId": record_id,
                "data": {
                    "chunks": [] # This will hold all your department chunks
                },
                "errors": [],
                "warnings": []
            }

            # Populate the 'chunks' array within the 'data' field
            for i, dept in enumerate(departments):
                chunk_id = f"{record_id}-{i}" # Unique ID for each chunk within the main record

                current_record_output["data"]["chunks"].append({
                    "chunk_id": chunk_id, # Include the chunk_id if you want to reference it later
                    "patient_id": dept.get("patient_id"), # Ensure your parse_medical_record extracts this
                    "department_name": dept.get("department_name"),
                    "department_value": dept.get("department_value"),
                    "access": dept.get("access")
                })
            
            output_values.append(current_record_output)

        except Exception as e:
            logging.error(f"Error processing record {record_id}: {str(e)}")
            output_values.append({
                "recordId": record_id,
                "data": {},
                "errors": [{"message": f"Error processing XML: {str(e)}"}],
                "warnings": []
            })

    logging.info(f"Processed {len(output_values)} input records.")

    # Return all processed records in the expected Azure AI Search format
    return func.HttpResponse(
        json.dumps({"values": output_values}, indent=2),
        mimetype="application/json",
        status_code=200
    )


@app.blob_trigger(arg_name="myblob", path="xmlfilesplitting",
                               connection="AzureWebJobsStorage") 
def xmlFileSplittingblob(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")
