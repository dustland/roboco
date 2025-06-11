"""
Context Management Tools - Core Roboco Builtin Tools

Simple, focused tools for managing project context and shared state.
These tools enable cross-agent collaboration through persistent data storage.
"""

from typing import Any, Dict, AsyncGenerator, Type, Optional, List
from datetime import datetime
from pathlib import Path
import json

from pydantic import BaseModel, Field

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig


class ContextSaveParams(BaseModel):
    """Parameters for saving context data."""
    category: str = Field(..., description="Context category (search_results, documents, etc.)")
    key: str = Field(..., description="Unique identifier for this data")
    data: Dict[str, Any] = Field(..., description="The data to save")
    agent_id: str = Field(default="unknown", description="ID of the agent saving the data")


class ContextLoadParams(BaseModel):
    """Parameters for loading context data."""
    category: str = Field(..., description="Context category to load from")
    key: str = Field(..., description="Unique identifier of the data to load")


class ContextListParams(BaseModel):
    """Parameters for listing context data."""
    category: Optional[str] = Field(default=None, description="Specific category to list (optional)")


class ContextSaveTool(AbstractTool):
    """
    Save data to persistent context storage.
    
    This tool allows agents to save their work results for later use by
    other agents, enabling cross-agent collaboration.
    """
    
    def __init__(self, workspace_dir: str = "./workspace/context"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard context categories
        self.categories = {
            "search_results", "documents", "research", "tasks", 
            "reviews", "drafts", "sources", "metadata"
        }
    
    @property
    def name(self) -> str:
        return "context_save"
    
    @property
    def description(self) -> str:
        return "Save data to persistent context storage for cross-agent collaboration"
    
    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="category",
                type="string",
                description="Context category (search_results, documents, research, tasks, etc.)",
                required=True
            ),
            ToolParameterConfig(
                name="key",
                type="string", 
                description="Unique identifier for this data",
                required=True
            ),
            ToolParameterConfig(
                name="data",
                type="object",
                description="The data to save",
                required=True
            ),
            ToolParameterConfig(
                name="agent_id",
                type="string",
                description="ID of the agent saving the data",
                required=False,
                default="unknown"
            )
        ]
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return configuration schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "workspace_dir": {
                    "type": "string",
                    "description": "Directory path for context storage",
                    "default": "./workspace/context"
                }
            }
        }
    
    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """Stream version of context save (yields progress updates)."""
        result = await self.run(input_data, config)
        yield result
    
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        params = ContextSaveParams(**kwargs)
        
        # Create category directory
        category_dir = self.workspace_dir / params.category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data with metadata
        context_data = {
            "key": params.key,
            "category": params.category,
            "agent_id": params.agent_id,
            "timestamp": datetime.now().isoformat(),
            "data": params.data
        }
        
        # Save to file
        file_path = category_dir / f"{params.key}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            return {
                "success": True,
                "category": params.category,
                "key": params.key,
                "file_path": str(file_path),
                "agent_id": params.agent_id,
                "timestamp": context_data["timestamp"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save context: {str(e)}"
            }


class ContextLoadTool(AbstractTool):
    """
    Load data from persistent context storage.
    
    This tool allows agents to retrieve data saved by other agents,
    enabling cross-agent collaboration and project continuity.
    """
    
    def __init__(self, workspace_dir: str = "./workspace/context"):
        self.workspace_dir = Path(workspace_dir)
    
    @property
    def name(self) -> str:
        return "context_load"
    
    @property
    def description(self) -> str:
        return "Load data from persistent context storage"
    
    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="category",
                type="string",
                description="Context category to load from",
                required=True
            ),
            ToolParameterConfig(
                name="key",
                type="string",
                description="Unique identifier of the data to load",
                required=True
            )
        ]
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return configuration schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "workspace_dir": {
                    "type": "string",
                    "description": "Directory path for context storage",
                    "default": "./workspace/context"
                }
            }
        }
    
    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """Stream version of context load."""
        result = await self.run(input_data, config)
        yield result
    
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        params = ContextLoadParams(**kwargs)
        
        # Locate file
        category_dir = self.workspace_dir / params.category
        file_path = category_dir / f"{params.key}.json"
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Context not found: {params.category}/{params.key}"
            }
        
        try:
            with open(file_path, 'r') as f:
                context_data = json.load(f)
            
            return {
                "success": True,
                "category": params.category,
                "key": params.key,
                "data": context_data["data"],
                "metadata": {
                    "agent_id": context_data.get("agent_id"),
                    "timestamp": context_data.get("timestamp")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load context: {str(e)}"
            }


class ContextListTool(AbstractTool):
    """
    List available context data.
    
    This tool allows agents to discover what context data is available,
    helping them understand what information has been saved by other agents.
    """
    
    def __init__(self, workspace_dir: str = "./workspace/context"):
        self.workspace_dir = Path(workspace_dir)
    
    @property
    def name(self) -> str:
        return "context_list"
    
    @property
    def description(self) -> str:
        return "List available context data by category"
    
    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="category",
                type="string",
                description="Specific category to list (optional - lists all if not provided)",
                required=False
            )
        ]
    
    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Return configuration schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "workspace_dir": {
                    "type": "string",
                    "description": "Directory path for context storage",
                    "default": "./workspace/context"
                }
            }
        }
    
    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """Stream version of context list."""
        result = await self.run(input_data, config)
        yield result
    
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        params = ContextListParams(**kwargs)
        
        try:
            if not self.workspace_dir.exists():
                return {
                    "success": True,
                    "categories": {},
                    "total_items": 0
                }
            
            categories = {}
            total_items = 0
            
            if params.category:
                # List specific category
                category_dir = self.workspace_dir / params.category
                if category_dir.exists():
                    items = []
                    for json_file in category_dir.glob("*.json"):
                        try:
                            with open(json_file, 'r') as f:
                                data = json.load(f)
                            items.append({
                                "key": data.get("key", json_file.stem),
                                "agent_id": data.get("agent_id"),
                                "timestamp": data.get("timestamp"),
                                "file_path": str(json_file)
                            })
                        except Exception:
                            # Skip corrupted files
                            continue
                    categories[params.category] = items
                    total_items = len(items)
            else:
                # List all categories
                for category_dir in self.workspace_dir.iterdir():
                    if category_dir.is_dir():
                        items = []
                        for json_file in category_dir.glob("*.json"):
                            try:
                                with open(json_file, 'r') as f:
                                    data = json.load(f)
                                items.append({
                                    "key": data.get("key", json_file.stem),
                                    "agent_id": data.get("agent_id"),
                                    "timestamp": data.get("timestamp"),
                                    "file_path": str(json_file)
                                })
                            except Exception:
                                # Skip corrupted files
                                continue
                        if items:  # Only include categories with items
                            categories[category_dir.name] = items
                            total_items += len(items)
            
            return {
                "success": True,
                "categories": categories,
                "total_items": total_items
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list context: {str(e)}"
            } 