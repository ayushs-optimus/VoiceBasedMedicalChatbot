
import json
import logging 
import requests
from app.config import get_settings

logger = logging.getLogger(__name__)

setting = get_settings()
async def get_patient_data(filter_query: str) -> str:
    try:
        print(f"filter query: {filter_query}")

        headers = {
            'Content-Type': 'application/json',
            'api-key': setting.AZURE_SEARCH_KEY
        }

        params = {
            'api-version': setting.AZURE_SEARCH_API_VERSION
        }

        search_payload_2 ={
            "search": filter_query,
            "count": True,
            "queryType": "semantic",
            "semanticConfiguration": "default-department-config",
            "captions": "extractive",
            "answers": "extractive|count-3",
            "queryLanguage": "en-us",
        }

        url = f"{setting.AZURE_SEARCH_ENDPOINT}/indexes/{setting.AZURE_SEARCH_INDEX_2}/docs/search"

        resp = requests.post(url, data=json.dumps(search_payload_2), headers=headers, params=params)

        search_results = resp.json()
        results = search_results.get("value", [])
        print(f"Search results: {json.dumps(results, indent=2)}")

        if results:
            return json.dumps(results, indent=2)
        else:
            return "No patient data found."

    except Exception as ex:
        logger.exception(f"Error fetching patient data: {ex}")
        return "Error fetching patient data."