from typing import List, Dict, Any, Optional
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.config import get_settings
from app.services.telemetry import get_telemetry_client
from app.core.openai import get_openai_client

logger = logging.getLogger(__name__)
telemetry_client = get_telemetry_client()

class AzureSearchClient:
    def __init__(self):
        settings = get_settings()
        
        self.service_name = settings.AZURE_SEARCH_SERVICE
        self.index_name = settings.AZURE_SEARCH_INDEX
        self.api_version = settings.AZURE_SEARCH_API_VERSION
        self.credential = AzureKeyCredential(settings.AZURE_SEARCH_KEY)
        
        self.client = SearchClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            index_name=self.index_name,
            credential=self.credential,
            api_version=self.api_version
        )
        
        self.openai_client = get_openai_client()
        
        logger.info(f"Azure Search client initialized for index {self.index_name}")
    
    async def search(
        self,
        query: str,
        user_roles: List[str],
        filter: Optional[str] = None,
        top: int = 5,
        search_type: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """Search documents with role-based filtering"""
        try:
            # Create role-based filter
            role_filter = " or ".join([f"allowed_roles/any(r: r eq '{role}')" for role in user_roles])
            
            # Combine with existing filter
            combined_filter = f"({role_filter})"
            if filter:
                combined_filter = f"({role_filter}) and ({filter})"
            
            # Track in telemetry
            telemetry_client.track_event(
                "AzureSearch",
                {
                    "query": query,
                    "filter": combined_filter,
                    "top": top,
                    "search_type": search_type,
                    "user_roles": user_roles
                }
            )
            
            # Set up search options
            search_options = {
                "top": top,
                "query_type": "simple",
                "search_fields": ["content", "title"],
                "select": "*",
                "filter": combined_filter
            }
            
            # Generate embeddings for vector search
            vector_query = None
            if search_type in ["vector", "hybrid"]:
                embeddings = await self.openai_client.generate_embeddings([query])
                vector_query = VectorizedQuery(
                    vector=embeddings[0],
                    k_nearest_neighbors=top,
                    fields="contentVector"
                )
            
            # Perform search
            if search_type == "vector":
                search_options["vector_queries"] = [vector_query]
                search_options["search_text"] = None
                results = await self.client.search(
                    search_text=None, 
                    **search_options
                )
            elif search_type == "hybrid":
                search_options["vector_queries"] = [vector_query]
                results = await self.client.search(
                    search_text=query,
                    **search_options
                )
            else:
                results = await self.client.search(
                    search_text=query,
                    **search_options
                )
            
            # Process results
            documents = []
            async for result in results:
                documents.append(dict(result))
            
            return documents
            
        except Exception as e:
            logger.exception(f"Error searching documents: {e}")
            telemetry_client.track_exception()
            raise

# Singleton client
_client = None

def get_search_client() -> AzureSearchClient:
    """Get the Azure Search client singleton"""
    global _client
    if _client is None:
        _client = AzureSearchClient()
    return _client