"""
Basic Tools - Decorator-based implementation using the new Tool system.
"""

import os
import asyncio
from pathlib import Path
from typing import Annotated
from ..core.tool import Tool, tool

class BasicTool(Tool):
    """Basic file system and utility tools using the new decorator-based system."""
    
    # Define required dependencies
    REQUIRED_DEPENDENCIES = {
        "workspace_path": "Path to the workspace directory for file operations"
    }
    
    def __init__(self, workspace_path: str = "./workspace"):
        super().__init__()
        self.workspace_path = Path(workspace_path).resolve()
        # Ensure workspace exists
        self.workspace_path.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace and validate security."""
        # Convert to Path and resolve
        target_path = (self.workspace_path / path).resolve()
        
        # Security check: ensure path is within workspace
        try:
            target_path.relative_to(self.workspace_path)
        except ValueError:
            raise PermissionError(f"Access denied: Path '{path}' is outside workspace")
        
        return target_path
    
    @tool(description="Echo back a message, potentially with a prefix")
    async def echo_message(
        self,
        task_id: str,
        agent_id: str,
        message: Annotated[str, "The message to echo back"],
        prefix: Annotated[str, "Optional prefix to add to the message"] = ""
    ) -> str:
        """Echo back a message with optional prefix."""
        if prefix:
            return f"{prefix}: {message}"
        return message
    
    @tool(description="Read the contents of a file within the workspace")
    async def read_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to read (relative to workspace)"]
    ) -> str:
        """Read file contents safely within workspace."""
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return f"❌ File not found: {path}"
            
            if not file_path.is_file():
                return f"❌ Path is not a file: {path}"
            
            # Read file with proper encoding detection
            try:
                content = file_path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                content = file_path.read_text(encoding='latin-1')
            
            return f"📄 Contents of {path}:\n\n{content}"
            
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"
    
    @tool(description="Write content to a file within the workspace")
    async def write_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to write (relative to workspace)"],
        content: Annotated[str, "Content to write to the file"]
    ) -> str:
        """Write content to file safely within workspace."""
        try:
            file_path = self._resolve_path(path)
            
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            file_path.write_text(content, encoding='utf-8')
            
            file_size = file_path.stat().st_size
            return f"✅ Successfully wrote {len(content)} characters ({file_size} bytes) to {path}"
            
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"
    
    @tool(description="List the contents of a directory within the workspace")
    async def list_directory(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Directory path to list (relative to workspace)"] = "."
    ) -> str:
        """List directory contents safely within workspace."""
        try:
            dir_path = self._resolve_path(path)
            
            if not dir_path.exists():
                return f"❌ Directory not found: {path}"
            
            if not dir_path.is_dir():
                return f"❌ Path is not a directory: {path}"
            
            # Get directory contents
            items = []
            for item in sorted(dir_path.iterdir()):
                relative_path = item.relative_to(self.workspace_path)
                if item.is_dir():
                    items.append(f"📁 {relative_path}/")
                else:
                    size = item.stat().st_size
                    items.append(f"📄 {relative_path} ({size} bytes)")
            
            if not items:
                return f"📂 Directory {path} is empty"
            
            return f"📂 Contents of {path}:\n\n" + "\n".join(items)
            
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"
    
    @tool(description="Check if a file or directory exists within the workspace")
    async def file_exists(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to check (relative to workspace)"]
    ) -> str:
        """Check if a file or directory exists within workspace."""
        try:
            file_path = self._resolve_path(path)
            
            if file_path.exists():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    return f"✅ File exists: {path} ({size} bytes)"
                elif file_path.is_dir():
                    item_count = len(list(file_path.iterdir()))
                    return f"✅ Directory exists: {path} ({item_count} items)"
                else:
                    return f"✅ Path exists: {path} (special file type)"
            else:
                return f"❌ Path does not exist: {path}"
                
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error checking path: {str(e)}"
    
    @tool(description="Create a directory within the workspace")
    async def create_directory(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Directory path to create (relative to workspace)"]
    ) -> str:
        """Create a directory safely within workspace."""
        try:
            dir_path = self._resolve_path(path)
            
            if dir_path.exists():
                if dir_path.is_dir():
                    return f"ℹ️ Directory already exists: {path}"
                else:
                    return f"❌ Path exists but is not a directory: {path}"
            
            # Create directory and any necessary parent directories
            dir_path.mkdir(parents=True, exist_ok=True)
            
            return f"✅ Successfully created directory: {path}"
            
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error creating directory: {str(e)}"
    
    @tool(description="Delete a file within the workspace")
    async def delete_file(
        self,
        task_id: str,
        agent_id: str,
        path: Annotated[str, "Path to the file to delete (relative to workspace)"]
    ) -> str:
        """Delete a file safely within workspace."""
        try:
            file_path = self._resolve_path(path)
            
            if not file_path.exists():
                return f"❌ File not found: {path}"
            
            if not file_path.is_file():
                return f"❌ Path is not a file: {path}"
            
            # Delete the file
            file_path.unlink()
            
            return f"✅ Successfully deleted file: {path}"
            
        except PermissionError as e:
            return f"❌ Permission denied: {str(e)}"
        except Exception as e:
            return f"❌ Error deleting file: {str(e)}"
    
    @tool(description="Hand off control to another agent in the team")
    async def handoff(
        self,
        task_id: str,
        agent_id: str,
        destination_agent: Annotated[str, "Name of the agent to hand off to"],
        reason: Annotated[str, "Reason for the handoff"],
        context: Annotated[str, "Additional context for the handoff"] = ""
    ) -> str:
        """
        Hand off control to another agent.
        
        This is a special tool that signals the orchestrator to switch
        the active agent to the specified destination agent.
        """
        # This tool returns a special marker that the orchestrator will recognize
        handoff_data = {
            "type": "handoff",
            "destination_agent": destination_agent,
            "reason": reason,
            "context": context,
            "from_agent": agent_id
        }
        
        # Return a special format that the orchestrator can detect
        return f"🔄 HANDOFF_REQUEST: {handoff_data}"

# Export the tool class
__all__ = ['BasicTool']
