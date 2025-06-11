from typing import List, Dict, Any, Optional
import logging
import openai
import os
from azure.identity import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings
from app.services.telemetry import get_telemetry_client

logger = logging.getLogger(__name__)
telemetry_client = get_telemetry_client()

# Fix: import RateLimitError with fallback
try:
    from openai.error import RateLimitError
except ImportError:
    # fallback dummy RateLimitError in case openai.error is missing
    class RateLimitError(Exception):
        pass

class AzureOpenAIClient:
    """Client for Azure OpenAI API"""

    def __init__(self):

        settings = get_settings()

        # Configure OpenAI client for Azure
        openai.api_type = "azure"
        openai.api_base = settings.OPENAI_API_BASE
        openai.api_version = settings.AZURE_OPENAI_API_VERSION
        openai.api_key = settings.AZURE_OPENAI_KEY

        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT
        self.embedding_deployment = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT

        logger.info(f"Azure OpenAI client initialized for deployment {self.deployment_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)  # Use imported RateLimitError here
    )
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 800,
        stream: bool = False
    ) -> Dict[str, Any]:
        try:
            formatted_messages = []

            if system_message:
                formatted_messages.append({"role": "system", "content": system_message})

            formatted_messages.extend(messages)

            telemetry_client.track_event(
                "OpenAICompletion",
                {
                    "message_count": len(messages),
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )

            response = await openai.ChatCompletion.acreate(
                deployment_id=self.deployment_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )

            if stream:
                return response
            else:
                completion = response.choices[0].message.content

                telemetry_client.track_event(
                    "OpenAICompletionSuccess",
                    {
                        "completion_length": len(completion),
                        "finish_reason": response.choices[0].finish_reason
                    }
                )

                return {
                    "completion": completion,
                    "usage": response.usage.to_dict() if hasattr(response, 'usage') else None,
                    "created_at": response.created
                }

        except Exception as e:
            logger.exception(f"Error generating completion: {e}")
            telemetry_client.track_exception()
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(RateLimitError)  # Use imported RateLimitError here as well
    )
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            telemetry_client.track_event(
                "OpenAIEmbedding",
                {
                    "text_count": len(texts),
                    "avg_text_length": sum(len(t) for t in texts) / len(texts) if texts else 0
                }
            )

            response = await openai.Embedding.acreate(
                deployment_id=self.embedding_deployment,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]

            telemetry_client.track_event(
                "OpenAIEmbeddingSuccess",
                {
                    "embedding_count": len(embeddings)
                }
            )

            return embeddings

        except Exception as e:
            logger.exception(f"Error generating embeddings: {e}")
            telemetry_client.track_exception()
            raise


# Singleton client
_client = None

def get_openai_client() -> AzureOpenAIClient:
    global _client
    if _client is None:
        _client = AzureOpenAIClient()
    return _client
