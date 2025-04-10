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
    """Load CSS styles for the UI."""
    css = """
    <style>
    /* Main styles for the UI */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        color: #1e293b;
    }

    /* Improve overall layout and spacing */
    .main {
        padding: 0 !important;
    }
    
    div.main div.block-container {
        padding: 1.5rem !important;
        max-width: 100%;
        overflow-x: hidden;
    }
    
    /* Better heading styles */
    h1, h2, h3, h4, h5, h6 {
        color: #18192c;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    h2 {
        font-size: 1.75rem;
        margin-bottom: 1.25rem;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }
    
    h3 {
        font-size: 1.35rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }
    
    h4 {
        color: #4b5563;
        font-size: 1.15rem;
        margin-top: 1.5rem;
        font-weight: 500;
    }
    
    /* Make the chat tab take up more space */
    div.stTabs {
        margin-top: 1rem;
    }

    div.stTabs > div[data-baseweb="tab-list"] {
        gap: 10px;
        margin-bottom: 0.5rem;
    }

    div.stTabs > div[data-baseweb="tab-list"] > button {
        border-radius: 6px 6px 0 0;
        padding: 10px 16px;
        font-weight: 500;
    }

    div.stTabs > div[data-baseweb="tab-list"] > button[aria-selected="true"] {
        background-color: #f1f5f9;
        border-bottom: 2px solid #3b82f6;
    }
    
    div.stTabs [data-baseweb="tab-panel"] {
        padding: 1.25rem;
        background-color: #f8fafc;
        border-radius: 0 6px 6px 6px;
        max-width: 100%;
        overflow-x: auto;
        border: 1px solid #e5e7eb;
    }
    
    /* Add horizontal scrolling to tables and long content */
    div.element-container {
        max-width: 100%;
        overflow-x: auto;
    }
    
    /* Constrain content width and enable horizontal scroll */
    .content-wrapper {
        max-width: 100%;
        overflow-x: auto;
        white-space: nowrap;
        padding: 0.5rem 0;
    }
    
    /* Better table styling with horizontal scroll */
    div.stDataFrame {
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
        border-radius: 6px;
    }
    
    /* Give more space to chat messages */
    div.stChatMessage {
        margin-bottom: 1rem;
        max-width: 100%;
        overflow-wrap: break-word;
        word-wrap: break-word;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
        padding: 0 0.25rem;
    }
    
    /* Keep the chat input visible at the bottom */
    div.stChatInputContainer {
        position: sticky !important;
        bottom: 0;
        background-color: white;
        padding-top: 1rem;
        margin-top: 1rem;
        z-index: 100;
        max-width: 100%;
        box-shadow: 0 -5px 15px rgba(0, 0, 0, 0.05);
        border-top: 1px solid #e5e7eb;
        padding: 1rem;
    }
    
    /* File browser styling */
    .file-item, .dir-item {
        padding: 10px 12px;
        border-radius: 6px;
        margin-bottom: 6px;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border: 1px solid #e5e7eb;
    }
    
    .file-item:hover, .dir-item:hover {
        background-color: #f1f5f9;
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05);
    }
    
    .dir-item {
        font-weight: 500;
        background-color: #f8fafc;
    }
    
    /* Directory and file path styling */
    .path-breadcrumb {
        background-color: #f1f5f9;
        padding: 10px 15px;
        border-radius: 6px;
        margin-bottom: 15px;
        font-family: 'SF Mono', 'Roboto Mono', 'Courier New', monospace;
        max-width: 100%;
        overflow-x: auto;
        white-space: nowrap;
        border: 1px solid #e5e7eb;
        color: #4b5563;
    }
    
    .path-breadcrumb a {
        color: #3b82f6;
        text-decoration: none;
        transition: color 0.2s;
    }
    
    .path-breadcrumb a:hover {
        color: #2563eb;
        text-decoration: underline;
    }
    
    /* File viewer */
    .file-header {
        display: flex;
        justify-content: space-between;
        padding: 12px 15px;
        background-color: #f1f5f9;
        border-radius: 6px 6px 0 0;
        max-width: 100%;
        overflow-x: auto;
        border: 1px solid #e5e7eb;
        border-bottom: none;
    }
    
    .file-content {
        border: 1px solid #e5e7eb;
        border-radius: 0 0 6px 6px;
        max-width: 100%;
        overflow-x: auto;
    }
    
    /* Fix sidebar width */
    section[data-testid="stSidebar"] {
        width: 300px !important;
        min-width: 250px !important;
        box-shadow: 2px 0 5px rgba(0, 0, 0, 0.05);
        background-color: #f8fafc;
    }
    
    section[data-testid="stSidebar"] > div {
        padding: 2rem 1rem;
    }
    
    /* Better styling for buttons */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        height: auto;
        transition: all 0.2s;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 10px 15px;
        border: 1px solid #e5e7eb;
        background-color: #f8fafc;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #f1f5f9;
        border-color: #cbd5e1;
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Primary buttons */
    .stButton > button[data-baseweb="button"] {
        background-color: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }
    
    .stButton > button[data-baseweb="button"]:hover {
        background-color: #2563eb;
        border-color: #2563eb;
    }
    
    /* Form styling */
    div[data-testid="stForm"] {
        padding: 1.5rem;
        border-radius: 6px;
        background-color: #f8fafc;
        border: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    
    /* Table styling for file lists */
    .file-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: separate;
        border-spacing: 0 5px;
    }
    
    .file-table td {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 10px;
        border-bottom: 1px solid #e5e7eb;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #4b5563;
        background-color: #f1f5f9;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 0.75rem 1rem;
    }
    
    .streamlit-expanderContent {
        border: 1px solid #e5e7eb;
        border-top: none;
        border-radius: 0 0 6px 6px;
        padding: 1rem;
        overflow-x: auto;
    }
    
    .streamlit-expander {
        margin-bottom: 1.5rem;
    }
    
    /* Code blocks should scroll horizontally */
    pre {
        white-space: pre;
        overflow-x: auto;
        max-width: 100%;
        border-radius: 6px;
        background-color: #1e1e1e !important;
    }
    
    /* Sample message buttons styling */
    div[data-testid="stVerticalBlock"] button {
        text-align: left;
        padding: 12px 16px;
        margin-bottom: 10px;
        font-size: 14px;
        background-color: #f8fafc;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        white-space: normal;
        overflow-wrap: break-word;
        word-wrap: break-word;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    div[data-testid="stVerticalBlock"] button:hover {
        background-color: #f1f5f9;
        border-color: #cbd5e1;
        transform: translateY(-1px);
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Hide pre/code blocks showing CSS */
    div.stMarkdown + div pre {
        display: none !important;
    }

    /* Chat messages improvements */
    [data-testid="stChatMessageContent"] > div > div > p {
        line-height: 1.6;
    }

    /* Info, warning, error message styling */
    [data-testid="stChatMessageContent"] .element-container [data-baseweb="notification"] {
        margin: 0.5rem 0;
        border-radius: 6px;
    }

    /* Chat tabs styling */
    div.stTabs div.stHorizontal {
        gap: 5px;
        padding-bottom: 0.5rem;
    }

    div.stTabs div.stHorizontal button[role="tab"] {
        background-color: #f1f5f9;
        border-radius: 6px;
        border: 1px solid #e5e7eb;
        padding: 5px 10px;
        gap: 5px;
        margin-right: 5px;
    }

    div.stTabs div.stHorizontal button[role="tab"][aria-selected="true"] {
        background-color: #e0f2fe;
        border-color: #93c5fd;
        color: #1d4ed8;
    }

    /* Input field styling */
    input[type="text"], textarea {
        border-radius: 6px !important;
        border: 1px solid #d1d5db !important;
    }

    input[type="text"]:focus, textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }

    /* Improve text input UI */
    div[data-baseweb="input"] {
        border-radius: 6px;
    }

    div[data-baseweb="base-input"] {
        background-color: white;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def hide_raw_css():
    """Hide raw CSS elements that might be showing incorrectly."""
    hide_style = """
        <style>
        /* Hide code blocks that might contain CSS */
        pre {
            display: none !important;
        }
        
        /* Hide any divs that might be showing CSS incorrectly */
        div:has(> pre:contains("/* Make the chat tab")) {
            display: none !important;
        }
        
        div:has(> pre:contains(".stTabs [data-baseweb")) {
            display: none !important;
        }
        
        /* Hide any paragraphs displaying CSS */
        p:contains("/* Make the chat tab") {
            display: none !important;
        }
        
        p:contains(".stTabs [data-baseweb") {
            display: none !important;
        }
        </style>
    """
    st.markdown(hide_style, unsafe_allow_html=True)

def fix_iframe_height():
    """Fix the height of iframes which might be causing rendering issues."""
    iframe_style = """
    <style>
    iframe {
        height: 0 !important;
        display: none !important;
    }
    
    /* Fix additional elements that might show CSS incorrectly */
    div.element-container:has(> div > pre:contains("/* Make the chat tab")) {
        display: none !important;
    }
    
    .stMarkdown pre {
        display: none !important;
    }
    </style>
    """
    st.markdown(iframe_style, unsafe_allow_html=True)
    
def clean_ui_display():
    """Apply all UI fixes to ensure proper rendering."""
    # Apply CSS styling
    load_css()
    
    # Hide any raw CSS
    hide_raw_css()
    
    # Fix iframe heights
    fix_iframe_height() 