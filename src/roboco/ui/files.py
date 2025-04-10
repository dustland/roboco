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

def handle_file_browser_events():
    """Custom component to handle file browser events from JavaScript."""
    # Get query parameters
    query_params = st.query_params
    
    # Handle path navigation from query parameter
    if "path" in query_params:
        path = query_params["path"]
        if path != st.session_state.current_path:
            st.session_state.current_path = path
            # Remove the query parameter to avoid navigation loop
            st.query_params.clear()
            st.rerun()
    
    # Add JavaScript to handle postMessage events
    js_code = """
    <script>
    // Create a function to handle messages from iframes/components
    window.addEventListener('message', function(event) {
        // Check if it's a navigation event
        if (event.data.type === 'navigate') {
            const path = event.data.path;
            // Update the URL with the new path
            window.location.href = '?path=' + encodeURIComponent(path);
        }
        
        // Check if it's a file selection event
        if (event.data.type === 'select_file') {
            const path = event.data.path;
            // Store the selected file path in sessionStorage
            sessionStorage.setItem('selectedFile', path);
            // Reload the page to trigger file selection
            window.location.reload();
        }
    });
    
    // Check if we have a file to select from sessionStorage
    document.addEventListener('DOMContentLoaded', function() {
        const selectedFile = sessionStorage.getItem('selectedFile');
        if (selectedFile) {
            // Clear the storage to avoid selection loop
            sessionStorage.removeItem('selectedFile');
            // Send a custom event to Streamlit
            const event = new CustomEvent('streamlit:file-selected', { detail: selectedFile });
            window.dispatchEvent(event);
        }
    });
    </script>
    """
    st.markdown(js_code, unsafe_allow_html=True)
    
    # Use session state to check if we need to select a file
    # This is a workaround since we can't directly catch the custom event
    if "file_selection_event" in st.session_state:
        file_path = st.session_state.file_selection_event
        st.session_state.selected_file = file_path
        del st.session_state.file_selection_event
        st.rerun()

def explore_project_files() -> None:
    """Display project files and their content."""
    if not st.session_state.project_id:
        st.info("No active project. Start a conversation to create one.")
        return
    
    # Handle file browser events
    handle_file_browser_events()
    
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
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col1:
        if st.button("↩ Back", disabled=st.session_state.current_path == ""):
            # Go up one directory level
            parent_path = os.path.dirname(st.session_state.current_path)
            if parent_path == "":  # Root
                parent_path = ""
            st.session_state.current_path = parent_path
            st.rerun()
            
    with col2:
        new_path = st.text_input("Directory Path", value=st.session_state.current_path)
        if new_path != st.session_state.current_path:
            st.session_state.current_path = new_path
            st.rerun()
            
    with col3:
        if st.button("⟳ Refresh"):
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
        
        # Display directory contents in a clean table format
        display_path = st.session_state.current_path if st.session_state.current_path else "/"
        
        # Format the path with dividers for better navigation
        path_parts = display_path.split('/')
        path_html = '<div class="path-breadcrumb">'
        cumulative_path = ""
        
        # Add root
        path_html += f'<span><a href="#" onclick="return false;" data-path="">🏠 root</a></span>'
        
        # Add each path part with separator
        for i, part in enumerate(path_parts):
            if part:  # Skip empty parts
                if i > 0 or cumulative_path:
                    path_html += ' <span style="color: #94a3b8; margin: 0 5px;">/</span> '
                
                cumulative_path += f"/{part}" if cumulative_path else part
                path_html += f'<span><a href="#" onclick="return false;" data-path="{cumulative_path}">{part}</a></span>'
        
        path_html += '</div>'
        
        # Add script to handle path navigation clicks
        path_html += """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.path-breadcrumb a').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const path = this.getAttribute('data-path');
                    window.parent.postMessage({type: 'navigate', path: path}, '*');
                });
            });
        });
        </script>
        """
        
        st.markdown(path_html, unsafe_allow_html=True)
        
        # Use a cleaner header style
        st.markdown(f'''
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0; flex-grow: 1;">Files & Directories</h3>
            <span style="color: #64748b; font-size: 14px; font-weight: 500;">{display_path}</span>
        </div>
        ''', unsafe_allow_html=True)
        
        # Add a file/dir actions row with wrapper for horizontal scrolling and better styling
        st.markdown('<div style="display: flex; gap: 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("➕ New File", use_container_width=True, type="primary"):
                st.session_state.create_new_file = True
                st.rerun()
                
        with col2:
            if st.button("📁 New Folder", use_container_width=True):
                st.session_state.create_new_folder = True
                st.rerun()
        
        with col3:
            if st.button("⟳ Refresh", use_container_width=True):
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle new folder creation
        if st.session_state.get("create_new_folder", False):
            with st.form("new_folder_form"):
                folder_name = st.text_input("Folder Name")
                submit = st.form_submit_button("Create Folder")
                
                if submit and folder_name:
                    # Determine the full path
                    folder_path = os.path.join(st.session_state.current_path, folder_name)
                    
                    # Call API to create the folder
                    try:
                        response = requests.post(
                            f"{get_api_url()}/projects/{st.session_state.project_id}/directories",
                            json={"path": folder_path},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            st.success(f"Folder '{folder_name}' created successfully!")
                            st.session_state.create_new_folder = False
                            st.rerun()
                        else:
                            st.error(f"Error creating folder: {response.text}")
                    except Exception as e:
                        st.error(f"Error creating folder: {str(e)}")
        
        # Handle new file creation
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
        
        # Display directories first with folder icons
        if directories:
            st.markdown('<h4 style="margin-top: 1.5rem; font-size: 1.1rem; color: #4b5563; font-weight: 500;">📁 Directories</h4>', unsafe_allow_html=True)
            
            # Use a grid layout for directories
            grid_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px;">'
            
            for d in directories:
                modified_date = d.get("modified", "")
                # Create a card-like element for each directory
                grid_html += f'''
                <div class="dir-item" onclick="window.location.href='?path={d["path"]}'" 
                     style="display: flex; flex-direction: column; cursor: pointer; padding: 15px; border-radius: 8px; 
                     border: 1px solid #e2e8f0; background-color: #f8fafc; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 20px; margin-right: 8px;">📁</span>
                        <span style="font-weight: 500; flex-grow: 1; overflow: hidden; text-overflow: ellipsis;">{d["name"]}</span>
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-top: auto;">
                        {modified_date}
                    </div>
                </div>
                '''
            
            grid_html += '</div>'
            st.markdown(grid_html, unsafe_allow_html=True)
        
        # Display files with appropriate icons based on extension
        if regular_files:
            st.markdown('<h4 style="margin-top: 1.5rem; font-size: 1.1rem; color: #4b5563; font-weight: 500;">📄 Files</h4>', unsafe_allow_html=True)
            
            # Define file type icons
            file_icons = {
                "py": "🐍",
                "js": "📜",
                "html": "🌐",
                "css": "🎨",
                "md": "📝",
                "json": "📊",
                "txt": "📄",
                "png": "🖼️",
                "jpg": "🖼️",
                "jpeg": "🖼️",
                "gif": "🖼️"
            }
            
            # Use a grid layout for files
            grid_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; margin-bottom: 20px;">'
            
            for f in regular_files:
                # Get file extension for icon
                _, ext = os.path.splitext(f["name"])
                ext = ext[1:] if ext else ""  # Remove the dot
                icon = file_icons.get(ext, "📄")  # Default to generic file icon
                
                # Format file size
                size = f.get("size", 0)
                if size is not None:
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                else:
                    size_str = ""
                    
                modified_date = f.get("modified", "")
                
                # Create a card-like element for each file
                grid_html += f'''
                <div class="file-item" data-path="{f["path"]}" 
                     style="display: flex; flex-direction: column; cursor: pointer; padding: 15px; border-radius: 8px; 
                     border: 1px solid #e2e8f0; background-color: white; transition: all 0.2s;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 20px; margin-right: 8px;">{icon}</span>
                        <span style="font-weight: 500; flex-grow: 1; overflow: hidden; text-overflow: ellipsis;">{f["name"]}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #64748b; margin-top: auto;">
                        <span>{size_str}</span>
                        <span>{modified_date}</span>
                    </div>
                </div>
                '''
            
            grid_html += '</div>'
            
            # Add script to handle file selection
            grid_html += '''
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                document.querySelectorAll('.file-item').forEach(item => {
                    item.addEventListener('click', function() {
                        const path = this.getAttribute('data-path');
                        window.parent.postMessage({type: 'select_file', path: path}, '*');
                    });
                });
            });
            </script>
            '''
            
            st.markdown(grid_html, unsafe_allow_html=True)
        
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
        st.code(f"cd workspace/{st.session_state.project_id}\nls -la", language="bash")

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
        file_type = file_data.get("type", "")
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size/1024:.1f} KB"
        else:
            size_str = f"{file_size/(1024*1024):.1f} MB"
        
        # Create a modern file viewer
        file_viewer_html = f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 20px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            <!-- File header -->
            <div style="display: flex; justify-content: space-between; align-items: center; 
                 padding: 12px 15px; background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 10px;">📄</span>
                    <span style="font-weight: 600; font-size: 16px;">{file_name}</span>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <span style="font-size: 13px; color: #64748b;">{file_type.upper()}</span>
                    <span style="font-size: 13px; color: #64748b;">{size_str}</span>
                    <button id="close-file-btn" style="background: none; border: none; cursor: pointer; 
                            font-size: 16px; color: #64748b;">×</button>
                </div>
            </div>
        """
        
        # Determine language for syntax highlighting
        language = file_type
        language_map = {
            "py": "python",
            "js": "javascript",
            "jsx": "jsx",
            "ts": "typescript",
            "tsx": "tsx",
            "html": "html",
            "css": "css",
            "json": "json",
            "md": "markdown",
            "sh": "bash"
        }
        language = language_map.get(file_type, language)
        
        # Add file content placeholder - we'll use streamlit's code display for syntax highlighting
        file_viewer_html += """
            <!-- Content placeholder -->
            <div id="file-content">
                <!-- Streamlit code component will be rendered here -->
            </div>
        </div>
        
        <script>
        // Handle close button click
        document.addEventListener('DOMContentLoaded', function() {
            const closeBtn = document.getElementById('close-file-btn');
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    // Signal to clear the selected file
                    sessionStorage.setItem('clearSelectedFile', 'true');
                    window.location.reload();
                });
            }
        });
        </script>
        """
        
        # Render the file viewer HTML
        st.markdown(file_viewer_html, unsafe_allow_html=True)
        
        # Now render the code with syntax highlighting
        st.code(file_data["content"], language=language)
        
        # Handle file clear event from JavaScript
        if "clearSelectedFile" in st.session_state:
            st.session_state.selected_file = None
            del st.session_state.clearSelectedFile
            st.rerun()
            
    except Exception as e:
        st.error(f"Error displaying file: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e)) 