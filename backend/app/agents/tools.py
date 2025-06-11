from typing import Dict, List, Any, Optional, Callable, Type
import logging
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.pydantic_v1 import BaseModel, Field
from pydantic import create_model

from app.core.search import get_search_client
from app.services.telemetry import get_telemetry_client

logger = logging.getLogger(__name__)
telemetry_client = get_telemetry_client()

# Define schemas for tool inputs
class SearchToolInput(BaseModel):
    query: str = Field(description="The search query")
    filter: Optional[str] = Field(None, description="Optional filter for search")
    top: int = Field(5, description="Number of results to return")

class CalculatorInput(BaseModel):
    expression: str = Field(description="The mathematical expression to evaluate")

# Search Tool
@tool("search", args_schema=SearchToolInput)
async def search_tool(query: str, filter: Optional[str] = None, top: int = 5) -> str:
    """
    Search for documents related to a query using Azure AI Search.
    
    Args:
        query: The search query
        filter: Optional filter expression
        top: Number of results to return
        
    Returns:
        String containing search results summary
    """
    try:
        telemetry_client.track_event(
            "AgentToolUsed", 
            {"tool": "search", "query": query}
        )
        
        search_client = get_search_client()
        results = await search_client.search(query=query, filter=filter, top=top)
        
        if not results:
            return "No results found for the query."
        
        # Format search results
        formatted_results = []
        for i, result in enumerate(results):
            title = result.get("title", f"Document {i+1}")
            content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
            source = result.get("source", "Unknown")
            
            formatted_result = f"[{i+1}] {title} (Source: {source})\n{content}\n"
            formatted_results.append(formatted_result)
        
        return "Search Results:\n\n" + "\n".join(formatted_results)
        
    except Exception as e:
        logger.exception(f"Error in search tool: {e}")
        telemetry_client.track_exception()
        return f"Error performing search: {str(e)}"

# Calculator Tool
@tool("calculator", args_schema=CalculatorInput)
def calculator_tool(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        String containing the result
    """
    try:
        telemetry_client.track_event(
            "AgentToolUsed", 
            {"tool": "calculator", "expression": expression}
        )
        
        # Safely evaluate the expression
        # Note: In a production environment, you would want to use a safer method
        # than eval() to evaluate mathematical expressions
        result = eval(expression)
        return f"The result of {expression} is {result}"
        
    except Exception as e:
        logger.exception(f"Error in calculator tool: {e}")
        telemetry_client.track_exception()
        return f"Error evaluating expression: {str(e)}"

# Get a list of all available tools
def get_agent_tools() -> List[Callable]:
    """Get all tools available for agents"""
    return [search_tool, calculator_tool]