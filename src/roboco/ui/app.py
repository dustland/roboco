"""
RoboCo web interface for chat and project management.

This provides a web interface for:
1. Chatting with RoboCo agents
2. Viewing execution status and progress
3. Exploring project files and tasks
4. Controlling the execution of tasks
"""

import streamlit as st
import os
from datetime import datetime

# Import from other modules
from roboco.ui.utils import init_session_state, check_api_connection, clean_ui_display
from roboco.ui.chat import chat_view
from roboco.ui.files import explore_project_files
from roboco.ui.status import update_execution_log
from roboco.ui.settings import settings_view
from roboco.ui.sidebar import sidebar_content

def main():
    """Main Streamlit application."""
    # Initialize session state
    init_session_state()
    
    # Check API connection
    api_connected = check_api_connection()
    
    # Set page config
    st.set_page_config(
        page_title="RoboCo Chat",
        page_icon="👽",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply all UI fixes and styling
    clean_ui_display()
    
    # Streamlit UI layout - simplified header
    st.markdown("## RoboCo Chat")
    
    if not api_connected:
        st.error("Cannot connect to RoboCo API. Make sure to start the API server with `roboco server --workers 4`")
        st.info("Run the command in a separate terminal and refresh this page")
        return
    
    # Simplified tabs without emojis
    tab1, tab2, tab3 = st.tabs(["Start Chat", "Project Files", "Settings"])
    
    with tab1:
        # Give the chat view more space by removing redundant headers
        chat_view()
    
    with tab2:
        st.subheader("Project Files")
        explore_project_files()
    
    with tab3:
        settings_view()
    
    # Add a sidebar with information
    with st.sidebar:
        sidebar_content()
    
    # Auto-update status every few seconds if project is active
    if st.session_state.project_id:
        update_execution_log()

if __name__ == "__main__":
    main() 