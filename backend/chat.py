import os
import streamlit as st
from openai import OpenAI

def get_openai_client():
    """
    Get OpenAI client with API key from Streamlit secrets (Cloud) or environment variable (local).
    Initializes the client lazily to avoid import-time errors.
    """
    # Get API key from Streamlit secrets (Cloud) or environment variable (local)
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        # Fall back to environment variable for local development
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found. Please set it in Streamlit secrets (Cloud) or .env file (local)."
        )

    # Initialize and return OpenAI client
    return OpenAI(api_key=api_key)

def chat_with_ai_stream(message: str, conversation_history: list = None):
    """
    Main function to chat with OpenAI API with streaming.
    
    Args:
        message: User's message
        conversation_history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
    
    Yields:
        Chunks of the AI's response as strings
    """
    # System prompt explaining the role
    system_prompt = """You are a helpful travel assistant. Your role is to assist users with:
- Travel planning and recommendations
- Destination information and tips
- Itinerary suggestions
- Travel-related questions and advice
- Booking guidance and travel tips

Be friendly, informative, and provide practical travel advice."""
    
    # Prepare messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    try:
        # Get OpenAI client
        client = get_openai_client()
        
        # Call OpenAI API with streaming
        stream = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.7,
            stream=True
        )
        
        # Yield chunks as they come
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    except Exception as e:
        yield f"Error: {str(e)}"

