"""
Terminal Tool

This module provides a tool for executing terminal commands,
designed to be compatible with autogen's function calling mechanism.
"""

import os
import shlex
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
from roboco.core.logger import get_logger

from roboco.core.tool import Tool

# Initialize logger
logger = get_logger(__name__)

class TerminalTool(Tool):
    """Tool for executing terminal commands with directory persistence."""
    
    def __init__(self):
        """Initialize the terminal tool."""
        # Initialize instance variables
        self.current_path = os.getcwd()
        self._process = None
        self._running = False
        
        # Define the execute function
        def execute(command: str, working_dir: str = None) -> Dict[str, Any]:
            """
            Execute a terminal command and track directory changes.
            
            Args:
                command: The terminal command to execute
                working_dir: Optional override for the current working directory
                
            Returns:
                Dictionary with command output and execution info
            """
            # Use tracked path if working_dir not specified
            if working_dir is None:
                working_dir = self.current_path
            
            try:
                # Handle 'cd' command specially to track directory changes
                if command.lstrip().startswith("cd "):
                    return self._handle_cd_command(command)
                
                # Handle commands with chained execution
                if "&" in command or ";" in command or "&&" in command or "||" in command:
                    return self._handle_complex_command(command, working_dir)
                
                # Execute the command
                process = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=working_dir
                )
                
                logger.info(f"Executed command: {command}")
                return {
                    "success": process.returncode == 0,
                    "command": command,
                    "output": process.stdout,
                    "error": process.stderr,
                    "return_code": process.returncode,
                    "working_dir": working_dir
                }
            except Exception as e:
                logger.error(f"Error executing command '{command}': {e}")
                return {
                    "success": False,
                    "command": command,
                    "output": "",
                    "error": str(e),
                    "return_code": -1,
                    "working_dir": working_dir
                }
        
        # Define the get_current_directory function
        def get_current_directory() -> Dict[str, Any]:
            """
            Get the current working directory tracked by the terminal tool.
            
            Returns:
                Dictionary with current directory info
            """
            return {
                "success": True,
                "current_directory": self.current_path
            }
        
        # Initialize the Tool parent class with the execute function
        super().__init__(
            name="execute",
            description="Execute terminal commands with directory tracking",
            func_or_tool=execute
        )
        
        # Register the functions
        self.register_function(get_current_directory)
        
        logger.info(f"Initialized TerminalTool in {self.current_path}")
    
    def _handle_cd_command(self, command: str) -> Dict[str, Any]:
        """
        Handle 'cd' command to track directory changes.
        
        Args:
            command: The cd command to execute
            
        Returns:
            Dictionary with command execution info
        """
        try:
            # Extract the target directory
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                # 'cd' without arguments goes to home directory
                target_dir = os.path.expanduser("~")
            else:
                target_dir = parts[1].strip()
            
            # Handle relative paths
            if not os.path.isabs(target_dir):
                target_dir = os.path.normpath(os.path.join(self.current_path, target_dir))
            
            # Check if directory exists
            if not os.path.exists(target_dir):
                return {
                    "success": False,
                    "command": command,
                    "output": "",
                    "error": f"Directory not found: {target_dir}",
                    "return_code": 1,
                    "working_dir": self.current_path
                }
            
            if not os.path.isdir(target_dir):
                return {
                    "success": False,
                    "command": command,
                    "output": "",
                    "error": f"Not a directory: {target_dir}",
                    "return_code": 1,
                    "working_dir": self.current_path
                }
            
            # Update the current path
            old_path = self.current_path
            self.current_path = target_dir
            
            logger.info(f"Changed directory from {old_path} to {target_dir}")
            return {
                "success": True,
                "command": command,
                "output": f"Changed directory to {target_dir}",
                "error": "",
                "return_code": 0,
                "working_dir": target_dir
            }
        except Exception as e:
            logger.error(f"Error handling cd command '{command}': {e}")
            return {
                "success": False,
                "command": command,
                "output": "",
                "error": str(e),
                "return_code": 1,
                "working_dir": self.current_path
            }
    
    def _handle_complex_command(self, command: str, working_dir: str) -> Dict[str, Any]:
        """
        Handle complex commands with chained execution.
        
        Args:
            command: The complex command to execute
            working_dir: The working directory for the command
            
        Returns:
            Dictionary with command execution info
        """
        try:
            # Execute the command
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir
            )
            
            # Check if the command contains a cd command that we need to track
            if "cd " in command:
                # This is a best-effort approach - we'll try to extract the final directory
                # For complex commands, this might not always work perfectly
                self._update_directory_after_complex_command(command, working_dir)
            
            logger.info(f"Executed complex command: {command}")
            return {
                "success": process.returncode == 0,
                "command": command,
                "output": process.stdout,
                "error": process.stderr,
                "return_code": process.returncode,
                "working_dir": self.current_path  # Use the potentially updated path
            }
        except Exception as e:
            logger.error(f"Error executing complex command '{command}': {e}")
            return {
                "success": False,
                "command": command,
                "output": "",
                "error": str(e),
                "return_code": -1,
                "working_dir": working_dir
            }
    
    def _update_directory_after_complex_command(self, command: str, working_dir: str) -> None:
        """
        Update the current directory after executing a complex command.
        
        Args:
            command: The complex command that was executed
            working_dir: The working directory for the command
        """
        try:
            # Execute pwd to get the current directory
            process = subprocess.run(
                "pwd",
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir
            )
            
            if process.returncode == 0:
                new_dir = process.stdout.strip()
                if os.path.exists(new_dir) and os.path.isdir(new_dir):
                    self.current_path = new_dir
                    logger.info(f"Updated current directory to {new_dir} after complex command")
        except Exception as e:
            logger.warning(f"Failed to update directory after complex command: {e}")
            # Continue without updating the directory
    
    async def execute_async(self, command: str, working_dir: str = None, timeout: int = 60) -> Dict[str, Any]:
        """
        Execute a terminal command asynchronously.
        
        Args:
            command: The terminal command to execute
            working_dir: Optional override for the current working directory
            timeout: Maximum execution time in seconds
            
        Returns:
            Dictionary with command output and execution info
        """
        # Use tracked path if working_dir not specified
        if working_dir is None:
            working_dir = self.current_path
        
        try:
            # Handle 'cd' command specially to track directory changes
            if command.lstrip().startswith("cd "):
                return self._handle_cd_command(command)
            
            # Set up the subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            try:
                # Wait for the process to complete with timeout
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""
                
                logger.info(f"Executed async command: {command}")
                return {
                    "success": process.returncode == 0,
                    "command": command,
                    "output": stdout_str,
                    "error": stderr_str,
                    "return_code": process.returncode,
                    "current_directory": self.current_path
                }
            except asyncio.TimeoutError:
                # Handle timeout
                logger.warning(f"Command timed out: {command}")
                process.terminate()
                return {
                    "success": False,
                    "command": command,
                    "error": f"Command timed out after {timeout} seconds",
                    "timed_out": True,
                    "current_directory": self.current_path
                }
                
        except Exception as e:
            logger.error(f"Error executing async command '{command}': {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "current_directory": self.current_path
            }
    
    def list_directory(self, path: str = None) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            path: Directory path to list (defaults to current directory)
            
        Returns:
            Dictionary with directory contents
        """
        try:
            # Use specified path or current directory
            dir_path = path if path else self.current_path
            
            # Expand user directory if needed
            if '~' in dir_path:
                dir_path = os.path.expanduser(dir_path)
            
            # Verify the directory exists
            if not os.path.isdir(dir_path):
                return {
                    "success": False,
                    "error": f"Directory not found: {dir_path}",
                    "current_directory": self.current_path
                }
            
            # List directory contents
            entries = os.listdir(dir_path)
            
            # Separate files and directories
            files = []
            directories = []
            
            for entry in entries:
                entry_path = os.path.join(dir_path, entry)
                if os.path.isdir(entry_path):
                    directories.append(entry)
                else:
                    files.append(entry)
            
            return {
                "success": True,
                "directory": dir_path,
                "files": files,
                "directories": directories,
                "current_directory": self.current_path
            }
        except Exception as e:
            logger.error(f"Error listing directory: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "current_directory": self.current_path
            }