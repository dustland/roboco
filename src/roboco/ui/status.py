"""
Execution status tracking for the RoboCo UI.

This module contains functions for tracking task execution status and updating the UI.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from roboco.ui.api import get_project_info, get_project_tasks, stop_execution

def update_execution_log() -> None:
    """Update the execution log based on project status."""
    if not st.session_state.project_id:
        return
    
    try:
        # Get project info
        project = get_project_info(st.session_state.project_id)
        if not project:
            logger.warning(f"Project not found: {st.session_state.project_id}")
            return
            
        # Get tasks
        tasks = get_project_tasks(st.session_state.project_id)
        st.session_state.tasks = tasks
        
        # Add project creation to log if it's not there
        if not st.session_state.execution_log:
            st.session_state.execution_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "project_created",
                "message": f"Project '{project.get('name', 'Unnamed')}' created"
            })
            
        # Check for task status changes and add to log
        for task in tasks:
            task_log_entry = {
                "time": task.get("updated_at", datetime.now().strftime("%H:%M:%S")),
                "type": "task_status",
                "task_id": task.get("id"),
                "status": task.get("status"),
                "title": task.get("title"),
                "message": f"Task '{task.get('title')}' is {task.get('status')}"
            }
            
            # Check if this task status is already in the log
            exists = False
            for log in st.session_state.execution_log:
                if (log.get("type") == "task_status" and 
                    log.get("task_id") == task.get("id") and 
                    log.get("status") == task.get("status")):
                    exists = True
                    break
                    
            if not exists:
                st.session_state.execution_log.append(task_log_entry)
                
        # Update last update time
        st.session_state.last_update = datetime.now()
    except Exception as e:
        logger.exception(f"Error updating execution log: {str(e)}")
        
def display_execution_status() -> None:
    """Render the execution status interface."""
    # Display active project
    if st.session_state.project_id:
        try:
            project = get_project_info(st.session_state.project_id)
            if project:
                # More modern project info display
                st.container().markdown(f"""
                <div style="padding: 10px; border-radius: 5px; background-color: #f0f2f6; margin-bottom: 20px;">
                    <h4 style="margin-top: 0;">Active Project</h4>
                    <p><strong>Name:</strong> {project.get('name', 'Unnamed')}</p>
                    <p><strong>ID:</strong> {st.session_state.project_id}</p>
                    <p><strong>Created:</strong> {project.get('created_at', 'Unknown')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Add stop button
                if st.button("⚠️ Stop Execution", key="stop_execution"):
                    if stop_execution(st.session_state.project_id):
                        st.success("Execution stopped successfully")
                    else:
                        st.error("Failed to stop execution")
            else:
                st.warning(f"Project not found: {st.session_state.project_id}")
        except Exception as e:
            st.error(f"Error loading project: {str(e)}")
    else:
        st.info("No active project. Start a conversation to create one.")
    
    # Display tasks status
    if st.session_state.tasks:
        # Create a progress bar for task completion
        completed_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "COMPLETED")
        total_tasks = len(st.session_state.tasks)
        failed_tasks = sum(1 for task in st.session_state.tasks if task.get("status", "").upper() == "FAILED")
        
        if total_tasks > 0:
            completion_percentage = int(completed_tasks / total_tasks * 100)
            
            # Display statistics in a cleaner format
            cols = st.columns(4)
            cols[0].metric("Total Tasks", f"{total_tasks}")
            cols[1].metric("Completed", f"{completed_tasks}", f"{completion_percentage}%")
            cols[2].metric("In Progress", f"{total_tasks - completed_tasks - failed_tasks}")
            cols[3].metric("Failed", f"{failed_tasks}", delta=None, delta_color="inverse")
            
            # Progress bar
            st.progress(completion_percentage / 100, text=f"Completed: {completed_tasks}/{total_tasks}")
        
        # Create tabs for different views of the tasks
        task_tab1, task_tab2 = st.tabs(["📋 Task List", "📝 Task Details"])
        
        with task_tab1:
            # Display tasks in a table
            task_data = []
            for task in st.session_state.tasks:
                status = task.get("status", "").upper()
                status_emoji = "✅" if status == "COMPLETED" else "❌" if status == "FAILED" else "⏳"
                
                task_data.append({
                    "Title": task.get("title", ""),
                    "Status": f"{status_emoji} {status}",
                    "Created": task.get("created_at", ""),
                    "Updated": task.get("updated_at", "")
                })
            
            st.dataframe(task_data, use_container_width=True)
        
        with task_tab2:
            # Detailed task view with errors
            for task in st.session_state.tasks:
                status = task.get("status", "").upper()
                status_emoji = "✅" if status == "COMPLETED" else "❌" if status == "FAILED" else "⏳"
                
                with st.expander(f"{status_emoji} {task.get('title', 'Untitled Task')} - {status}"):
                    st.markdown(f"**Description:** {task.get('description', 'No description provided')}")
                    st.markdown(f"**Created:** {task.get('created_at', 'Unknown')}")
                    st.markdown(f"**Last Updated:** {task.get('updated_at', 'Unknown')}")
                    
                    # Add error information for failed tasks
                    if status == "FAILED":
                        error_info = task.get("meta", {}).get("error", "Unknown error")
                        error_details = task.get("meta", {}).get("error_details", "")
                        st.error(f"Task failed: {error_info}")
                        if error_details:
                            with st.expander("Show error details"):
                                st.code(error_details)
    
        # Display execution log in a more modern format
        if st.session_state.execution_log:
            st.markdown("### 📜 Execution Log")
            
            # Create an expandable log
            with st.expander("View Log", expanded=False):
                # Create a clean table for the log
                for log in st.session_state.execution_log:
                    icon = "⏳"  # Default icon
                    if log.get("type") == "task_status":
                        status = log.get("status")
                        if status == "COMPLETED":
                            icon = "✅"
                        elif status == "FAILED":
                            icon = "❌"
                    elif log.get("type") == "project_created":
                        icon = "🆕"
                    
                    st.text(f"{log['time']} {icon} {log['message']}")
    
    # Add a refresh button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Refresh", key="refresh_status"):
            update_execution_log()
    with col2:
        st.text(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}") 