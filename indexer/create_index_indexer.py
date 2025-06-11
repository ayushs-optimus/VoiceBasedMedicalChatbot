import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField,
    SearchIndexer, SearchIndexerDataSourceConnection,
    SearchIndexerDataContainer, SearchIndexerDataSourceType
)
from dotenv import load_dotenv
load_dotenv()

# Load environment variables or define directly
endpoint = os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_SERVICE_ADMIN_API_KEY")

index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")
data_source_name = os.getenv("AZURE_SEARCH_DATASOURCE_NAME")
indexer_name = os.getenv("AZURE_SEARCH_INDEXER_NAME")

connection_string = os.getenv("AZURE_SEARCH_DATA_SOURCE_URL")
container_name = os.getenv("AZURE_SEARCH_BLOB_CONTAINER_NAME")

skillset_name = os.getenv("AZURE_SEARCH_SKILLSET_NAME")

# Auth client
credential = AzureKeyCredential(api_key)
index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
indexer_client = SearchIndexerClient(endpoint=endpoint, credential=credential)

# Step 2: Create Data Source (Blob Storage)
data_source = SearchIndexerDataSourceConnection(
    name=data_source_name,
    type=SearchIndexerDataSourceType.AZURE_BLOB,
    connection_string=connection_string,
    container=SearchIndexerDataContainer(
        name=container_name,
        # This is where you configure parsing mode
        query=None,  # Optional if you're not filtering by virtual directory or filename
        parameters={"parsingMode": "json"}
    ),
    parsing_mode="json",
    description="Data source for Azure Blob Storage containing medical records in JSON format."
)
indexer_client.create_or_update_data_source_connection(data_source)
print(f"✅ Data source '{data_source_name}' created or updated.")


