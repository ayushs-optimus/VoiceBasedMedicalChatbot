import streamlit as st
from streamlit_option_menu import option_menu
from utils.session import initialize_session_state
from feedback.feedback_management import view_user_feedback
from chat.chat_interface import chat_page
from auth.authentication import login_page, is_authenticated

st.set_page_config(
    page_title="MediChat AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global theme styles
def apply_global_styles():
    st.markdown("""
        <style>
        :root {
  --background: oklch(0.9824 0.0013 286.3757);
  --foreground: oklch(0.3211 0 0);
  --card: oklch(1.0000 0 0);
  --card-foreground: oklch(0.3211 0 0);
  --primary: oklch(0.6487 0.1538 150.3071);
  --primary-foreground: oklch(1.0000 0 0);
  --sidebar: oklch(0.9824 0.0013 286.3757);
  --sidebar-foreground: oklch(0.3211 0 0);
  --radius: 0.5rem;
  --shadow: 0 1px 3px 0px hsl(0 0% 0% / 0.10), 0 1px 2px -1px hsl(0 0% 0% / 0.10);
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: oklch(0.2303 0.0125 264.2926);
    --foreground: oklch(0.9219 0 0);
    --card: oklch(0.3210 0.0078 223.6661);
    --card-foreground: oklch(0.9219 0 0);
    --primary: oklch(0.6487 0.1538 150.3071);
    --primary-foreground: oklch(1.0000 0 0);
    --sidebar: oklch(0.2303 0.0125 264.2926);
    --sidebar-foreground: oklch(0.9219 0 0);
  }
}


        [data-testid="stApp"] {
            background-color: var(--background);
            color: var(--foreground);
        }

        header[data-testid="stHeader"], footer { display: none; }

        section[data-testid="stSidebar"] {
            background-color: var(--sidebar) !important;
            border-right: 1px solid var(--primary);
        }

        /* Option Menu Wrapper */
        .menu-wrapper .nav.nav-pills {
            background-color: var(--card) !important;
            border-radius: var(--radius);
            padding: 0.5rem;
            box-shadow: var(--shadow);
        }

        .menu-wrapper .nav-link {
            color: var(--sidebar-foreground) !important;
            background-color: transparent !important;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
            border-radius: var(--radius);
            margin-bottom: 0.5rem;
            text-color: white !important;
        }

        .menu-wrapper .nav-link:hover {
            background-color: var(--primary) !important;
            color: var(--primary-foreground) !important;
            transform: translateX(4px);
        }

        .menu-wrapper .nav-link.active {
            background-color: var(--primary) !important;
            color: var(--primary-foreground) !important;
            box-shadow: var(--shadow);
        }

        .welcome-card, .session-info {
            background-color: var(--card);
            color: var(--card-foreground);
            border-radius: var(--radius);
            padding: 1rem;
            margin-bottom: 1rem;
            text-align: center;
            box-shadow: var(--shadow);
        }

        .profile-img {
            border-radius: 50%;
            border: 3px solid var(--primary);
            box-shadow: var(--shadow);
            margin-bottom: 0.5rem;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("""
        <style>
        /* Fix white background from Bootstrap injected by streamlit-option-menu */
        .menu-wrapper .nav,
        .menu-wrapper .nav-pills,
        .menu-wrapper .nav-pills .nav-link,
        .menu-wrapper .nav-pills .nav-link.active {
            background-color: var(--card) !important;
            color: var(--sidebar-foreground) !important;
            border-radius: var(--radius);
            transition: background-color 0.3s ease;
            border: none !important;
            box-shadow: none !important;
        }

        /* Hover and active states */
        .menu-wrapper .nav-pills .nav-link:hover {
            background-color: var(--sidebar-accent) !important;
            color: var(--sidebar-accent-foreground) !important;
            transform: translateX(4px);
        }

        .menu-wrapper .nav-pills .nav-link.active {
            background-color: var(--primary) !important;
            color: var(--primary-foreground) !important;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)


initialize_session_state()

def main():
    apply_global_styles()
    if not is_authenticated():
        login_page()
    else:
        show_main_app()

def show_main_app():
    with st.sidebar:
        # Welcome card
        st.markdown(f"""
            <div class="welcome-card">
                <img src="https://upload.wikimedia.org/wikipedia/commons/9/99/Sample_User_Icon.png" class="profile-img" width="80">
                <h4>Welcome!</h4>
                <p>{st.session_state.get('user_name', 'User')}</p>
            </div>
        """, unsafe_allow_html=True)

        # Navigation menu inside wrapper
        st.markdown('<div class="menu-wrapper">', unsafe_allow_html=True)


        selected = st.radio(
            "MediChat AI",
            options=["Chat", "History", "Feedback"] + (["Admin"] if st.session_state.get('user_role') == "admin" else []),
            index=0,
            key="main_menu"
        )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("""
            <style>
            /* Hide Streamlit radio group label */
            [data-testid="stRadio"] > label {
                display: none;
            }

            /* Style the whole radio block */
            [data-testid="stRadio"] {
                background-color: var(--card);
                padding: 1rem;
                border-radius: var(--radius);
                box-shadow: var(--shadow);
                color: var(--sidebar-foreground);
            }

            /* Style radio label text */
            [data-testid="stRadio"] div.row-widget.stRadio > div {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }

            /* Style individual radio buttons */
            div[data-testid="stRadio"] > div > label {
                display: flex;
                align-items: center;
                padding: 0.5rem;
                border-radius: var(--radius);
                transition: background-color 0.3s ease;
                cursor: pointer;
            }

            /* Circle indicator customization */
            div[data-testid="stRadio"] input[type="radio"] {
                accent-color: var(--primary);
                margin-right: 0.5rem;
            }

            /* Selected label style */
            div[data-testid="stRadio"] > div > label[data-baseweb="radio"] input:checked + div {
                color: var(--primary);
                font-weight: 600;
            }
            </style>
            """, unsafe_allow_html=True)



        # Session Info
        st.markdown(f"""
            <div class="session-info">
                <h4 style="margin-bottom: 0.5rem; color: var(--primary);">Session Info</h4>
                <p><strong>Session ID:</strong> <code>{st.session_state.get('current_chat_id', 'N/A')[:8] + '...' if st.session_state.get('current_chat_id') else 'N/A'}</code></p>
                <p><strong>Messages:</strong> {len(st.session_state.get('messages', []))}</p>
            </div>
        """, unsafe_allow_html=True)

    # Main content
    if selected == "Chat":
        # chat_page()
        print("Chat page is being developed.")
    elif selected == "History":
        st.markdown("""
            <div style="background-color: var(--card); border-radius: var(--radius); padding: 2rem; box-shadow: var(--shadow); text-align: center;">
                <h2 style="color: var(--primary); margin-bottom: 1rem;">📚 Chat History</h2>
                <p style="color: var(--foreground);">Your conversation history will appear here.</p>
            </div>
        """, unsafe_allow_html=True)
        try:
            from chat.history import display_history
            display_history()
        except ImportError:
            st.info("Chat history module is being developed.")
    elif selected == "Feedback":
        st.markdown("""
            <div style="background-color: var(--card); border-radius: var(--radius); padding: 2rem; box-shadow: var(--shadow); text-align: center;">
                <h2 style="color: var(--primary); margin-bottom: 1rem;">⭐ Feedback</h2>
                <p style="color: var(--foreground);">Share your experience with MediChat AI.</p>
            </div>
        """, unsafe_allow_html=True)
        try:
            view_user_feedback()
        except Exception:
            st.info("Feedback system is being set up.")
    elif selected == "Admin":
        st.markdown("""
            <div style="background-color: var(--card); border-radius: var(--radius); padding: 2rem; box-shadow: var(--shadow); text-align: center;">
                <h2 style="color: var(--primary); margin-bottom: 1rem;">🔒 Admin Panel</h2>
                <p style="color: var(--foreground);">Administrative functions and system management.</p>
            </div>
        """, unsafe_allow_html=True)
        for icon, label in zip(["👥", "📊", "⚙️"], ["User Management", "Analytics", "Settings"]):
            st.markdown(f"""
                <div style="background-color: var(--background); border-radius: var(--radius); padding: 1.5rem; text-align: center; margin-bottom: 1rem;">
                    <h4 style="color: var(--primary);">{icon} {label}</h4>
                    <p style="color: var(--foreground); font-size: 0.9rem;">Coming soon...</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.error("Invalid menu selection.")

if __name__ == "__main__":
    main()
