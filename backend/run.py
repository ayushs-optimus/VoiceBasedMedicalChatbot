import uvicorn
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Determine environment
environment = os.getenv("ENVIRONMENT", "production").lower()

# Set logging level based on environment
log_level = "WARNING" if environment == "development" else os.getenv("LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Entry point to start the FastAPI application."""
    logger.info(f"Starting Voice-Based Medical Chatbot in {environment} mode...")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=(environment == "development")
    )


if __name__ == "__main__":
    main()
