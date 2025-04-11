"""
Utility functions for the RoboCo UI.

This module contains common utility functions used across the UI components.
"""

import os
import requests
import logging
import warnings
import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress handoff loop warnings
original_showwarning = warnings.showwarning

def custom_showwarning(message, category, filename, lineno, file=None, line=None):
    """Custom warning handler to filter out handoff loop warnings."""
    msg_str = str(message)
    if "Potential handoff loop detected" in msg_str:
        # Skip this warning
        return
    # For all other warnings, use the original handler
    original_showwarning(message, category, filename, lineno, file, line)

warnings.showwarning = custom_showwarning

# Also filter handoff warnings in log output
class HandoffWarningFilter(logging.Filter):
    """Filter to remove handoff loop warnings from logs."""
    def filter(self, record):
        if record.levelno == logging.WARNING and "Potential handoff loop detected" in record.getMessage():
            return False
        return True

# Apply the filter to the root logger
logging.getLogger().addFilter(HandoffWarningFilter())

def get_api_url() -> str:
    """Get the API URL from environment variables."""
    host = os.environ.get("HOST", "127.0.0.1")
    port = os.environ.get("PORT", "8000")
    return f"http://{host}:{port}"

def check_api_connection() -> bool:
    """Check if the API service is running."""
    try:
        response = requests.get(f"{get_api_url()}/health", timeout=2)
        st.session_state.api_connected = response.status_code == 200
        return st.session_state.api_connected
    except Exception as e:
        logger.warning(f"API connection failed: {str(e)}")
        st.session_state.api_connected = False
        return False

def init_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        # Initialize with an empty messages list
        st.session_state.messages = []
    if "project_id" not in st.session_state:
        st.session_state.project_id = None
    if "execution_log" not in st.session_state:
        st.session_state.execution_log = []
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    if "api_connected" not in st.session_state:
        st.session_state.api_connected = False
    if "last_update" not in st.session_state:
        st.session_state.last_update = datetime.now()
        
# CSS styles for the UI
def load_css():
    """Load minimal CSS styles for the UI."""
    css = """
    <style>
    /* Add a more formal font stack */
    .stApp {
        font-family: "Georgia", "Times New Roman", serif;
    }
    
    /* Headings with a more formal style */
    h1, h2, h3, h4, h5, h6 {
        font-family: "Helvetica Neue", Arial, sans-serif;
        font-weight: 500;
    }
    
    /* Minimal styles that work in light and dark mode */
    div.stChatMessage {
        margin-bottom: 1rem;
        max-width: 100%;
        overflow-wrap: break-word;
        word-wrap: break-word;
    }
    
    /* Keep the chat input visible at the bottom */
    div.stChatInputContainer {
        position: sticky !important;
        bottom: 0;
        padding-top: 1rem;
        margin-top: 1rem;
        z-index: 100;
        max-width: 100%;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def hide_raw_css():
    """Empty function to maintain backward compatibility."""
    pass

def fix_iframe_height():
    """Empty function to maintain backward compatibility."""
    pass
    
def clean_ui_display():
    """Apply minimal UI fixes without background colors or styles that break dark mode."""
    # Only apply minimal styling that works in both light and dark mode
    load_css() 