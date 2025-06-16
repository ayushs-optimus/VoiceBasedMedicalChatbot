
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

        search_payload = {
            "search": "*",
            "filter": filter_query,
            "select": "*",
            "top": 5,
            "count": True,
            "queryType": "simple"
        }

        url = f"{setting.AZURE_SEARCH_ENDPOINT}/indexes/{setting.AZURE_SEARCH_INDEX_2}/docs/search"

        resp = requests.post(url, data=json.dumps(search_payload), headers=headers, params=params)

        search_results = resp.json()
        print(f"Search results: {search_results}")
        results = search_results.get("value", [])

        if results:
            return json.dumps(results[0], indent=2)
        else:
            return "No patient data found."

    except Exception as ex:
        logger.exception(f"Error fetching patient data: {ex}")
        return "Error fetching patient data."