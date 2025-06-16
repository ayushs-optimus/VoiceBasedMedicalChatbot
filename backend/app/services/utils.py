

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
