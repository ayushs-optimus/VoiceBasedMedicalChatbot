from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from app.config import get_settings
from app.core.search import get_search_client
from app.core.openai import get_openai_client
from app.services.telemetry import get_telemetry_client

logger = logging.getLogger(__name__)
telemetry_client = get_telemetry_client()

class RAGEngine:
    """Retrieval-Augmented Generation engine"""
    
    def __init__(self):
        """Initialize the RAG engine"""
        settings = get_settings()
        
        # Initialize clients
        self.search_client = get_search_client()
        self.openai_client = get_openai_client()
        
        # Initialize LangChain components
        self.llm = AzureChatOpenAI(
            openai_api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
            openai_api_key=settings.AZURE_OPENAI_KEY,
            azure_endpoint=f"https://{settings.AZURE_OPENAI_SERVICE}.openai.azure.com",
            temperature=0.7
        )
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        
        # Set up RAG prompt template
        self.rag_prompt_template = ChatPromptTemplate.from_template("""
        You are an AI assistant that provides helpful, accurate, and concise answers.
        
        Use ONLY the following context to answer the question. If the context doesn't contain the answer, 
        say you don't know and avoid making up information.
        
        Context:
        {context}
        
        Question: {question}
        
        Answer in a professional and conversational tone. Include relevant specific details from the context when appropriate.
        """)
        
        # Create LangChain for RAG
        self.rag_chain = LLMChain(
            llm=self.llm,
            prompt=self.rag_prompt_template
        )
        
        logger.info("RAG engine initialized")
    
    async def _retrieve_documents(
        self,
        query: str,
        filter: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from Azure Search
        
        Args:
            query: The search query
            filter: Optional filter
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        try:
            # Get documents from search
            documents = await self.search_client.search(
                query=query,
                filter=filter,
                top=top_k,
                search_type="hybrid"
            )
            
            return documents
        except Exception as e:
            logger.exception(f"Error retrieving documents: {e}")
            telemetry_client.track_exception()
            raise
    
    async def _format_context_from_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> str:
        """
        Format documents into context string
        
        Args:
            documents: List of documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents):
            # Extract content and metadata
            content = doc.get("content", "")
            title = doc.get("title", f"Document {i+1}")
            source = doc.get("source", "Unknown")
            
            # Format document
            doc_text = f"[{i+1}] {title} (Source: {source})\n{content}\n"
            context_parts.append(doc_text)
        
        return "\n".join(context_parts)
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        use_retrieval: bool = True,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a completion with RAG
        
        Args:
            messages: List of message dictionaries
            system_message: Optional system message
            use_retrieval: Whether to use retrieval
            search_query: Optional explicit search query
            
        Returns:
            Dict with the answer and any additional information
        """
        try:
            # Start timing
            start_time = datetime.now()
            
            # Get the user's last question
            last_user_message = None
            for message in reversed(messages):
                if message["role"] == "user":
                    last_user_message = message["content"]
                    break
            
            if not last_user_message:
                return {
                    "answer": "I couldn't find a question to answer.",
                    "created_at": datetime.now().isoformat()
                }
            
            # Determine query for retrieval
            query = search_query or last_user_message
            
            # Track in telemetry
            telemetry_client.track_event(
                "RAGCompletion",
                {
                    "message_count": len(messages),
                    "use_retrieval": use_retrieval,
                    "has_search_query": search_query is not None
                }
            )
            
            if use_retrieval:
                # Retrieve relevant documents
                documents = await self._retrieve_documents(query=query)
                
                # Format context from documents
                context = await self._format_context_from_documents(documents)
                
                # Get answer using RAG
                response = await self.rag_chain.arun(
                    context=context,
                    question=last_user_message
                )
                
                # Format citations
                citations = [
                    {
                        "title": doc.get("title", ""),
                        "source": doc.get("source", ""),
                        "content": doc.get("content", "")[:200] + "...",
                        "id": doc.get("id", "")
                    }
                    for doc in documents
                ]
                
                result = {
                    "answer": response,
                    "citations": citations,
                    "retrieval_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    "created_at": datetime.now().isoformat()
                }
            else:
                # Use regular chat completion without retrieval
                openai_response = await self.openai_client.generate_completion(
                    messages=messages,
                    system_message=system_message
                )
                
                result = {
                    "answer": openai_response["completion"],
                    "created_at": datetime.now().isoformat()
                }
            
            # Track success
            telemetry_client.track_event(
                "RAGCompletionSuccess",
                {
                    "response_length": len(result["answer"]),
                    "citation_count": len(result.get("citations", [])),
                    "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            )
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in RAG completion: {e}")
            telemetry_client.track_exception()
            raise

# Singleton engine
_engine = None

def get_rag_engine() -> RAGEngine:
    """Get the RAG engine singleton"""
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine