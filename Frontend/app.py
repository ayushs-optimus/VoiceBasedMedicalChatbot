import streamlit as st
from streamlit_option_menu import option_menu
from utils.session import initialize_session_state
from utils.styles import apply_custom_styles
from feedback.feedback_management import view_user_feedback
from chat.chat_interface import chat_page
from auth.authentication import login_page, is_authenticated

st.set_page_config(
    page_title="MediChat AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_session_state()
apply_custom_styles()

def main():
    if not is_authenticated():
        login_page()
    else:
        show_main_app()

def show_main_app():
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/9/99/Sample_User_Icon.png?20200919003010",
            width=80
        )
        st.markdown(f"""
            <div style="text-align: center;">
                <h4 style="margin-bottom: 0;">Welcome!</h4>
                <p style="margin-top: 0;">{st.session_state.user_name}</p>
            </div>
        """, unsafe_allow_html=True)

        selected = option_menu(
            menu_title="MediChat AI",
            options=["Chat", "History", "Feedback"] + (["Admin"] if st.session_state.user_role == "admin" else []),
            icons=["chat-dots-fill", "clock-history", "star-fill", "shield-lock-fill"],
            menu_icon="hospital",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#1565C0", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "0px",
                    "padding": "12px 16px",
                    "border-radius": "8px",
                    "margin-bottom": "4px",
                    "--hover-color": "var(--shadow-light)",
                    "color": "var(--text-color)",
                },
                "nav-link-selected": {
                    "background-color": "#1565C0", 
                    "color": "white",
                    "font-weight": "500"
                },
            },
        )

        st.markdown("---")
        st.markdown("### Session Info")
        st.markdown(f"**Session ID:** `{st.session_state.get('current_chat_id', 'N/A')[:8]}...`")
        st.markdown(f"**Messages:** {len(st.session_state.get('messages', []))}")

    if selected == "Chat":
        chat_page()
    elif selected == "History":
        from chat.history import display_history
        display_history()
    elif selected == "Feedback":
        view_user_feedback()
    elif selected == "Admin":
        st.title("🔒 Admin Panel")
        st.info("Admin functionality under construction.")
    else:
        st.error("Something went wrong. Please try again.")

if __name__ == "__main__":
    main()
