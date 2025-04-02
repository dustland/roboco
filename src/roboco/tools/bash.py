"""
Bash Tool

This module provides a tool for executing bash commands,
designed to be compatible with autogen's function calling mechanism.
"""

import os
import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from loguru import logger

from roboco.core.tool import Tool, command
from roboco.core.project_fs import ProjectFS

# Initialize logger
logger = logger.bind(module=__name__)

class BashTool(Tool):
    """Tool for executing bash commands in the terminal."""
    
    def __init__(self, fs: Optional[ProjectFS] = None):
        """
        Initialize the bash tool.
        
        Args:
            fs: Project filesystem instance to determine the project root directory
        """
        super().__init__(
            name="bash",
            description="Execute bash commands in the terminal"
        )
        
        # Initialize instance variables
        self._process = None
        self._running = False
        self._fs = fs
        self._project_root = fs.base_dir if fs else os.getcwd()
        
        logger.info(f"Initialized BashTool with project root: {self._project_root}")
    
    @command()
    def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a bash command in the terminal.
        
        Args:
            command: The bash command to execute
            timeout: Maximum execution time in seconds (default: 30)
            
        Returns:
            Dictionary with command output and execution info
        """
        try:
            # For long-running commands that should run in background
            if command.strip().endswith("&"):
                return self._execute_background_command(command)
            
            # For normal commands with timeout
            env = os.environ.copy()
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self._project_root,
                timeout=timeout,
                env=env
            )
            
            logger.info(f"Executed command: {command}")
            return {
                "success": True,
                "command": command,
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr
            }
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out after {timeout}s: {command}")
            return {
                "success": False,
                "command": command,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    def _execute_background_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a command in the background.
        
        Args:
            command: The command to execute
            
        Returns:
            Dictionary with execution info
        """
        try:
            # Remove the trailing & if present
            if command.strip().endswith("&"):
                command = command.strip()[:-1].strip()
            
            # Start the process
            env = os.environ.copy()
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._project_root,
                env=env
            )
            
            # Store the process
            self._process = process
            self._running = True
            
            logger.info(f"Started background command: {command}")
            return {
                "success": True,
                "command": command,
                "pid": process.pid,
                "running": True,
                "message": f"Command started in background with PID {process.pid}"
            }
        except Exception as e:
            logger.error(f"Error starting background command '{command}': {e}")
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    @command()
    async def execute_interactive(self, command: str, timeout: int = 120) -> Dict[str, Any]:
        """
        Execute an interactive bash command with streaming output.
        This is an async version that can handle interactive commands.
        
        Args:
            command: The bash command to execute
            timeout: Maximum execution time in seconds (default: 120)
            
        Returns:
            Dictionary with command output and execution info
        """
        if self._running:
            return {
                "success": False,
                "error": "A command is already running. Please wait for it to complete."
            }
        
        try:
            self._running = True
            
            # Set up the process
            env = os.environ.copy()
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
                cwd=self._project_root,
                env=env
            )
            
            self._process = process
            
            # Stream output with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""
                
                logger.info(f"Completed interactive command: {command}")
                return {
                    "success": process.returncode == 0,
                    "command": command,
                    "output": stdout_str,
                    "error": stderr_str,
                    "return_code": process.returncode
                }
                
            except asyncio.TimeoutError:
                # Don't kill the process, just return what we have so far
                logger.warning(f"Interactive command timed out (still running): {command}")
                return {
                    "success": False,
                    "command": command,
                    "output": "Command is still running in the background.",
                    "error": f"Command timed out after {timeout} seconds but continues to run.",
                    "return_code": -1,
                    "timed_out": True
                }
                
        except Exception as e:
            logger.error(f"Error executing interactive command '{command}': {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "return_code": -1
            }
        finally:
            self._running = False
            self._process = None
    
    @command()
    def send_interrupt(self) -> Dict[str, Any]:
        """
        Send an interrupt signal (CTRL+C) to the currently running process.
        
        Returns:
            Dictionary with operation result info
        """
        if not self._process:
            return {
                "success": False,
                "error": "No interactive process is currently running."
            }
        
        try:
            # Send SIGINT to the process group
            self._process.terminate()
            logger.info("Sent interrupt signal to running process")
            return {
                "success": True,
                "message": "Interrupt signal sent to the process."
            }
        except Exception as e:
            logger.error(f"Error sending interrupt: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @command()
    def check_command_exists(self, command: str) -> Dict[str, Any]:
        """
        Check if a command exists in the system.
        
        Args:
            command: The command to check
            
        Returns:
            Dictionary indicating if command exists
        """
        try:
            # Use 'which' to check if command exists
            # Always execute this at the project root
            result = subprocess.run(
                f"which {command}",
                shell=True,
                capture_output=True,
                text=True,
                cwd=self._project_root
            )
            
            exists = result.returncode == 0
            path = result.stdout.strip() if exists else None
            
            return {
                "success": True,
                "command": command,
                "exists": exists,
                "path": path
            }
        except Exception as e:
            logger.error(f"Error checking command existence: {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }