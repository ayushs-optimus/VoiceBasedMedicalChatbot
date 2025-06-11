from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Load environment variables
endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_SERVICE_ADMIN_API_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

# Create the search client
credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

filter_expression = (
    "(department_name eq 'diagnosis' and access/any(a: a eq 'doctor')) or " +
    "(department_name eq 'billing' and access/any(a: a eq 'admin'))"
)

results = search_client.search(search_text="*", filter=filter_expression)

print("Records matching the complex access and department criteria:")
for result in results:
    json_output = json.dumps(result, indent=2) 
    print(json_output)
    print("-" * 30)