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

# Import application modules


def main():
    """Main function to run the Streamlit application."""
    if not is_authenticated():
        # Only show login page (MS login button)
        login_page()
    else:
        with st.sidebar:
            st.image("https://img.freepik.com/free-vector/gradient-medical-logo-design_23-2149605214.jpg", width=150)
            st.title(f"Welcome, {st.session_state.user_name}")

            selected = option_menu(
                menu_title="MediChat AI",
                options=["Chat", "History", "Feedback"] + (["Admin"] if st.session_state.user_role == "admin" else []),
                icons=["chat-dots-fill", "clock-history", "star-fill", "shield-lock-fill"],
                menu_icon="hospital",
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#f8f9fa"},
                    "icon": {"color": "#1565C0", "font-size": "16px"},
                    "nav-link": {
                        "font-size": "14px",
                        "text-align": "left",
                        "margin": "0px",
                        "padding": "10px",
                        "--hover-color": "#eee",
                    },
                    "nav-link-selected": {"background-color": "#1565C0", "color": "white"},
                },
            )
            

        if selected == "Chat":
            st.title("MediChat AI Assistant")
            chat_page()
            
        elif selected == "History":
            st.title("Chat History")
            from chat.history import display_history
            display_history()
        elif selected == "Feedback":
            st.title("User Feedback")
            view_user_feedback()
        else:
            st.warning("Something went wrong. Please try again.")


main()
