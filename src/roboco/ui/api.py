"""
API client functions for the RoboCo UI.

This module contains functions for communicating with the RoboCo API.
"""

import requests
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from roboco.ui.utils import get_api_url
import streamlit as st

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

def get_directory_contents(project_id: str, path: str) -> List[Dict[str, Any]]:
    """Get contents of a directory in a project.
    
    Args:
        project_id: The project ID
        path: Directory path relative to project root
        
    Returns:
        List of file/directory information
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Getting directory contents for project_id={project_id}, path={path}")
        response = requests.get(
            f"{api_url}/projects/{project_id}/files",
            params={"path": path},
            timeout=5
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return []
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting directory contents: {str(e)}")
        return []

def get_file_content(project_id: str, path: str) -> Optional[Dict[str, Any]]:
    """Get content of a file in a project.
    
    Args:
        project_id: The project ID
        path: File path relative to project root
        
    Returns:
        File content information or None if not found
    """
    api_url = get_api_url()
    
    try:
        logger.info(f"Getting file content for project_id={project_id}, path={path}")
        response = requests.get(
            f"{api_url}/projects/{project_id}/files/content",
            params={"path": path},
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code}, {response.text}")
            return None
            
        return response.json()
    except Exception as e:
        logger.exception(f"Error getting file content: {str(e)}")
        return None 