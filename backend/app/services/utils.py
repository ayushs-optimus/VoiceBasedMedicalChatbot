
from app.services.prompts import filter_query_prompt
from typing import Any, List, Tuple

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

async def generate_filter_query(query: str, patient_id : List[str],roles: List[str], llm: Any) -> str:
    
    roles_str = ', '.join([f"'{r}'" for r in roles])
    prompt = filter_query_prompt + f"\n\nUser Query:\n{query}\n\nRoles: {roles_str} \n\nPatient ID: {patient_id}\n\nGenerate a filter query for Azure Search that includes the patient ID and roles."
    
    try:
        response = await llm.ainvoke(prompt)
        print("Generated Filter:", response)
        return response.content.strip()
    except Exception as e:
        print("Error:", str(e))
        return f"Error generating filter: {str(e)}"
