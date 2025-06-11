import streamlit as st
from datetime import datetime

# Dummy data to simulate backend response
def get_dummy_chat_sessions():
    return [
        {
            "id": "session1",
            "title": "Diabetes Info",
            "created_at": "2023-10-01 12:00:00",
            "message_count": 4,
            "first_message": "What are the symptoms of diabetes?"
        },
        {
            "id": "session2",
            "title": "Headache Help",
            "created_at": "2023-11-15 09:30:00",
            "message_count": 3,
            "first_message": "I've had a headache for 3 days..."
        }
    ]

def get_chat_messages(chat_id):
    """Dummy messages to simulate backend"""
    return [
        {
            "role": "user",
            "content": "What are the symptoms of diabetes?",
            "timestamp": "2023-10-01 12:00 PM",
            "username": "You"
        },
        {
            "role": "assistant",
            "content": "Common symptoms include increased thirst, frequent urination, and fatigue.",
            "timestamp": "2023-10-01 12:01 PM",
            "username": "AI Assistant",
            "thinking_process": [
                {"step": "Query understanding", "content": "Analyzing query about symptoms"},
                {"step": "Knowledge retrieval", "content": "Retrieving diabetes-related symptoms"}
            ]
        }
    ]

def display_history():
    """Display chat history for the current user"""
    user_id = st.session_state.get("user_id", "guest_user")

    chat_sessions = get_dummy_chat_sessions()

    if not chat_sessions:
        st.info("You don't have any chat history yet. Start a new chat to begin!")
        return

    st.subheader("Your Chat History")

    for session in chat_sessions:
        col1, col2 = st.columns([5, 1])

        with col1:
            created_at = session.get("created_at", "")
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                formatted_date = dt.strftime("%b %d, %Y at %I:%M %p")
            except:
                formatted_date = created_at

            first_message = session.get("first_message", "Empty chat")
            if len(first_message) > 60:
                first_message = first_message[:60] + "..."

            st.markdown(f"""
                <div style="background-color: #f9f9f9; border: 1px solid #ddd; padding: 1rem; border-radius: 10px;">
                    <h4>{session.get("title", f"Chat #{session['id']}")}</h4>
                    <p style="color: #718096; font-size: 0.8rem;">{formatted_date} · {session.get("message_count", 0)} messages</p>
                    <p>{first_message}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("View", key=f"view_{session['id']}"):
                st.session_state.selected_chat_id = session["id"]
                st.rerun()

    if "selected_chat_id" in st.session_state:
        display_chat_detail(st.session_state.selected_chat_id)

def display_chat_detail(chat_id):
    """Display detailed chat messages for a specific chat session"""
    st.subheader("Chat Details")

    if st.button("← Back to History"):
        del st.session_state.selected_chat_id
        st.rerun()

    messages = get_chat_messages(chat_id)

    if not messages:
        st.info("This chat session doesn't have any messages.")
        return

    for message in messages:
        role = message["role"]
        content = message["content"]
        timestamp = message["timestamp"]
        username = message["username"]

        if role == "user":
            st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
                    <div style="background-color: #DCF8C6; padding: 1rem; border-radius: 10px; max-width: 70%;">
                        <p>{content}</p>
                        <small style="color: #555; font-size: 0.7rem;">{username} · {timestamp}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 16px;">
                    <div style="background-color: #F1F0F0; padding: 1rem; border-radius: 10px; max-width: 70%;">
                        <p>{content}</p>
                        <small style="color: #555; font-size: 0.7rem;">AI Assistant · {timestamp}</small>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if message.get("thinking_process"):
                with st.expander("View AI thinking process"):
                    for step in message["thinking_process"]:
                        st.markdown(f"**{step['step']}**: {step['content']}")

    if st.button("Continue this chat"):
        st.session_state.current_chat_id = chat_id
        st.session_state.messages = [
            {
                "role": msg["role"],
                "content": msg["content"],
                "thinking_process": msg.get("thinking_process")
            }
            for msg in messages
        ]
        st.experimental_set_query_params(page="chat")
        st.rerun()

