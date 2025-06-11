from typing import Any, Dict, AsyncGenerator, Type, Optional, List

from pydantic import BaseModel, Field

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig

class EchoToolParams(BaseModel):
    """Parameters for invoking the EchoTool."""
    message: str = Field(..., description="The message to be echoed back.")
    prefix: str = Field(default="", description="An optional prefix to add to the echoed message at invocation time.")

class EchoToolInstanceConfig(BaseModel):
    """Configuration parameters for an instance of EchoTool."""
    name: str = Field(default="echo_tool", description="The name of this tool instance.")
    description: str = Field(default="Echoes back a message.", description="The description of this tool instance.")
    default_prefix: str = Field(default="", description="A default prefix configured on the tool instance itself, used if no prefix is provided at invocation.")

class EchoTool(AbstractTool):
    """
    A simple tool that echoes back a message, potentially with a prefix.
    The tool's behavior can be customized via instance configuration (e.g., a default prefix)
    and invocation parameters (e.g., the message and an overriding prefix).
    """
    _name: str
    _description: str
    _default_prefix: str

    def __init__(self, name: str = "echo_tool", description: str = "Echoes back a message.", default_prefix: str = ""):
        self._name = name
        self._description = description
        self._default_prefix = default_prefix

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @classmethod
    def get_config_schema(cls) -> Optional[Type[BaseModel]]:
        return EchoToolInstanceConfig

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        """Return the schema for tool invocation parameters."""
        return [
            ToolParameterConfig(
                name="message",
                type="string",
                description="The message to be echoed back.",
                required=True
            ),
            ToolParameterConfig(
                name="prefix",
                type="string",
                description="An optional prefix to add to the echoed message at invocation time.",
                required=False,
                default=""
            )
        ]

    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        params = EchoToolParams(**kwargs)
        prefix_to_use = params.prefix if params.prefix else self._default_prefix
        result = f"{prefix_to_use}{params.message}"
        return {"echoed_message": result, "status": "success"}

    async def stream(self, **kwargs: Any) -> AsyncGenerator[Dict[str, Any], None]:
        params = EchoToolParams(**kwargs)
        prefix_to_use = params.prefix if params.prefix else self._default_prefix
        
        if prefix_to_use:
            yield {"type": "prefix", "content": prefix_to_use, "is_final": False}
        
        if params.message:
            yield {"type": "message_part", "content": params.message, "is_final": False}
        
        final_echoed_message = f"{prefix_to_use}{params.message}"
        yield {"type": "final_result", "full_echo": final_echoed_message, "status": "success", "is_final": True}

class FileSystemTool(AbstractTool):
    """
    A tool for basic file system operations.
    
    Provides secure file operations like reading, writing, and listing files
    within a restricted workspace.
    """
    
    def __init__(self, workspace_path: str = "./workspace", **kwargs):
        """
        Initialize filesystem tool.
        
        Args:
            workspace_path: Base path for file operations (for security)
        """
        self.workspace_path = workspace_path
        
    @property
    def name(self) -> str:
        return "filesystem"
    
    @property
    def description(self) -> str:
        return "Perform file system operations like reading, writing, and listing files"
    
    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        """Return the schema for tool invocation parameters."""
        return [
            ToolParameterConfig(
                name="operation",
                type="string",
                description="Operation to perform: read, write, list, exists",
                required=True
            ),
            ToolParameterConfig(
                name="path",
                type="string", 
                description="File or directory path relative to workspace",
                required=True
            ),
            ToolParameterConfig(
                name="content",
                type="string",
                description="Content to write (only for write operation)",
                required=False,
                default=""
            )
        ]
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "workspace_path": {
                    "type": "string",
                    "description": "Base workspace path for file operations",
                    "default": "./workspace"
                }
            }
        }
    
    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute file system operation."""
        import os
        from pathlib import Path
        
        operation = input_data.get("operation")
        path = input_data.get("path")
        content = input_data.get("content", "")
        
        if not operation or not path:
            return {
                "success": False,
                "error": "Operation and path are required"
            }
        
        # Secure path resolution within workspace
        try:
            workspace = Path(self.workspace_path).resolve()
            target_path = (workspace / path).resolve()
            
            # Ensure target is within workspace
            if not str(target_path).startswith(str(workspace)):
                return {
                    "success": False,
                    "error": "Path outside workspace not allowed"
                }
            
            if operation == "read":
                if target_path.exists() and target_path.is_file():
                    try:
                        with open(target_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        return {
                            "success": True,
                            "operation": "read",
                            "path": str(path),
                            "content": content,
                            "size": len(content)
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Failed to read file: {e}"
                        }
                else:
                    return {
                        "success": False,
                        "error": "File does not exist or is not a file"
                    }
            
            elif operation == "write":
                try:
                    # Create parent directories if needed
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return {
                        "success": True,
                        "operation": "write", 
                        "path": str(path),
                        "size": len(content)
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to write file: {e}"
                    }
            
            elif operation == "list":
                try:
                    if target_path.exists():
                        if target_path.is_dir():
                            files = []
                            for item in target_path.iterdir():
                                files.append({
                                    "name": item.name,
                                    "type": "directory" if item.is_dir() else "file",
                                    "size": item.stat().st_size if item.is_file() else None
                                })
                            return {
                                "success": True,
                                "operation": "list",
                                "path": str(path),
                                "files": files
                            }
                        else:
                            return {
                                "success": False,
                                "error": "Path is not a directory"
                            }
                    else:
                        return {
                            "success": False,
                            "error": "Directory does not exist"
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to list directory: {e}"
                    }
            
            elif operation == "exists":
                return {
                    "success": True,
                    "operation": "exists",
                    "path": str(path),
                    "exists": target_path.exists(),
                    "type": "directory" if target_path.is_dir() else "file" if target_path.is_file() else None
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Filesystem operation failed: {e}"
            }
    
    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream filesystem operation results."""
        result = await self.run(input_data, config)
        yield result
