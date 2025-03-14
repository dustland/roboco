"""
Bash Tool

This module provides a tool for executing bash commands,
designed to be compatible with autogen's function calling mechanism.
"""

import os
import asyncio
import subprocess
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from roboco.core.tool import Tool


class BashTool(Tool):
    """Tool for executing bash commands in the terminal."""
    
    def __init__(self):
        """Initialize the bash tool."""
        super().__init__(name="bash", description="Execute bash commands in the terminal")
        self._process = None
        self._running = False
        logger.info("Initialized BashTool")
    
    def execute_command(self, command: str, working_dir: str = None, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a bash command in the terminal.
        
        Args:
            command: The bash command to execute
            working_dir: The working directory for the command (optional)
            timeout: Maximum execution time in seconds (default: 30)
            
        Returns:
            Dictionary with command output and execution info
        """
        try:
            # For long-running commands that should run in background
            if command.strip().endswith("&"):
                return self._execute_background_command(command, working_dir)
            
            # For normal commands with timeout
            env = os.environ.copy()
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                env=env,
                timeout=timeout
            )
            
            logger.info(f"Executed command: {command}")
            return {
                "success": process.returncode == 0,
                "command": command,
                "output": process.stdout,
                "error": process.stderr,
                "return_code": process.returncode
            }
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {command}")
            return {
                "success": False,
                "command": command,
                "output": "",
                "error": f"Command timed out after {timeout} seconds",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Error executing command '{command}': {str(e)}")
            return {
                "success": False,
                "command": command,
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    def _execute_background_command(self, command: str, working_dir: str = None) -> Dict[str, Any]:
        """
        Execute a command in the background.
        
        Args:
            command: The bash command to execute (should end with &)
            working_dir: The working directory for the command (optional)
            
        Returns:
            Dictionary with basic execution info
        """
        try:
            # For background processes, don't capture output (it will be redirected)
            env = os.environ.copy()
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Just return immediately since it's a background process
            logger.info(f"Started background command: {command}")
            return {
                "success": True,
                "command": command,
                "message": f"Command started in background with PID {process.pid}",
                "pid": process.pid
            }
        except Exception as e:
            logger.error(f"Error starting background command '{command}': {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    async def execute_interactive(self, command: str, working_dir: str = None, timeout: int = 120) -> Dict[str, Any]:
        """
        Execute an interactive bash command with streaming output.
        This is an async version that can handle interactive commands.
        
        Args:
            command: The bash command to execute
            working_dir: The working directory for the command (optional)
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
                cwd=working_dir,
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
    
    def check_command_exists(self, command: str) -> Dict[str, Any]:
        """
        Check if a command exists in the system.
        
        Args:
            command: The command to check
            
        Returns:
            Dictionary with check result
        """
        try:
            # Use 'which' to check if the command exists
            process = subprocess.run(
                f"which {command.split()[0]}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            exists = process.returncode == 0
            
            if exists:
                path = process.stdout.strip()
                logger.info(f"Command '{command}' exists at: {path}")
                return {
                    "exists": True,
                    "command": command,
                    "path": path
                }
            else:
                logger.warning(f"Command '{command}' not found")
                return {
                    "exists": False,
                    "command": command
                }
        except Exception as e:
            logger.error(f"Error checking command existence: {str(e)}")
            return {
                "exists": False,
                "command": command,
                "error": str(e)
            }