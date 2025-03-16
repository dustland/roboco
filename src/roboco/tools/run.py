"""
Run Tool

This module provides a lightweight tool for running shell commands asynchronously
with timeout control and output management.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Tuple, Union
from loguru import logger

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
        super().__init__(name="run", description="Run shell commands asynchronously with timeout control")
        logger.info("Initialized RunTool")
    
    def maybe_truncate(self, content: str, truncate_after: Optional[int] = MAX_RESPONSE_LENGTH) -> str:
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
    
    async def run_async(
        self, 
        command: str, 
        timeout: Optional[float] = 120.0,
        truncate_after: Optional[int] = MAX_RESPONSE_LENGTH
    ) -> Dict[str, Any]:
        """
        Run a shell command asynchronously with timeout control.
        
        Args:
            command: Shell command to run
            timeout: Maximum execution time in seconds
            truncate_after: Maximum length for command output
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        try:
            process = await asyncio.create_subprocess_shell(
                command, 
                stdout=asyncio.subprocess.PIPE, 
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                stdout_str = self.maybe_truncate(
                    stdout.decode() if stdout else "", 
                    truncate_after=truncate_after
                )
                stderr_str = self.maybe_truncate(
                    stderr.decode() if stderr else "", 
                    truncate_after=truncate_after
                )
                
                execution_time = time.time() - start_time
                logger.info(f"Command '{command}' completed in {execution_time:.2f}s")
                
                return {
                    "success": process.returncode == 0,
                    "command": command,
                    "return_code": process.returncode or 0,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "execution_time": execution_time,
                    "timeout_reached": False
                }
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.warning(f"Command '{command}' timed out after {timeout} seconds")
                
                # Attempt to kill the process
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                    
                return {
                    "success": False,
                    "command": command,
                    "error": f"Command timed out after {timeout} seconds",
                    "execution_time": execution_time,
                    "timeout_reached": True
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error running command '{command}': {str(e)}")
            
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "execution_time": execution_time,
                "timeout_reached": False
            }
    
    def run(
        self, 
        command: str, 
        timeout: float = 120.0,
        truncate_after: int = MAX_RESPONSE_LENGTH
    ) -> Dict[str, Any]:
        """
        Run a shell command with timeout control (synchronous wrapper).
        
        Args:
            command: Shell command to run
            timeout: Maximum execution time in seconds
            truncate_after: Maximum length for command output
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Create an event loop if one doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # If we're not in an async context, create a new loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the command asynchronously
            result = loop.run_until_complete(
                self.run_async(command, timeout, truncate_after)
            )
            return result
            
        except Exception as e:
            logger.error(f"Error in synchronous run wrapper: {str(e)}")
            return {
                "success": False,
                "command": command,
                "error": str(e),
                "timeout_reached": False
            }