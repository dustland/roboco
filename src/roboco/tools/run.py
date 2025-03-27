"""
Run Tool

This module provides a lightweight tool for running shell commands asynchronously
with timeout control and output management.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple, Union
from loguru import logger

# Initialize logger
logger = logger.bind(module=__name__)

from roboco.core.tool import Tool


# Constants for output management
MAX_RESPONSE_LENGTH = 16000
TRUNCATED_MESSAGE = "<response clipped due to length>"


class RunTool(Tool):
    """
    Tool for running shell commands asynchronously with timeout control.
    Simpler than BashTool or TerminalTool, focused on one-off command execution.
    """
    
    def __init__(self):
        """Initialize the run tool."""
        
        # Define the maybe_truncate helper function
        def maybe_truncate(content: str, truncate_after: Optional[int] = MAX_RESPONSE_LENGTH) -> str:
            """
            Truncate content if it exceeds specified length.
            
            Args:
                content: String content to potentially truncate
                truncate_after: Maximum length before truncation
                
            Returns:
                Original or truncated content
            """
            if not truncate_after or len(content) <= truncate_after:
                return content
            return content[:truncate_after] + TRUNCATED_MESSAGE
        
        # Define the run function
        def run(command: str, timeout: Optional[float] = 120.0, working_dir: Optional[str] = None) -> Dict[str, Any]:
            """
            Run a shell command with timeout control.
            
            Args:
                command: The shell command to execute
                timeout: Maximum execution time in seconds (default: 120)
                working_dir: Working directory for command execution
                
            Returns:
                Dictionary with command output and execution info
            """
            try:
                # Create and run the command
                start_time = time.time()
                result = asyncio.run(self._run_command_async(command, timeout, working_dir))
                end_time = time.time()
                
                # Process the result
                stdout = maybe_truncate(result.get("stdout", ""))
                stderr = maybe_truncate(result.get("stderr", ""))
                
                logger.info(f"Command executed in {end_time - start_time:.2f}s: {command}")
                return {
                    "success": result.get("returncode", -1) == 0,
                    "command": command,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": result.get("returncode", -1),
                    "execution_time": end_time - start_time
                }
            except Exception as e:
                logger.error(f"Error executing command '{command}': {e}")
                return {
                    "success": False,
                    "command": command,
                    "error": str(e),
                    "stdout": "",
                    "stderr": "",
                    "returncode": -1
                }
        
        # Initialize the Tool parent class with the run function
        super().__init__(
            name="run",
            description="Run shell commands asynchronously with timeout control",
            func_or_tool=run
        )
        
        logger.info("Initialized RunTool")
    
    async def _run_command_async(
        self, 
        command: str, 
        timeout: Optional[float] = 120.0,
        working_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a shell command asynchronously with timeout control.
        
        Args:
            command: The shell command to execute
            timeout: Maximum execution time in seconds
            working_dir: Working directory for command execution
            
        Returns:
            Dictionary with command output and execution info
        """
        try:
            # Create the subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            # Wait for the process to complete with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                return {
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "returncode": process.returncode
                }
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                except Exception:
                    pass
                
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "returncode": -1
                }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "returncode": -1
            }