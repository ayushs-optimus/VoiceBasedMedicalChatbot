from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    # Azure OpenAI
    AZURE_OPENAI_SERVICE: str
    AZURE_OPENAI_DEPLOYMENT: str
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_API_VERSION: str
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str
    Azure_OPENAI_ENDPOINT: str
    
    # Azure AI Search
    AZURE_SEARCH_SERVICE: str
    AZURE_SEARCH_KEY: str
    AZURE_SEARCH_INDEX: str
    AZURE_SEARCH_API_VERSION: str
    
    # Azure Blob Storage
    AZURE_BLOB_STORAGE_ACCOUNT: str
    AZURE_BLOB_STORAGE_CONTAINER: str
    AZURE_BLOB_STORAGE_KEY: str
    
    # Azure Form Recognizer
    AZURE_FORM_RECOGNIZER_ENDPOINT: str
    AZURE_FORM_RECOGNIZER_KEY: str
    
    # Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING: str
    
    # Azure AD Settings
    AZURE_AD_TENANT_ID: str
    AZURE_AD_CLIENT_ID: str
    AZURE_AD_CLIENT_SECRET: str
    
    # App Settings
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Azure Cosmos DB
    AZURE_COSMOS_DB_ENDPOINT: str
    AZURE_COSMOS_DB_KEY: str
    AZURE_COSMOS_DB_DATABASE: str
    AZURE_COSMOS_DB_CONTAINER: str
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        return self.ALLOWED_ORIGINS
    
    @property
    def OPENAI_API_BASE(self) -> str:
        return f"https://{self.AZURE_OPENAI_SERVICE}.openai.azure.com"
    
    @property
    def SEARCH_ENDPOINT(self) -> str:
        return f"https://{self.AZURE_SEARCH_SERVICE}.search.windows.net"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()
