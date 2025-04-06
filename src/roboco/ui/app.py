"""
RoboCo web interface for chat and project management.

This provides a web interface for:
1. Chatting with RoboCo agents
2. Viewing execution status and progress
3. Exploring project files and tasks
4. Controlling the execution of tasks
"""

import streamlit as st
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
from pathlib import Path
import requests
import logging
import time
import warnings
import re

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

# Initialize session state variables if they don't exist
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

def send_chat_message(content: str) -> Dict[str, Any]:
    """Send a chat message to the API.
    
    Args:
        content: The message content
        
    Returns:
        The API response
    """
    api_url = get_api_url()
    
    try:
        payload = {"query": content}
        
        # Determine which endpoint to use
        if st.session_state.project_id:
            # Continue existing chat with a project
            endpoint = f"{api_url}/chat/project/{st.session_state.project_id}"
        else:
            # Start new chat
            endpoint = f"{api_url}/chat"
            
        # Log the API request for debugging
        logger.info(f"Sending request to {endpoint}")
        logger.info(f"Request payload: {payload}")
            
        # Make the API request
        response = requests.post(
            endpoint,
            json=payload,
            timeout=60  # Longer timeout for potentially complex tasks
        )
        
        # Handle non-200 responses
        if response.status_code != 200:
            error_msg = f"API error: {response.status_code}"
            try:
                error_detail = response.json().get("detail", "Unknown error")
                error_msg = f"{error_msg}, {error_detail}"
            except:
                error_msg = f"{error_msg}, {response.text}"
                
            logger.error(error_msg)
            return {"message": error_msg, "error": True}
            
        # Parse the JSON response
        data = response.json()
        logger.info(f"API response: {data}")
        
        # Update project ID if available
        if "project_id" in data:
            st.session_state.project_id = data["project_id"]
            
        return data
    except Exception as e:
        logger.exception(f"Error sending chat message: {str(e)}")
        return {"message": f"Error: {str(e)}", "error": True}

def get_project_info(project_id: str) -> Optional[Dict[str, Any]]:
    """Get information about a project.
    
    Args:
        project_id: The project ID
        
    Returns:
        Project information or None if not found
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Getting project info for project_id={project_id}")
        response = requests.get(
            f"{api_url}/projects/{project_id}",
            timeout=5
        )
        
        if response.status_code == 404:
            logger.warning(f"Project not found: {project_id}")
            return None
            
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return None
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting project info: {str(e)}")
        return None

def get_project_tasks(project_id: str) -> List[Dict[str, Any]]:
    """Get tasks for a project.
    
    Args:
        project_id: The project ID
        
    Returns:
        List of tasks
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Getting tasks for project_id={project_id}")
        response = requests.get(
            f"{api_url}/projects/{project_id}/tasks",
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return []
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting project tasks: {str(e)}")
        return []

def get_all_projects() -> List[Dict[str, Any]]:
    """Get all projects.
    
    Returns:
        List of projects
    """
    api_url = get_api_url()
    
    try:
        logger.info("Getting all projects")
        response = requests.get(
            f"{api_url}/projects",
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return []
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting projects: {str(e)}")
        return []

def stop_execution(project_id: str) -> bool:
    """Stop the execution of the current project.
    
    Args:
        project_id: The project ID
        
    Returns:
        True if successful, False otherwise
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Stopping execution for project_id={project_id}")
        response = requests.post(
            f"{api_url}/projects/{project_id}/stop",
            timeout=5
        )
        return response.status_code == 200
    except Exception as e:
        logger.exception(f"Error stopping execution: {str(e)}")
        return False

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

def explore_project_files() -> None:
    """Display project files and their content."""
    if not st.session_state.project_id:
        st.info("No active project. Start a conversation to create one.")
        return
    
    # Instead of using an API endpoint, inform the user that file access is not available through the API
    st.info("File access is not available through the UI at this time. Please use the command line to explore files.")
    
    # Provide instructions for accessing files via command line
    st.code(f"cd workspace/{st.session_state.project_id}\nls -la", language="bash")

def chat_view():
    """Render the chat interface."""
    # Display warning about server configuration
    if len(st.session_state.messages) == 0:
        st.warning("""
        ⚠️ **FastAPI Server Configuration** 
        
        If the API becomes unresponsive during chat operations, it's likely running with only one worker.
        
        Run the server with multiple workers to handle concurrent requests:
        ```
        roboco server --workers 4
        ```
        
        This allows the API to handle both the chat request and other operations (like status updates) simultaneously.
        """)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Add sample message suggestions
    if not st.session_state.messages or len(st.session_state.messages) <= 4:
        st.write("Sample message suggestions:")
        sample_messages = [
            "Create a simple calculator web app with React and CSS Grid layout",
            "Build a modern todo app with Vue.js, local storage, and dark mode support",
            "Research the latest advancements in quantum computing and summarize key findings",
            "Create a responsive blog template with HTML, CSS, and a working comment system"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(sample_messages[0], key="sample_1"):
                handle_chat_input(sample_messages[0])
            if st.button(sample_messages[2], key="sample_3"):
                handle_chat_input(sample_messages[2])
        
        with col2:
            if st.button(sample_messages[1], key="sample_2"):
                handle_chat_input(sample_messages[1])
            if st.button(sample_messages[3], key="sample_4"):
                handle_chat_input(sample_messages[3])
    
    # Chat input
    if prompt := st.chat_input("What would you like RoboCo to do?"):
        handle_chat_input(prompt)

def get_task_messages(task_id: str) -> List[Dict[str, Any]]:
    """Get messages for a specific task.
    
    Args:
        task_id: The task ID
        
    Returns:
        List of task messages
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Getting messages for task_id={task_id}")
        response = requests.get(
            f"{api_url}/tasks/{task_id}/messages",
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return []
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting task messages: {str(e)}")
        return []

def handle_chat_input(prompt: str):
    """Handle a chat input from the user, either from direct input or sample messages.
    
    Args:
        prompt: The chat message content
    """
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Initial "Thinking..." message
        message_placeholder.markdown("Thinking...")
        
        try:
            # Start response without waiting for completion - this initiates the task
            response = send_chat_message(prompt)
            
            if response.get("error", False):
                message_placeholder.error(response.get("message", "An error occurred"))
                st.session_state.messages.append({"role": "assistant", "content": response.get("message", "")})
            else:
                # Get the task_id if it exists
                task_id = response.get("task_id")
                is_completed = response.get("status") == "completed"
                
                # If task is still running and we have a task ID, poll for updates
                if task_id and not is_completed:
                    message_placeholder.markdown("Processing your request... I'll update you with progress.")
                    
                    # Poll for updates up to 60 seconds (20 attempts × 3 second intervals)
                    for i in range(20):
                        # Show that we're still working
                        dots = "." * ((i % 3) + 1)
                        status_placeholder.markdown(f"Working{dots} (Polling for updates)")
                        
                        # Get latest task messages
                        messages = get_task_messages(task_id)
                        
                        # If we have messages, show the most recent one
                        if messages:
                            latest_content = []
                            for msg in messages[-min(3, len(messages)):]:  # Show up to last 3 messages
                                content = msg.get("content", "")
                                role = msg.get("role", "system")
                                if role != "system" and content:  # Skip empty or system messages
                                    latest_content.append(f"- {content}")
                            
                            if latest_content:
                                update_text = "**Current progress:**\n\n" + "\n\n".join(latest_content)
                                message_placeholder.markdown(update_text)
                        
                        # Check if task is complete
                        task_status = get_task_info(task_id)
                        if task_status and task_status.get("status") == "COMPLETED":
                            break
                            
                        # Wait before polling again
                        time.sleep(3)
                
                # Show the final response
                message_placeholder.markdown(response.get("message", "No response"))
                status_placeholder.empty()  # Remove the status indicator
                
                # Add the final message to chat history
                st.session_state.messages.append({"role": "assistant", "content": response.get("message", "")})
                
                # Update execution log
                update_execution_log()
        except Exception as e:
            logger.exception(f"Error in chat view: {str(e)}")
            message_placeholder.error(f"Error: {str(e)}")
    
    # Force a rerun to update the UI immediately
    st.rerun()

def get_task_info(task_id: str) -> Optional[Dict[str, Any]]:
    """Get information about a task.
    
    Args:
        task_id: The task ID
        
    Returns:
        Task information or None if not found
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Getting task info for task_id={task_id}")
        response = requests.get(
            f"{api_url}/tasks/{task_id}",
            timeout=5
        )
        
        if response.status_code == 404:
            logger.warning(f"Task not found: {task_id}")
            return None
            
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return None
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting task info: {str(e)}")
        return None

def execution_status_view():
    """Render the execution status interface."""
    st.subheader("Execution Status")
    
    # Display active project
    if st.session_state.project_id:
        try:
            project = get_project_info(st.session_state.project_id)
            if project:
                st.success(f"Active project: {project.get('name', 'Unnamed')} (ID: {st.session_state.project_id})")
                
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
        st.write("Tasks:")
        
        # Create a progress bar for task completion
        completed_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "COMPLETED")
        total_tasks = len(st.session_state.tasks)
        if total_tasks > 0:
            completion_percentage = int(completed_tasks / total_tasks * 100)
            st.progress(completion_percentage / 100, text=f"Completed: {completed_tasks}/{total_tasks} ({completion_percentage}%)")
        
        # Display tasks in a table
        task_data = []
        for task in st.session_state.tasks:
            task_data.append({
                "Title": task.get("title", ""),
                "Status": task.get("status", ""),
                "Created": task.get("created_at", ""),
                "Updated": task.get("updated_at", "")
            })
            
        st.dataframe(task_data, use_container_width=True)
    
    # Display execution log
    if st.session_state.execution_log:
        st.write("Execution Log:")
        for log in st.session_state.execution_log:
            icon = "🟢" if log.get("type") == "task_status" and log.get("status") == "COMPLETED" else "⏳"
            if log.get("type") == "project_created":
                icon = "🆕"
            st.text(f"{log['time']} {icon} {log['message']}")
    
    # Add a refresh button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Refresh", key="refresh_status"):
            update_execution_log()
    with col2:
        st.text(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

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

def sidebar_content():
    """Render the sidebar content."""
    st.title("About RoboCo")
    st.markdown("""
    RoboCo is a powerful platform that combines Domain-Driven Design with 
    Multi-Agent Systems to create intelligent, collaborative AI teams.
    """)
    
    st.subheader("Active Session")
    if st.session_state.project_id:
        st.info(f"Project ID: {st.session_state.project_id}")
    
    if st.button("Start New Chat", key="new_chat"):
        st.session_state.messages = []
        st.session_state.project_id = None
        st.session_state.execution_log = []
        st.session_state.tasks = []
        st.success("New chat started!")
        st.rerun()
    
    # Status indicators
    st.subheader("System Status")
    if st.session_state.api_connected:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Disconnected")
        if st.button("Retry Connection"):
            st.session_state.api_connected = check_api_connection()
            st.rerun()
    
    if st.session_state.project_id and st.session_state.tasks:
        completed_tasks = sum(1 for task in st.session_state.tasks if task.get("status") == "COMPLETED")
        total_tasks = len(st.session_state.tasks)
        if total_tasks > 0:
            completion_percentage = int(completed_tasks / total_tasks * 100)
            st.metric("Task Completion", f"{completion_percentage}%", f"{completed_tasks}/{total_tasks}")

def main():
    """Main Streamlit application."""
    # Initialize session state
    init_session_state()
    
    # Check API connection
    api_connected = check_api_connection()
    
    # Set page config
    st.set_page_config(
        page_title="RoboCo Chat",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Streamlit UI layout
    st.title("RoboCo Chat Interface")
    
    if not api_connected:
        st.error("❌ Cannot connect to RoboCo API. Make sure to start the API server with `roboco server`")
        st.info("Run: `roboco server` in a separate terminal and refresh this page")
        return
    
    st.success("✅ Connected to RoboCo API")
    st.markdown("Chat with RoboCo agents and monitor project execution")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Execution Status", "Project Files", "Settings"])
    
    with tab1:
        chat_view()
    
    with tab2:
        execution_status_view()
    
    with tab3:
        st.subheader("Project Files")
        explore_project_files()
    
    with tab4:
        settings_view()
    
    # Add a sidebar with information
    with st.sidebar:
        sidebar_content()
    
    # Auto-update status every few seconds if project is active
    if st.session_state.project_id:
        update_execution_log()

if __name__ == "__main__":
    main() 