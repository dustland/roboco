"""
File browser functionality for the RoboCo UI.

This module contains functions for browsing project files and displaying file content.
"""

import streamlit as st
import os
from typing import Dict, Any, List, Optional
from loguru import logger
import requests

from roboco.ui.api import get_directory_contents, get_file_content
from roboco.ui.utils import get_api_url

def explore_project_files() -> None:
    """Display project files and their content."""
    if not st.session_state.project_id:
        st.info("No active project. Start a conversation to create one.")
        return
    
    # Initialize session state variables
    if "current_path" not in st.session_state:
        st.session_state.current_path = ""
    if "create_new_file" not in st.session_state:
        st.session_state.create_new_file = False
    if "create_new_folder" not in st.session_state:
        st.session_state.create_new_folder = False
    if "selected_file" not in st.session_state:
        st.session_state.selected_file = None
    if "root_ensured" not in st.session_state:
        st.session_state.root_ensured = False
        
    # Ensure project root directory exists (only once per session)
    if not st.session_state.root_ensured:
        try:
            api_url = get_api_url()
            response = requests.post(
                f"{api_url}/projects/{st.session_state.project_id}/ensure_root",
                timeout=5
            )
            st.session_state.root_ensured = True
        except Exception as e:
            logger.warning(f"Could not ensure project root: {str(e)}")
            # Continue anyway, as the API will create directories as needed
        
    # Handle navigation buttons and path input
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("Back", disabled=st.session_state.current_path == "", help="Go back to parent directory", use_container_width=True):
            # Go up one directory level
            parent_path = os.path.dirname(st.session_state.current_path)
            if parent_path == "":  # Root
                parent_path = ""
            st.session_state.current_path = parent_path
            st.rerun()
            
    with col2:
        new_path = st.text_input(
            label="Path",  # Label needed but will be hidden
            value=st.session_state.current_path,
            label_visibility="collapsed",  # Hide the label completely
            placeholder="Enter path..."
        )
        if new_path != st.session_state.current_path:
            st.session_state.current_path = new_path
            st.rerun()
    
    with col3:
        if st.button("Refresh", help="Refresh directory listing", use_container_width=True):
            st.rerun()
            
    try:
        # Get files and directories
        files = get_directory_contents(
            st.session_state.project_id, 
            st.session_state.current_path
        )
        
        if not files:
            # Could be an empty directory or an error
            # Add a more informative message
            st.info(f"Directory '{st.session_state.current_path or '/'}' appears to be empty. If this is unexpected, check if the project has any files or try a different path.")
            
            # Add a create file button for this directory
            if st.button("➕ Create a New File", key="create_new_file"):
                st.session_state.create_new_file = True
                st.rerun()
            
            # If we're in file creation mode, show a file name input
            if st.session_state.get("create_new_file", False):
                with st.form("new_file_form"):
                    file_name = st.text_input("File Name")
                    file_content = st.text_area("File Content", height=200)
                    submit = st.form_submit_button("Create File")
                    
                    if submit and file_name:
                        # Determine the full path
                        file_path = os.path.join(st.session_state.current_path, file_name)
                        
                        # Call API to create the file
                        try:
                            response = requests.post(
                                f"{get_api_url()}/projects/{st.session_state.project_id}/files",
                                json={"path": file_path, "content": file_content},
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                st.success(f"File '{file_name}' created successfully!")
                                st.session_state.create_new_file = False
                                st.rerun()
                            else:
                                st.error(f"Error creating file: {response.text}")
                        except Exception as e:
                            st.error(f"Error creating file: {str(e)}")
            
            return
            
        # Group by type (directories first, then files)
        directories = sorted([f for f in files if f["type"] == "directory"], key=lambda x: x["name"])
        regular_files = sorted([f for f in files if f["type"] == "file"], key=lambda x: x["name"])
        
        # Display directories first with folder icons
        if directories:
            st.markdown("##### 📁 Directories")
            
            # Create columns for grid layout
            cols = st.columns(3)
            
            for i, directory in enumerate(directories):
                col_idx = i % 3
                with cols[col_idx]:
                    dir_name = directory["name"]
                    modified = directory.get("modified", "")
                    
                    # Display directory as a button
                    if st.button(f"📁 {dir_name}", key=f"dir_{i}", use_container_width=True):
                        # Navigate to this directory
                        st.session_state.current_path = directory["path"]
                        st.rerun()
                    
                    # Show modified date if available
                    if modified:
                        st.caption(f"Modified: {modified}")
        
        # Display files with appropriate icons based on extension
        if regular_files:
            st.markdown("##### 📄 Files")
            
            # Define file type icons
            file_icons = {
                "py": "🐍",
                "js": "📜",
                "html": "🌐",
                "css": "🎨",
                "md": "📝",
                "json": "📄",
                "txt": "📄",
                "png": "🖼️",
                "jpg": "🖼️",
                "jpeg": "🖼️",
                "gif": "🖼️"
            }
            
            # Create columns for grid layout
            cols = st.columns(3)
            
            for i, file in enumerate(regular_files):
                col_idx = i % 3
                with cols[col_idx]:
                    file_name = file["name"]
                    
                    # Get file extension for icon
                    _, ext = os.path.splitext(file_name)
                    ext = ext[1:] if ext else ""  # Remove the dot
                    icon = file_icons.get(ext.lower(), "📄")  # Default to generic file icon
                    
                    # Format file size
                    size = file.get("size", 0)
                    if size is not None:
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.1f} KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f} MB"
                    else:
                        size_str = ""
                        
                    modified = file.get("modified", "")
                    
                    # Display file as a button
                    if st.button(f"{icon} {file_name}", key=f"file_{i}", use_container_width=True):
                        # Set this file as selected
                        st.session_state.selected_file = file["path"]
                        st.rerun()
                    
                    # Show file size and modified date if available
                    if size_str:
                        st.caption(f"{size_str} • {modified if modified else ''}")
        
        # If no files or directories
        if not directories and not regular_files:
            st.info("Directory is empty.")
        
        # Display selected file content if any
        if "selected_file" in st.session_state and st.session_state.selected_file:
            display_file_content(st.session_state.project_id, st.session_state.selected_file)
                
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error accessing project files: {error_msg}")
        
        # Display a user-friendly error message
        if "404" in error_msg:
            st.error(f"Directory not found: {st.session_state.current_path}")
            st.info("The project directory may not exist yet. Try creating files or directories first.")
        elif "403" in error_msg:
            st.error(f"Permission denied accessing directory: {st.session_state.current_path}")
        else:
            st.error(f"Error accessing project files: {error_msg}")
            
        # Reset path to root if there's a navigation error
        if "current_path" in st.session_state and st.session_state.current_path:
            if st.button("Return to Root Directory"):
                st.session_state.current_path = ""
                st.rerun()
                
        # Optional: Add ability to report the error
        with st.expander("Error Details"):
            st.code(error_msg)
            
        st.info("Check if the API is running and the project exists.")
        
    # Add instructions for accessing files via command line as a fallback
    with st.expander("Access via Command Line"):
        st.code(f"cd ~/roboco_workspace/{st.session_state.project_id}\nls -la", language="bash")

def display_file_content(project_id: str, file_path: str) -> None:
    """Display file content with syntax highlighting.
    
    Args:
        project_id: The project ID
        file_path: The file path relative to project root
    """
    try:
        file_data = get_file_content(project_id, file_path)
        if not file_data:
            st.error(f"Error reading file: {file_path}")
            return
        
        # Get file information
        file_name = os.path.basename(file_path)
        file_size = file_data.get("size", 0)
        content = file_data.get("content", "")
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"
        
        # File metadata
        st.caption(f"Size: {size_str}")
        
        # Determine language for syntax highlighting
        _, ext = os.path.splitext(file_name)
        ext = ext[1:] if ext else ""  # Remove the dot
        
        language_map = {
            "py": "python",
            "js": "javascript",
            "jsx": "jsx",
            "ts": "typescript",
            "tsx": "tsx",
            "html": "html",
            "css": "css",
            "scss": "scss",
            "json": "json",
            "md": "markdown",
            "txt": None,
            "csv": None,
            "yml": "yaml",
            "yaml": "yaml",
            "sh": "bash",
            "bash": "bash",
            "sql": "sql"
        }
        
        language = language_map.get(ext.lower(), None)
        
        # For markdown files, add a toggle between raw and rendered view
        if ext.lower() == "md":
            if "markdown_view_mode" not in st.session_state:
                st.session_state.markdown_view_mode = "rendered"  # Default to rendered view
                
            # Remove the toggle controls from here
                
            # Display according to selected mode
            if st.session_state.markdown_view_mode == "rendered":
                st.markdown(content)
            else:
                st.code(content, language="markdown")
        else:
            # Display file content with syntax highlighting for non-markdown files
            st.code(content, language=language)
        
        # File actions - now with toggle for markdown at the bottom
        col1, col2 = st.columns(2)
        
        with col1:
            # For markdown files, show the toggle button
            if st.button("Toggle Markdown", disabled=(ext.lower() != "md"), use_container_width=True):
                # Switch between rendered and raw mode
                st.session_state.markdown_view_mode = "raw" if st.session_state.markdown_view_mode == "rendered" else "rendered"
                st.rerun()
            st.caption(f"Currently in {'rendered' if st.session_state.markdown_view_mode == 'rendered' else 'raw code'} mode")
            
        with col2:
            if st.button("Download", use_container_width=True):
                # Create a download button
                st.download_button(
                    label="Click to Download",
                    data=content,
                    file_name=file_name,
                    mime="text/plain",
                    key="download_file"
                )
                
    except Exception as e:
        error_msg = str(e)
        st.error(f"Error displaying file: {error_msg}")
        with st.expander("Error Details"):
            st.code(error_msg) 