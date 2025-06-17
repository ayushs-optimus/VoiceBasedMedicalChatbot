import uuid
import streamlit as st
import msal
import requests
import os
from dotenv import load_dotenv
load_dotenv()

# Azure AD config - replace these with your Azure AD app info
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = os.getenv("AUTHORITY")
REDIRECT_URI = os.getenv("REDIRECT_URI")

print("TENANT_ID:", TENANT_ID)
print("CLIENT_ID:", CLIENT_ID)
print("AUTHORITY:", AUTHORITY)
SCOPE = ["User.Read"] # Include User.Read if you still need to fetch user info from Graph

def get_msal_app():
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

def get_sign_in_url():
    msal_app = get_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
    )
    return auth_url

def get_token_from_code(auth_code):
    msal_app = get_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI,
    )
    if "access_token" in result:
        print("Raw Access Token from MSAL:", result["access_token"]) # <-- ADD THIS LINE
    return result

def get_user_info(access_token):
    # This function uses the access_token to call Microsoft Graph.
    # If the access_token has multiple audiences (Graph and your API),
    # it *might* work, but it's generally better to get separate tokens
    # for different resources if you need to call both.
    # For now, if 'User.Read' is in SCOPE, this should still work.
    graph_endpoint = "https://graph.microsoft.com/v1.0/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_data = requests.get(graph_endpoint, headers=headers).json()
    return user_data

def login_page():
    st.title("Login with Microsoft")

    print("Login page accessed", st.session_state)
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        auth_code = query_params["code"][0]
        token_response = get_token_from_code(auth_code)
        if "access_token" in token_response:
            user = get_user_info(token_response["access_token"])
            st.session_state.authenticated = True
            st.session_state.user_name = user.get("displayName")
            st.session_state.user_email = user.get("mail") or user.get("userPrincipalName")
            st.session_state.access_token = token_response["access_token"]
            # Initialize session data for chat
            st.session_state.user_id = str(uuid.uuid4())
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.success(f"Welcome {st.session_state.user_name}!")
            st.experimental_set_query_params()  # clear code param
            st.rerun()
        else:
            st.error("Failed to authenticate.")
            st.write(token_response.get("error_description", ""))
            # Also log more details for debugging the token response
            st.write("Full token response:", token_response)
    else:
        sign_in_url = get_sign_in_url()
        st.markdown(f'<a href="{sign_in_url}"><button>Login with Microsoft</button></a>', unsafe_allow_html=True)


def logout():
    """Clear session and logout"""
    st.session_state.clear()
    st.rerun()

def is_authenticated():
    """Check if the user is authenticated"""
    return st.session_state.get("authenticated", False)