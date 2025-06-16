tool_call_prompt = """
Flow logic:

1. If the user asks a question about a specific patient:
   - First, retrieve the patient's ID.
   - Then, generate a filter query using the patient ID and role.
   - Finally, fetch the patient's data.

2. If the user’s query is not specific to any patient:
   - call generate filter tool.
   - call tool to get data.
"""
