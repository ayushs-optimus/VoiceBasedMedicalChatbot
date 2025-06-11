import streamlit as st
import time
import uuid
import requests

API_BASE = "http://localhost:8000/api"

def generate_session():
    """Generate new user_id and session_id if not already present"""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

def get_ai_response(query):
    """Call backend API for AI response"""
    payload = {
        "query": query,
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.current_chat_id
    }
    headers = {}
    # Pass access token from MSAL login if available
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    try:
        response = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("🚨 Full response JSON from backend:\n", data)

            return data.get("output", "No output received from backend."), data.get("thinking_steps", [])

        else:
            return f"Error {response.status_code}: {response.text}", []

    except requests.exceptions.RequestException as e:
        return f"Failed to connect to backend: {str(e)}", []
    except Exception as e:
        return f"Unexpected error: {str(e)}", []


def display_chat_message(role, content):
    """Display chat message"""
    align = "flex-end" if role == "user" else "flex-start"
    color = "#DCF8C6" if role == "user" else "#F1F0F0"
    st.markdown(f"""
        <div style="display: flex; justify-content: {align}; margin-bottom: 1rem;">
            <div style="background-color: {color}; padding: 1rem; border-radius: 10px;">
                {content}
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_thinking_process(thinking_process):
    with st.expander("View AI thinking process"):
        for step in thinking_process:
            st.markdown(f"**{step['step']}**: {step['content']}")

def start_new_chat():
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()

def logout():
    st.session_state.clear()
    st.rerun()

def chat_page():
    # Check authentication before loading chat
    if not st.session_state.get("authenticated", False):
        st.warning("Please login to access MediChat AI Assistant.")
        st.stop()

    st.title(f"MediChat AI Assistant - Welcome {st.session_state.get('user_name', '')}")
    generate_session()

    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])
        if "thinking_process" in message:
            display_thinking_process(message["thinking_process"])

    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input(
                "Ask a medical question:",
                placeholder="e.g., What are the symptoms of diabetes?",
                label_visibility="collapsed"
            )
        with col2:
            submitted = st.form_submit_button("Send")

    if submitted and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        display_chat_message("user", user_input)

        with st.spinner("MediChat is thinking..."):
            response, thinking_process = get_ai_response(user_input)
            time.sleep(1)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "thinking_process": thinking_process
        })
        display_chat_message("assistant", response)
        display_thinking_process(thinking_process)

    st.sidebar.button("New Chat", on_click=start_new_chat)
    st.sidebar.button("Logout", on_click=logout)

# Run chat page directly (assumes login is handled separately)
