import streamlit as st
import time
import uuid
import requests
import json

API_BASE = "https://containermedchat.thankfulsky-358fb2d4.westus2.azurecontainerapps.io/api"

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

    # Inject CSS with your color template
    st.markdown("""
        <style>
        /* CSS Variables from your template */
        :root {
            --background: oklch(0.9689 0.0090 314.7819);
            --foreground: oklch(0.3729 0.0306 259.7328);
            --card: oklch(1.0000 0 0);
            --card-foreground: oklch(0.3729 0.0306 259.7328);
            --popover: oklch(1.0000 0 0);
            --popover-foreground: oklch(0.3729 0.0306 259.7328);
            --primary: oklch(0.7090 0.1592 293.5412);
            --primary-foreground: oklch(1.0000 0 0);
            --secondary: oklch(0.9073 0.0530 306.0902);
            --secondary-foreground: oklch(0.4461 0.0263 256.8018);
            --muted: oklch(0.9464 0.0327 307.1745);
            --muted-foreground: oklch(0.5510 0.0234 264.3637);
            --accent: oklch(0.9376 0.0260 321.9388);
            --accent-foreground: oklch(0.3729 0.0306 259.7328);
            --destructive: oklch(0.8077 0.1035 19.5706);
            --destructive-foreground: oklch(1.0000 0 0);
            --border: oklch(0.9073 0.0530 306.0902);
            --input: oklch(0.9073 0.0530 306.0902);
            --ring: oklch(0.7090 0.1592 293.5412);
            --sidebar: oklch(0.9073 0.0530 306.0902);
            --sidebar-foreground: oklch(0.3729 0.0306 259.7328);
            --sidebar-primary: oklch(0.7090 0.1592 293.5412);
            --sidebar-primary-foreground: oklch(1.0000 0 0);
            --sidebar-accent: oklch(0.9376 0.0260 321.9388);
            --sidebar-accent-foreground: oklch(0.3729 0.0306 259.7328);
            --sidebar-border: oklch(0.9073 0.0530 306.0902);
            --sidebar-ring: oklch(0.7090 0.1592 293.5412);
            --radius: 1.5rem;
            --shadow: 0px 8px 16px -4px hsl(0 0% 0% / 0.08), 0px 1px 2px -5px hsl(0 0% 0% / 0.08);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --background: oklch(0.2161 0.0061 56.0434);
                --foreground: oklch(0.9299 0.0334 272.7879);
                --card: oklch(0.2805 0.0309 307.2326);
                --card-foreground: oklch(0.9299 0.0334 272.7879);
                --popover: oklch(0.2805 0.0309 307.2326);
                --popover-foreground: oklch(0.9299 0.0334 272.7879);
                --primary: oklch(0.7874 0.1179 295.7538);
                --primary-foreground: oklch(0.2161 0.0061 56.0434);
                --secondary: oklch(0.3416 0.0444 308.8496);
                --secondary-foreground: oklch(0.8717 0.0093 258.3382);
                --muted: oklch(0.2805 0.0309 307.2326);
                --muted-foreground: oklch(0.7137 0.0192 261.3246);
                --accent: oklch(0.3858 0.0509 304.6383);
                --accent-foreground: oklch(0.8717 0.0093 258.3382);
                --destructive: oklch(0.8077 0.1035 19.5706);
                --destructive-foreground: oklch(0.2161 0.0061 56.0434);
                --border: oklch(0.3416 0.0444 308.8496);
                --input: oklch(0.3416 0.0444 308.8496);
                --ring: oklch(0.7874 0.1179 295.7538);
                --sidebar: oklch(0.3416 0.0444 308.8496);
                --sidebar-foreground: oklch(0.9299 0.0334 272.7879);
                --sidebar-primary: oklch(0.7874 0.1179 295.7538);
                --sidebar-primary-foreground: oklch(0.2161 0.0061 56.0434);
                --sidebar-accent: oklch(0.3858 0.0509 304.6383);
                --sidebar-accent-foreground: oklch(0.8717 0.0093 258.3382);
                --sidebar-border: oklch(0.3416 0.0444 308.8496);
                --sidebar-ring: oklch(0.7874 0.1179 295.7538);
            }
        }

        /* Remove default Streamlit padding and margins */
        .main > div {
            padding-top: 0rem;
            padding-bottom: 0rem;
        }

        /* Hide Streamlit header and footer */
        header[data-testid="stHeader"] {
            display: none;
        }

        footer {
            display: none;
        }

        /* Main app container */
        html, body, [data-testid="stApp"] {
            height: 100vh;
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: var(--background);
            color: var(--foreground);
        }

        /* Sidebar styling */
        .css-1d391kg, .css-1cypcdb, .css-17eq0hr {
            background-color: var(--sidebar) !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        .css-1d391kg {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        section[data-testid="stSidebar"] {
            background-color: var(--sidebar) !important;
            border-right: 1px solid var(--sidebar-border);
            padding: 0 !important;
            margin: 0 !important;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-bottom: 1rem !important;
            background-color: var(--sidebar);
        }

        /* Sidebar buttons styling */
        .stButton > button {
            width: 100%;
            background-color: var(--sidebar-primary);
            color: var(--sidebar-primary-foreground);
            border: none;
            border-radius: calc(var(--radius) - 0.5rem);
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: var(--shadow);
        }

        .stButton > button:hover {
            background-color: var(--sidebar-accent);
            color: var(--sidebar-accent-foreground);
            border: none;
            transform: translateY(-1px);
        }

        .stButton > button:focus {
            border: 2px solid var(--sidebar-ring);
            box-shadow: 0 0 0 2px var(--sidebar-ring);
        }

        /* Main content area */
        .main .block-container {
            padding: 0 !important;
            max-width: none !important;
            margin: 0 !important;
            background-color: var(--background);
        }

        /* Chat container */
        .chat-container {
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            height: calc(100vh - 140px);
            overflow-y: auto;
            padding: 1.5rem;
            margin: 0;
            background-color: var(--background);
        }

        /* Chat bubbles */
        .chat-bubble {
            padding: 1rem 1.25rem;
            border-radius: var(--radius);
            margin: 0.5rem 0;
            max-width: 75%;
            word-wrap: break-word;
            font-size: 0.9rem;
            line-height: 1.5;
            box-shadow: var(--shadow);
            transition: all 0.2s ease;
        }

        .chat-bubble:hover {
            transform: translateY(-1px);
            box-shadow: 0px 12px 20px -6px hsl(0 0% 0% / 0.15);
        }

        .user-message {
            background-color: var(--primary);
            color: var(--primary-foreground);
            align-self: flex-end;
            margin-left: auto;
            border-bottom-right-radius: 0.5rem;
        }

        .assistant-message {
            background-color: var(--card);
            color: var(--card-foreground);
            align-self: flex-start;
            margin-right: auto;
            border-bottom-left-radius: 0.5rem;
            border: 1px solid var(--border);
        }

        .chat-row {
            display: flex;
            margin-bottom: 1rem;
        }

        /* Input container */
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: var(--background);
            padding: 1rem;
            border-top: 1px solid var(--border);
            z-index: 1000;
        }

        /* Chat input styling */
        .stChatInput > div > div {
            background-color: var(--input) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            transition: all 0.2s ease;
        }

        .stChatInput > div > div:focus-within {
            border-color: var(--ring) !important;
            box-shadow: 0 0 0 2px var(--ring) !important;
        }

        .stChatInput input {
            background-color: transparent !important;
            color: var(--foreground) !important;
            border: none !important;
        }

        .stChatInput input::placeholder {
            color: var(--muted-foreground) !important;
        }

        /* Spinner styling */
        .stSpinner > div {
            border-top-color: var(--primary) !important;
        }

        /* Expander styling for thinking process */
        .streamlit-expander {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-radius: calc(var(--radius) - 0.5rem);
            margin-top: 0.75rem;
            box-shadow: var(--shadow);
        }

        .streamlit-expander .streamlit-expanderHeader {
            color: var(--card-foreground);
            background-color: var(--card);
            border-radius: calc(var(--radius) - 0.5rem);
            padding: 0.75rem 1rem;
        }

        .streamlit-expander .streamlit-expanderContent {
            background-color: var(--muted);
            color: var(--muted-foreground);
            border-radius: 0 0 calc(var(--radius) - 0.5rem) calc(var(--radius) - 0.5rem);
        }

        /* Scrollbar styling */
        .chat-container::-webkit-scrollbar {
            width: 8px;
        }

        .chat-container::-webkit-scrollbar-track {
            background: var(--muted);
            border-radius: 4px;
        }

        .chat-container::-webkit-scrollbar-thumb {
            background: var(--muted-foreground);
            border-radius: 4px;
        }

        .chat-container::-webkit-scrollbar-thumb:hover {
            background: var(--accent);
        }

        /* Remove default Streamlit spacing */
        .element-container {
            margin-bottom: 0 !important;
        }

        .stMarkdown {
            margin-bottom: 0 !important;
        }

        /* Warning and info styling */
        .stAlert {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-radius: calc(var(--radius) - 0.5rem);
            color: var(--card-foreground);
        }

        /* Sidebar text styling */
        .css-1d391kg .markdown-text-container {
            color: var(--sidebar-foreground);
        }

        .css-1d391kg h3 {
            color: var(--sidebar-foreground);
        }

        .css-1d391kg p {
            color: var(--sidebar-foreground);
        }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar controls
    with st.sidebar:
        st.markdown("### MediChat AI")
        
        if st.button("🔄 Start New Chat"):
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        # Add some info about the current session
        st.markdown("---")
        st.markdown(f"**Session:** {st.session_state.current_chat_id[:8]}...")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")

    # Main chat area
    with st.container():
        for msg in st.session_state.messages:
            msg_class = "user-message" if msg["role"] == "user" else "assistant-message"
            align = "flex-end" if msg_class == "user-message" else "flex-start"

            st.markdown(f"""
            <div style='display: flex; justify-content: {align}; margin-bottom: 1rem;'>
                <div class='chat-bubble {msg_class}'>
                    {msg['content']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if msg.get("thinking_process") and msg["role"] == "assistant":
                with st.expander("🧠 View AI thinking process"):
                    for step in msg["thinking_process"]:
                        st.markdown(f"**{step['step']}**: {step['content']}")

    # Chat input at bottom
    user_input = st.chat_input("Type your messages...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            response = get_ai_response_stream(user_input)
            if response:
                full_response, thinking = handle_streaming_response(response)
            else:
                full_response, thinking = get_ai_response(user_input)

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "thinking_process": thinking
        })

        st.rerun()