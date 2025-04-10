"""
Settings functionality for the RoboCo UI.

This module contains functions for managing RoboCo settings and project selection.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from loguru import logger

from roboco.ui.api import get_all_projects
from roboco.ui.utils import get_api_url
from roboco.ui.status import update_execution_log

def settings_view():
    """Render the settings interface."""
    st.subheader("Settings")
    
    # API settings
    st.write("API Connection")
    api_url = get_api_url()
    st.code(f"Connected to: {api_url}")
    
    # Load existing projects
    st.write("Existing Projects")
    projects = get_all_projects()
    if projects:
        project_options = [f"{p.get('id', 'Unknown')} - {p.get('name', 'Untitled')}" for p in projects]
        selected_project = st.selectbox(
            "Load existing project:",
            options=project_options
        )
        
        if st.button("Load Selected Project"):
            try:
                # Extract project ID from selection
                project_id = selected_project.split(" - ")[0]
                
                # Reset current state
                st.session_state.messages = []
                st.session_state.project_id = project_id
                st.session_state.execution_log = []
                
                # Update execution log
                update_execution_log()
                st.success(f"Loaded project: {selected_project}")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading project: {str(e)}")
    else:
        st.info("No existing projects found.")
        
    # Environmental variables
    st.write("Environment Variables")
    with st.expander("Environment Settings"):
        st.write("These settings affect how RoboCo operates. You may need to restart the server for changes to take effect.")
        
        # Host setting
        current_host = get_api_url().split("://")[1].split(":")[0]
        new_host = st.text_input("API Host", value=current_host)
        
        # Port setting
        current_port = get_api_url().split(":")[-1]
        new_port = st.text_input("API Port", value=current_port)
        
        # Worker setting
        workers = st.number_input("API Workers", min_value=1, max_value=16, value=4)
        
        if st.button("Apply Settings"):
            st.warning("Settings application is not implemented yet. Please set these values in your environment variables.")
            st.code(f"""
            # Bash/ZSH:
            export HOST="{new_host}"
            export PORT="{new_port}"
            export WORKERS="{workers}"
            
            # Windows CMD:
            set HOST={new_host}
            set PORT={new_port}
            set WORKERS={workers}
            """)
    
    # Advanced options
    st.write("Advanced Options")
    with st.expander("Danger Zone"):
        st.warning("These actions can cause data loss. Use with caution.")
        
        if st.button("Clear Session Data", type="primary"):
            # Reset the session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Re-initialize the session state
            from roboco.ui.utils import init_session_state
            init_session_state()
            
            st.success("Session data cleared successfully!")
            st.rerun() 