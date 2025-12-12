import streamlit as st
import uuid
import os
from datetime import datetime

from backend.storage import save_conversation, delete_conversation


def check_authentication():
    """
    Check if user is authenticated with password protection.
    Returns True if authenticated, False otherwise.
    Shows login UI if not authenticated.
    Note: Authentication only persists during the current session.
    The correct password is read from st.secrets (Streamlit Cloud) or APP_PASSWORD env var (local).
    """
    # Get the correct password from Streamlit secrets (Cloud) or environment variable (local)
    try:
        correct_password = st.secrets["APP_PASSWORD"]
    except (KeyError, FileNotFoundError):
        # Fall back to environment variable for local development
        correct_password = os.getenv("APP_PASSWORD")
    
    if not correct_password:
        st.error("⚠️ APP_PASSWORD is not configured. Please set it in Streamlit secrets (Cloud) or .env file (local).")
        st.stop()
    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # If already authenticated, return True
    if st.session_state.authenticated:
        return True
    
    # Show login screen
    st.title("🔒 Welcome to AI Travel Assistant")
    st.write("Please enter the password to continue")
    
    user_password = st.text_input("Password", type="password", key="password_input")
    
    if st.button("Login", type="primary"):
        if user_password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    
    return False


def create_new_conversation():
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    conversation_data = {
        "id": conversation_id,
        "title": "New Conversation",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    st.session_state.conversations[conversation_id] = conversation_data
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = []
    # Save to storage
    save_conversation(conversation_id, conversation_data)


def load_conversation(conversation_id):
    """Load a conversation"""
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = st.session_state.conversations[conversation_id]["messages"]


def delete_conversation_handler(conversation_id):
    """Delete a conversation from session state and storage"""
    # Delete from storage
    delete_conversation(conversation_id)
    # Remove from session state
    if conversation_id in st.session_state.conversations:
        del st.session_state.conversations[conversation_id]
    # If it was the current conversation, clear it
    if st.session_state.current_conversation_id == conversation_id:
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
    # Rerun to update the UI
    st.rerun()

