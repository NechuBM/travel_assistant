"""OpenAI client management."""

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
