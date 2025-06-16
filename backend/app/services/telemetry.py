import logging
from typing import Optional
from applicationinsights import TelemetryClient

from app.config import get_settings

logger = logging.getLogger(__name__)

# Singleton telemetry client
_telemetry_client = None

def get_telemetry_client() -> TelemetryClient:
    """
    Get the Application Insights telemetry client
    
    Returns:
        TelemetryClient: The telemetry client
    """
    global _telemetry_client
    if _telemetry_client is None:
        settings = get_settings()
        
        # Initialize the telemetry client
        _telemetry_client = TelemetryClient(settings.APPLICATIONINSIGHTS_CONNECTION_STRING)
        # print(f"Telemetry client initialized with connection string: {settings.APPLICATIONINSIGHTS_CONNECTION_STRING}")
        # print(f"Telemetry client: {_telemetry_client}")
        # Set common properties
        _telemetry_client.context.application.ver = "1.0.0"
        _telemetry_client.context.cloud.role = "rag-azure-app"
        
        logger.info("Application Insights telemetry client initialized")
        
    return _telemetry_client

def setup_app_insights() -> TelemetryClient:
    """
    Set up Application Insights
    
    Returns:
        TelemetryClient: The configured telemetry client
    """
    try:
        client = get_telemetry_client()
        
        # Configure telemetry processors if needed
        # ...
        
        # Send a test event
        client.track_event("ApplicationStarted")
        client.flush()
        
        return client
    except Exception as e:
        logger.warning(f"Failed to initialize Application Insights: {e}")
        # Return a dummy client that won't actually send telemetry
        dummy_client = TelemetryClient("")
        return dummy_client

def track_exception(exception: Exception, properties: Optional[dict] = None):
    """
    Track an exception in Application Insights
    
    Args:
        exception: The exception to track
        properties: Optional properties to include
    """
    try:
        client = get_telemetry_client()
        client.track_exception(exception, properties=properties)
        client.flush()
    except Exception as e:
        logger.warning(f"Failed to track exception in Application Insights: {e}")