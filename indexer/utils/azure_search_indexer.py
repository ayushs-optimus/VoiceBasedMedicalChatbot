import requests
import os
import logging

# Load from environment or config
AZURE_SEARCH_ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]  # e.g. https://<your-search>.search.windows.net
AZURE_SEARCH_API_KEY = os.environ["AZURE_SEARCH_API_KEY"]

endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
deployment_id = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
api_key = os.environ["AZURE_OPENAI_API_KEY"]
api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

HEADERS = {
    "Content-Type": "application/json",
    "api-key": AZURE_SEARCH_API_KEY
}

def upload_documents_to_index(index_name: str, documents: list):
    try:
        url = f"{AZURE_SEARCH_ENDPOINT}/indexes/{index_name}/docs/index?api-version=2023-10-01-Preview"
        payload = {
            "value": [
                {
                    "@search.action": "upload",
                    **doc
                } for doc in documents
            ]
        }

        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()

        logging.info(f"Successfully inserted {len(documents)} docs into '{index_name}'.")
        return response.json()
    except Exception as e:
        logging.error(f"Error inserting docs into '{index_name}': {str(e)}")
        raise

def generate_embedding(description: str) -> list:
    
    url = f"{endpoint}/openai/deployments/{deployment_id}/embeddings?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    body = {
        "input": description,
        "user": "embedding-generator"
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()

    embedding = response.json()["data"][0]["embedding"]
    return embedding