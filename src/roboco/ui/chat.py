"""
Chat functionality for the RoboCo UI.

This module contains the chat view and related functions for the chat interface.
"""

import streamlit as st
from datetime import datetime
import time
from loguru import logger

from roboco.ui.api import (
    send_chat_message, 
    get_project_tasks, 
    get_task_messages, 
    get_task_info
)
from roboco.ui.utils import get_api_url

def chat_view():
    """Render the chat interface."""
    # Only show help content if there are no active projects or conversations
    if not st.session_state.project_id:
        # Show configuration warning when no project exists
        st.warning("""
        For optimal performance, run the server with multiple workers:
        ```bash
        roboco server --workers 4
        ```
        This allows the API to handle chat requests and status updates simultaneously.
        """)
        
        # Add sample message suggestions when no project exists
        st.markdown("**Sample tasks to try:**")
        
        sample_messages = [
            "Create a simple calculator web app with React and CSS Grid layout",
            "Build a modern todo app with Next.js, local storage, and dark mode support",
            "Research the latest advancements in quantum computing and summarize key findings",
            "Create a responsive blog template with HTML, CSS, and a working comment system"
        ]
        
        # Display sample messages in a single column
        for i, message in enumerate(sample_messages):
            if st.button(message, key=f"sample_{i}", type="secondary", use_container_width=True):
                handle_chat_input(message)
    else:
        # Fetch project tasks and their messages
        tasks = []
        task_messages = {}
        all_messages = []
        
        try:
            # Get all tasks for the project
            tasks = get_project_tasks(st.session_state.project_id)
            
            # Get messages for each task
            for task in tasks:
                task_id = task.get("id")
                if task_id:
                    # Get messages for this task
                    messages = get_task_messages(task_id)
                    
                    # Filter and process messages
                    filtered_messages = []
                    for msg in messages:
                        content = msg.get("content", "")
                        role = msg.get("role", "system")
                        
                        # Skip system messages and very short messages
                        if role != "system" and content and len(content.strip()) > 5:
                            # Add agent name if available
                            if role == "assistant" and msg.get("agent_id"):
                                agent_name = msg.get("agent_id")
                                msg["display_content"] = f"**{agent_name}**: {content}"
                            else:
                                msg["display_content"] = content
                                
                            filtered_messages.append(msg)
                    
                    # Sort messages by timestamp
                    filtered_messages.sort(key=lambda x: x.get("timestamp", ""))
                    
                    # Store task messages
                    task_messages[task_id] = filtered_messages
                    
                    # Add to all messages
                    all_messages.extend(filtered_messages)
            
            # Add user messages from session state that might not be in the API yet
            if st.session_state.messages:
                for msg in st.session_state.messages:
                    if msg["role"] == "user":
                        content = msg["content"]
                        if not any(m.get("content") == content and m.get("role") == "user" for m in all_messages):
                            user_msg = {
                                "role": "user",
                                "content": content,
                                "display_content": content,
                                "timestamp": datetime.now().isoformat()
                            }
                            all_messages.append(user_msg)
                            
                            # Add to each task's messages (to the first task if multiple exist)
                            if tasks and tasks[0].get("id") in task_messages:
                                task_messages[tasks[0].get("id")].append(user_msg)
            
            # Sort all messages by timestamp
            all_messages.sort(key=lambda x: x.get("timestamp", ""))
            
        except Exception as e:
            logger.exception(f"Error retrieving task messages: {str(e)}")
    
        # Set better styling for the chat container and messages
        st.markdown("""
        <style>
        .chat-container {
            overflow-y: auto;
            max-height: 70vh;
            padding-right: 10px;
            margin-bottom: 20px;
        }
        .stChatMessage {
            margin-bottom: 10px;
            border-radius: 8px;
        }
        .stChatMessageContent {
            border-radius: 8px;
            overflow-x: auto;
        }
        .main-chat-area {
            display: flex;
            flex-direction: column;
            min-height: 0;
        }
        .messages-container {
            flex-grow: 1;
            overflow-y: auto;
        }
        .chat-input-container {
            margin-top: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create tabs for each task plus a "Main" tab for all messages
        tab_titles = ["🏠 Main Chat"]
        for i, task in enumerate(tasks):
            status = task.get("status", "").upper()
            
            # Add emoji based on status
            if status == "COMPLETED":
                emoji = "✅"
            elif status == "FAILED":
                emoji = "❌"
            else:
                emoji = "○"
                
            # Use simpler numerical labels instead of task titles
            tab_titles.append(f"{emoji} Task {i+1}")
        
        # Create the tabs
        tabs = st.tabs(tab_titles)
        
        # Main Chat Tab - shows all messages in chronological order and chat input
        with tabs[0]:
            st.markdown('<div class="main-chat-area">', unsafe_allow_html=True)
            
            # Messages container
            chat_container = st.container()
            with chat_container:
                st.markdown('<div class="messages-container">', unsafe_allow_html=True)
                
                # If there are no messages but we have a project, show a welcome message
                if not all_messages:
                    with st.chat_message("assistant"):
                        st.markdown("👤 Welcome to your new project! How can I help you today?")
                
                # Display all messages in chronological order
                for message in all_messages:
                    role = message.get("role", "system")
                    with st.chat_message(role):
                        st.markdown(message.get("display_content", message.get("content", "")))
                        
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Chat input only in main chat tab
            st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
            if prompt := st.chat_input("What would you like RoboCo to do?", key="chat_input"):
                handle_chat_input(prompt)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Individual Task Tabs
        for i, task in enumerate(tasks):
            task_id = task.get("id")
            if task_id and task_id in task_messages:
                with tabs[i+1]:  # +1 because the first tab is the Main Chat
                    # Task info header
                    status = task.get("status", "").upper()
                    status_emoji = "✓" if status == "COMPLETED" else "✗" if status == "FAILED" else "○"
                    
                    # Task details
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                        <h4>{status_emoji} {task.get('title', 'Untitled Task')}</h4>
                        <p><strong>Description:</strong> {task.get('description', 'No description')}</p>
                        <p><strong>Status:</strong> {status}</p>
                        <p><strong>Created:</strong> {task.get('created_at', 'Unknown')}</p>
                        <p><strong>Updated:</strong> {task.get('updated_at', 'Unknown')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show error details if task failed
                    if status == "FAILED":
                        error_info = task.get("meta", {}).get("error", "Unknown error")
                        error_details = task.get("meta", {}).get("error_details", "")
                        
                        st.error(f"Task failed: {error_info}")
                        if error_details:
                            with st.expander("Show error details"):
                                st.code(error_details)
                    
                    # Task messages
                    task_chat_container = st.container()
                    with task_chat_container:
                        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                        
                        # Display messages for this task
                        for message in task_messages[task_id]:
                            role = message.get("role", "system")
                            with st.chat_message(role):
                                st.markdown(message.get("display_content", message.get("content", "")))
                                
                        st.markdown('</div>', unsafe_allow_html=True)

def handle_chat_input(prompt: str):
    """Handle a chat input from the user, either from direct input or sample messages.
    
    Args:
        prompt: The chat message content
    """
    # Add user message to temporary chat history for immediate display
    # We'll only add user messages to session_state, as we'll get assistant messages from the API
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Initial message is now more informative
        message_placeholder.markdown("🔎 Analyzing your request...")
        
        try:
            # Start response without waiting for completion - this initiates the task
            response = send_chat_message(prompt)
            
            if response.get("error", False):
                message_placeholder.error(response.get("message", "An error occurred"))
                # Don't add to session_state.messages as we'll get it from the API
            else:
                # Get the task_id if it exists
                task_id = response.get("task_id")
                is_completed = response.get("status") == "completed"
                
                # If task is still running and we have a task ID, poll for updates
                if task_id and not is_completed:
                    # Create a more informative initial message
                    message_placeholder.markdown("⚡ Working on your request... I'll share progress as tasks are processed.")
                    
                    # Poll for updates up to 60 seconds (20 attempts × 3 second intervals)
                    progress_updates = []
                    for i in range(20):
                        # Get latest task messages
                        messages = get_task_messages(task_id)
                        
                        # If we have messages, show them in a chat-like format
                        if messages:
                            # Get all meaningful messages that aren't duplicates
                            new_updates = []
                            for msg in messages:  # Process all messages
                                content = msg.get("content", "")
                                role = msg.get("role", "system")
                                agent = msg.get("agent_id", "")
                                
                                if role != "system" and content and len(content.strip()) > 5:  # Skip empty/very short messages
                                    # Create a unique ID for this message to avoid duplicates
                                    msg_id = f"{agent}:{content[:50]}"
                                    if msg_id not in [item.get('id') for item in progress_updates]:  # Avoid duplicates
                                        agent_prefix = f"**{agent}**: " if agent else ""
                                        new_updates.append({
                                            'id': msg_id,
                                            'text': f"{agent_prefix}{content}",
                                            'timestamp': msg.get('timestamp', datetime.now().isoformat())
                                        })
                            
                            # Add new updates to our tracking list
                            for update in new_updates:
                                progress_updates.append(update)
                            
                            # Sort updates by timestamp for chronological order
                            progress_updates.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                            
                            # Display all updates
                            if progress_updates:
                                # Create a list of formatted messages
                                formatted_updates = []
                                for idx, update in enumerate(progress_updates):
                                    # Use different styling for different messages
                                    if idx == 0:  # Latest message
                                        formatted_updates.append(f"### {update['text']}")
                                    else:
                                        formatted_updates.append(f"{update['text']}")
                                
                                # Join all updates and display them
                                update_text = "\n\n---\n\n".join(formatted_updates)
                                message_placeholder.markdown(update_text)
                        
                        # Check if task is complete or failed
                        task_status = get_task_info(task_id)
                        if task_status:
                            status = task_status.get("status", "").upper()
                            if status == "COMPLETED":
                                break
                            elif status == "FAILED":
                                # Extract error details from the task
                                error_info = task_status.get("meta", {}).get("error", "Unknown error")
                                error_traceback = task_status.get("meta", {}).get("error_details", "")
                                
                                # Update the UI with error information
                                error_message = f"✗ **Task failed**: {error_info}"
                                if error_traceback:
                                    error_message += f"\n\n<details><summary>Show error details</summary>\n\n```\n{error_traceback}\n```\n</details>"
                                
                                message_placeholder.error(error_message)
                                break
                        
                        # Wait before polling again
                        time.sleep(3)
                
                # Show the final response message if available
                final_message = response.get("message", "")
                if final_message:
                    message_placeholder.markdown(final_message)
                
                # Update execution log and tasks
                from roboco.ui.status import update_execution_log
                update_execution_log()
        except Exception as e:
            logger.exception(f"Error in chat view: {str(e)}")
            message_placeholder.error(f"Error: {str(e)}")
    
    # Force a rerun to update the UI immediately
    st.rerun() 