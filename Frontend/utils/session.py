import streamlit as st

def initialize_session_state():
    """Initialize session state variables."""
    # print("Initializing session state variables")
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "thinking_process" not in st.session_state:
        st.session_state.thinking_process = []
    
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # print("Session state initialized:", st.session_state)