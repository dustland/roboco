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
from loguru import logger

from roboco.core.tool import Tool


class TerminalTool(Tool):
    """Tool for executing terminal commands with directory persistence."""
    
    def __init__(self):
        """Initialize the terminal tool."""
        super().__init__(name="terminal", description="Execute terminal commands with directory tracking")
        self.current_path = os.getcwd()
        self._process = None
        self._running = False
        logger.info(f"Initialized TerminalTool in {self.current_path}")
    
    def execute(self, command: str, working_dir: str = None) -> Dict[str, Any]:
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
                # For chained commands, wrap in a subshell to maintain context
                wrapped_command = f"cd {shlex.quote(working_dir)} && {command}"
                process = subprocess.run(
                    wrapped_command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
            else:
                # For simple commands, use the specified working directory
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
                "current_directory": self.current_path
            }
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "current_directory": self.current_path
            }
    
    def _handle_cd_command(self, command: str) -> Dict[str, Any]:
        """
        Handle 'cd' command to change the current working directory.
        
        Args:
            command: The 'cd' command to process
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Extract the target directory
            parts = shlex.split(command)
            
            if len(parts) < 2:
                # 'cd' with no arguments goes to home directory
                new_path = os.path.expanduser("~")
            else:
                new_path = os.path.expanduser(parts[1])
            
            # Handle relative paths
            if not os.path.isabs(new_path):
                new_path = os.path.join(self.current_path, new_path)
            
            # Normalize the path
            new_path = os.path.abspath(new_path)
            
            # Verify the directory exists
            if os.path.isdir(new_path):
                self.current_path = new_path
                logger.info(f"Changed directory to {new_path}")
                return {
                    "success": True,
                    "command": command,
                    "output": f"Changed directory to {new_path}",
                    "current_directory": self.current_path
                }
            else:
                logger.warning(f"Directory not found: {new_path}")
                return {
                    "success": False,
                    "command": command,
                    "error": f"No such directory: {new_path}",
                    "current_directory": self.current_path
                }
        except Exception as e:
            logger.error(f"Error handling cd command: {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "current_directory": self.current_path
            }
    
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
    
    def get_current_directory(self) -> Dict[str, Any]:
        """
        Get the current working directory.
        
        Returns:
            Dictionary with current directory info
        """
        return {
            "success": True,
            "current_directory": self.current_path
        }