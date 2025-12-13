"""OpenAI client management and utilities."""

import os
import streamlit as st
from openai import OpenAI
from datetime import datetime
from zoneinfo import ZoneInfo


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


def get_runtime_context():
    """
    Generate runtime context with current date and time.
    This should be computed fresh on every LLM request and NOT persisted in conversation history.
    
    Returns:
        String with formatted runtime context
    """
    now = datetime.now()
    
    # Try to get system timezone, fallback to UTC
    try:
        tz = now.astimezone().tzname()
    except:
        tz = "UTC"
    
    context = f"""Runtime Context:
Current date: {now.strftime('%Y-%m-%d')}
Current time: {now.strftime('%H:%M:%S')}
Timezone: {tz}

Interpret relative dates (e.g., "next month", "this weekend", "in 2 weeks") relative to the current date above."""
    
    return context
