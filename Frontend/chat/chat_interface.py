import streamlit as st
import time
import uuid
import requests
import json

API_BASE = "http://localhost:8000/api"

def generate_session():
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

def get_ai_response_stream(query):
    payload = {
        "query": query,
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.current_chat_id,
        "stream": True
    }
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    try:
        response = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers, stream=True)
        return response if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

def get_ai_response(query):
    payload = {
        "query": query,
        "user_id": st.session_state.user_id,
        "session_id": st.session_state.current_chat_id
    }
    headers = {}
    if "access_token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"

    try:
        response = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            msg = data.get("message", "No output received from backend.")
            return msg.get("content", "No content provided"), msg.get("thinking_process", [])
        else:
            return f"Error {response.status_code}: {response.text}", []
    except requests.exceptions.RequestException as e:
        return f"Failed to connect to backend: {str(e)}", []
    except Exception as e:
        return f"Unexpected error: {str(e)}", []

def handle_streaming_response(response):
    full_response = ""
    thinking_process = []
    placeholder = st.empty()
    try:
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        json_data = json.loads(data)
                        if 'content' in json_data:
                            full_response += json_data['content']
                            placeholder.markdown(full_response)
                        if 'thinking_step' in json_data:
                            thinking_process.append(json_data['thinking_step'])
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        full_response = f"Error during streaming: {str(e)}"
    return full_response, thinking_process

def chat_page():
    if not st.session_state.get("authenticated", False):
        st.warning("Please login to access MediChat AI Assistant.")
        st.stop()

    generate_session()

    # Inject CSS for styling
    st.markdown("""
        <style>
html, body, [data-testid="stApp"] {
    height: 100%;
    margin: 0;
    padding: 0;
    overflow: hidden;
}

.chat-container {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    height: calc(100vh - 130px); /* Adjust height as needed */
    overflow-y: auto;
    padding: 0 16px;
    margin-bottom: 0;
}

.chat-bubble {
    padding: 10px 15px;
    border-radius: 20px;
    margin: 5px 0;
    max-width: 75%;
    word-wrap: break-word;
}

.user-message {
    background-color: #005c99;
    color: white;
    align-self: flex-end;
    margin-left: auto;
}

.assistant-message {
    background-color: #262730;
    color: #f0f0f0;
    align-self: flex-start;
    margin-right: auto;
}

.chat-row {
    display: flex;
}

.input-container {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    padding: 10px 16px;
    background-color: #0e1117;
    z-index: 10;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.4);
}
</style>

    """, unsafe_allow_html=True)

    # Header and controls
    col1, col2 = st.columns([0.75, 0.25])
    with col1:
        st.title("💬 MediChat AI Assistant")
        st.markdown(f"**Welcome, {st.session_state.get('user_name', 'User')}!**")
    with col2:
        if st.button("🔄 New Chat"):
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Chat display
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        msg_class = "user-message" if msg["role"] == "user" else "assistant-message"
        with st.container():
            st.markdown(f'''
                <div class="chat-row">
                    <div class="chat-bubble {msg_class}">
                        {msg["content"]}
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if msg.get("thinking_process") and msg["role"] == "assistant":
                with st.expander("🧠 View AI thinking process"):
                    for step in msg["thinking_process"]:
                        st.markdown(f"**{step['step']}**: {step['content']}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Input fixed at bottom
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    if user_input := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.markdown(f'''
            <div class="chat-row">
                <div class="chat-bubble user-message">
                    {user_input}
                </div>
            </div>
        ''', unsafe_allow_html=True)

        with st.spinner("Thinking..."):
            response = get_ai_response_stream(user_input)
            if response:
                full_response, thinking = handle_streaming_response(response)
            else:
                full_response, thinking = get_ai_response(user_input)
                st.markdown(f'''
                    <div class="chat-row">
                        <div class="chat-bubble assistant-message">
                            {full_response}
                        </div>
                    </div>
                ''', unsafe_allow_html=True)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "thinking_process": thinking
        })
    st.markdown('</div>', unsafe_allow_html=True)

