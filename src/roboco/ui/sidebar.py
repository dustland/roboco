"""
Sidebar functionality for the RoboCo UI.

This module contains functions for rendering the sidebar with project information and controls.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from loguru import logger

from roboco.ui.utils import check_api_connection
from roboco.ui.status import update_execution_log

def sidebar_content():
    """Render the sidebar content."""
    # Logo and header using native Streamlit components
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://raw.githubusercontent.com/dustland/roboco/main/assets/logo.png", width=64)
    with col2:
        st.title("RoboCo")
        
    st.caption("Solve complex problems with AI.")
    
    # Add a divider
    st.divider()
    
    # API connection status using native Streamlit components
    if st.session_state.api_connected:
        st.success("✓ Server Connected")
    else:
        st.error("✗ Server Disconnected")
        
        if st.button("Retry Connection", use_container_width=True):
            st.session_state.api_connected = check_api_connection()
            st.rerun()
    
    # New chat button
    if st.button("New Chat", key="new_chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.project_id = None
        st.session_state.execution_log = []
        st.session_state.tasks = []
        st.success("New chat started!")
        st.rerun()
    
    # Active project info
    if st.session_state.project_id:
        st.subheader("Active Project")
        st.code(st.session_state.project_id, language=None)

    # Task progress metrics using native Streamlit components
    if st.session_state.project_id and st.session_state.tasks:
        completed_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "COMPLETED")
        total_tasks = len(st.session_state.tasks)
        failed_tasks = sum(1 for task in st.session_state.tasks if task.get("status", "").upper() == "FAILED")
        
        if total_tasks > 0:
            completion_percentage = int(completed_tasks / total_tasks * 100)
            
            # Task completion metric
            st.subheader("Task Completion")
            st.progress(value=completed_tasks/total_tasks)
            st.text(f"{completion_percentage}% ({completed_tasks}/{total_tasks})")
            
            # Tasks by status with columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="Completed", value=completed_tasks)
                
            with col2:
                st.metric(label="In Progress", value=total_tasks - completed_tasks - failed_tasks)
                
            with col3:
                st.metric(label="Failed", value=failed_tasks)
    
    # Add footer with version info
    st.divider()
    st.caption("RoboCo v0.3.0") 