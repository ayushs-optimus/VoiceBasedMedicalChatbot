
from app.services.prompts import filter_query_prompt
from typing import Any, List, Optional, Tuple

def get_message_type_and_content(msg):
    """Safely extract 'type' and 'content' from different message types."""
    if isinstance(msg, dict):
        return msg.get("type"), msg.get("message", msg.get("content"))
    elif hasattr(msg, "type") and hasattr(msg, "content"):
        return getattr(msg, "type", "Unknown"), getattr(msg, "content", "")
    elif hasattr(msg, "content"):
        return "AI", msg.content
    else:
        return "Unknown", str(msg)

async def generate_filter_query(
    query: str,
    patient_id: Optional[List[str]],
    roles: List[str],
    llm: Any
) -> str:    
    roles_str = ', '.join([f"'{r}'" for r in roles])
    prompt = filter_query_prompt + f"\n\nUser Query:\n{query}\n\nRoles: {roles_str}. patient_id: {patient_id}"
    
    try:
        response = await llm.ainvoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"Error generating filter: {str(e)}"
