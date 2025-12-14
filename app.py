import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Load environment variables from .env file BEFORE importing backend modules
load_dotenv()

from backend.chat import chat_with_ai_stream
from backend.storage import save_conversation, load_all_conversations
from frontend.utils import (
    create_new_conversation, 
    load_conversation, 
    delete_conversation_handler,
    check_authentication
)


# Page configuration
st.set_page_config(
    page_title="AI Travel Assistant",
    page_icon="✈️",
    layout="wide"
)

# Password protection
if not check_authentication():
    st.stop()

# Initialize session state
if "conversations" not in st.session_state:
    # Load conversations from storage
    st.session_state.conversations = load_all_conversations()
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# Auto-create a new conversation with welcome message if no conversation is active
if not st.session_state.current_conversation_id:
    create_new_conversation()

# Sidebar - Conversations Panel
with st.sidebar:
    st.title("✈️ Travel Assistant")
    
    # New conversation button
    if st.button("➕ New Conversation", use_container_width=True):
        create_new_conversation()
    
    st.divider()
    
    # Conversations list
    st.subheader("Conversations")
    
    # Display existing conversations
    if st.session_state.conversations:
        # Sort conversations by created_at timestamp (newest to oldest)
        sorted_conversations = sorted(
            st.session_state.conversations.items(),
            key=lambda x: x[1].get("created_at", "0000-00-00T00:00:00"),
            reverse=True
        )
        
        for conv_id, conv in sorted_conversations:
            title = conv.get("title", "Untitled")
            is_current = st.session_state.current_conversation_id == conv_id
            button_type = "primary" if is_current else "secondary"
            
            # Create a single row with title button and delete icon
            cols = st.columns([6, 2], gap="small")
            with cols[0]:
                if st.button(title, key=f"load_{conv_id}", use_container_width=True, type=button_type):
                    load_conversation(conv_id)
            with cols[1]:
                if st.button("🗑️", key=f"del_{conv_id}", help="Delete", type="secondary"):
                    delete_conversation_handler(conv_id)
    else:
        st.caption("No conversations yet. Create one to get started!")

# Main Chat Area
st.title("💬 Chat with AI Travel Assistant")

# Display chat messages
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about travel..."):
    # Add user message to session state
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)
    
    # Display the new user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Prepare conversation history for API (excluding the current message)
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages[:-1]  # Exclude the current user message
    ]
    
    # Get AI response with streaming
    with st.chat_message("assistant"):
        # Stream the response using Streamlit's write_stream
        response = st.write_stream(chat_with_ai_stream(prompt, conversation_history))
    
    # Add assistant message to session state
    assistant_message = {"role": "assistant", "content": response}
    st.session_state.messages.append(assistant_message)
    
    # Create a new conversation if one doesn't exist
    if not st.session_state.current_conversation_id:
        conversation_id = str(uuid.uuid4())
        conversation_data = {
            "id": conversation_id,
            "title": "New Conversation",
            "messages": st.session_state.messages.copy(),  # Use existing messages
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        st.session_state.conversations[conversation_id] = conversation_data
        st.session_state.current_conversation_id = conversation_id
        # Note: Don't clear st.session_state.messages here!
        save_conversation(conversation_id, conversation_data)
    
    # Save to storage and rerun to show the complete conversation
    if st.session_state.current_conversation_id:
        conv_id = st.session_state.current_conversation_id
        st.session_state.conversations[conv_id]["messages"] = st.session_state.messages
        st.session_state.conversations[conv_id]["updated_at"] = datetime.now().isoformat()
        # Update title if it's still "New Conversation"
        if len(st.session_state.messages) >= 2:
            first_user_msg = next((msg["content"] for msg in st.session_state.messages if msg["role"] == "user"), None)
            if first_user_msg:
                title = first_user_msg[:50] + "..." if len(first_user_msg) > 50 else first_user_msg
                if st.session_state.conversations[conv_id].get("title") != title:
                    st.session_state.conversations[conv_id]["title"] = title
        save_conversation(conv_id, st.session_state.conversations[conv_id])
    st.rerun()

