"""
Advanced Context Management Tool

This tool provides sophisticated context management capabilities,
building on the basic context tools to provide document-level
and project-level context management.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncGenerator

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig


class ContextManagerTool(AbstractTool):
    """
    Core context management tool for Roboco framework.
    
    This tool provides persistent context storage that enables:
    - Cross-agent collaboration through shared state
    - Tool result persistence 
    - Project memory and continuity
    - Structured data organization by categories
    """
    
    def __init__(self, workspace_dir: str = "./workspace/context", name: str = "context_manager"):
        self._name = name
        self._description = "Manage project context and shared state using filesystem storage"
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Standard context categories for Roboco projects
        self.categories = {
            "search_results": self.workspace_dir / "search_results",
            "extracted_content": self.workspace_dir / "extracted_content", 
            "research_sources": self.workspace_dir / "research_sources",
            "task_plans": self.workspace_dir / "task_plans",
            "draft_sections": self.workspace_dir / "draft_sections", 
            "review_feedback": self.workspace_dir / "review_feedback",
            "final_documents": self.workspace_dir / "final_documents",
            "project_metadata": self.workspace_dir / "project_metadata",
            "agent_messages": self.workspace_dir / "agent_messages",
            "tool_outputs": self.workspace_dir / "tool_outputs"
        }
        
        # Create category directories
        for category_dir in self.categories.values():
            category_dir.mkdir(parents=True, exist_ok=True)
            
        # Initialize project metadata
        self._initialize_project_metadata()
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="action",
                type="string",
                description="Context action: 'save', 'load', 'list', 'search', 'delete'",
                required=True
            ),
            ToolParameterConfig(
                name="category",
                type="string",
                description="Context category (search_results, extracted_content, etc.)",
                required=False
            ),
            ToolParameterConfig(
                name="data",
                type="object", 
                description="Data to save (for save action)",
                required=False
            ),
            ToolParameterConfig(
                name="key",
                type="string",
                description="Unique key/filename for the data",
                required=False
            ),
            ToolParameterConfig(
                name="agent_id",
                type="string",
                description="ID of the agent saving/loading data",
                required=False
            )
        ]
    
    async def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute context management operations."""
        action = kwargs.get("action")
        
        if action == "save":
            return await self._save_context(kwargs)
        elif action == "load":
            return await self._load_context(kwargs)
        elif action == "list":
            return await self._list_context(kwargs)
        elif action == "search":
            return await self._search_context(kwargs)
        elif action == "delete":
            return await self._delete_context(kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": ["save", "load", "list", "search", "delete"]
            }
    
    async def _save_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save data to context storage."""
        category = params.get("category")
        data = params.get("data")
        key = params.get("key")
        agent_id = params.get("agent_id", "unknown")
        
        if not category or not data or not key:
            return {
                "success": False,
                "error": "Missing required parameters: category, data, key"
            }
        
        if category not in self.categories:
            return {
                "success": False,
                "error": f"Unknown category: {category}",
                "available_categories": list(self.categories.keys())
            }
        
        # Prepare data with metadata
        context_data = {
            "key": key,
            "category": category,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Save to category directory
        category_dir = self.categories[category]
        file_path = category_dir / f"{key}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(context_data, f, indent=2)
            
            return {
                "success": True,
                "action": "save",
                "category": category,
                "key": key,
                "file_path": str(file_path),
                "agent_id": agent_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save context: {str(e)}"
            }
    
    async def _load_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load data from context storage."""
        category = params.get("category")
        key = params.get("key")
        
        if not category or not key:
            return {
                "success": False,
                "error": "Missing required parameters: category, key"
            }
        
        if category not in self.categories:
            return {
                "success": False,
                "error": f"Unknown category: {category}",
                "available_categories": list(self.categories.keys())
            }
        
        # Load from category directory
        category_dir = self.categories[category]
        file_path = category_dir / f"{key}.json"
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Context not found: {category}/{key}"
            }
        
        try:
            with open(file_path, 'r') as f:
                context_data = json.load(f)
            
            return {
                "success": True,
                "action": "load",
                "category": category,
                "key": key,
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
    
    async def _list_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available context data."""
        category = params.get("category")
        
        if category and category not in self.categories:
            return {
                "success": False,
                "error": f"Unknown category: {category}",
                "available_categories": list(self.categories.keys())
            }
        
        # List specific category or all categories
        if category:
            categories_to_list = {category: self.categories[category]}
        else:
            categories_to_list = self.categories
        
        context_listing = {}
        
        for cat_name, cat_dir in categories_to_list.items():
            context_listing[cat_name] = []
            
            if cat_dir.exists():
                for file_path in cat_dir.glob("*.json"):
                    try:
                        with open(file_path, 'r') as f:
                            context_data = json.load(f)
                        
                        context_listing[cat_name].append({
                            "key": context_data.get("key", file_path.stem),
                            "agent_id": context_data.get("agent_id"),
                            "timestamp": context_data.get("timestamp"),
                            "size": file_path.stat().st_size
                        })
                    except Exception:
                        # Skip corrupted files
                        continue
        
        return {
            "success": True,
            "action": "list",
            "category": category,
            "context_data": context_listing,
            "total_items": sum(len(items) for items in context_listing.values())
        }
    
    async def _search_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search context data by query."""
        query = params.get("query", "").lower()
        category = params.get("category")
        
        if not query:
            return {
                "success": False,
                "error": "Search query is required"
            }
        
        search_results = []
        categories_to_search = {category: self.categories[category]} if category else self.categories
        
        for cat_name, cat_dir in categories_to_search.items():
            if not cat_dir.exists():
                continue
                
            for file_path in cat_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        context_data = json.load(f)
                    
                    # Simple text search in data
                    data_str = json.dumps(context_data.get("data", {})).lower()
                    if query in data_str or query in context_data.get("key", "").lower():
                        search_results.append({
                            "category": cat_name,
                            "key": context_data.get("key"),
                            "agent_id": context_data.get("agent_id"),
                            "timestamp": context_data.get("timestamp"),
                            "relevance": data_str.count(query)
                        })
                except Exception:
                    continue
        
        search_results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return {
            "success": True,
            "action": "search",
            "query": query,
            "results": search_results[:20],
            "total_found": len(search_results)
        }
    
    async def _delete_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete context data."""
        category = params.get("category")
        key = params.get("key")
        
        if not category or not key:
            return {
                "success": False,
                "error": "Missing required parameters: category, key"
            }
        
        if category not in self.categories:
            return {
                "success": False,
                "error": f"Unknown category: {category}",
                "available_categories": list(self.categories.keys())
            }
        
        category_dir = self.categories[category]
        file_path = category_dir / f"{key}.json"
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Context not found: {category}/{key}"
            }
        
        try:
            file_path.unlink()
            return {
                "success": True,
                "action": "delete",
                "category": category,
                "key": key
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete context: {str(e)}"
            }
    
    def _initialize_project_metadata(self):
        """Initialize project metadata file."""
        metadata_file = self.workspace_dir / "project_meta.json"
        
        if not metadata_file.exists():
            initial_metadata = {
                "project_id": f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "statistics": {
                    "total_saves": 0,
                    "total_loads": 0,
                    "total_deletes": 0
                },
                "categories": list(self.categories.keys())
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(initial_metadata, f, indent=2)
    
    async def _update_category_index(self, category: str, key: str, data: Optional[Dict], delete: bool = False):
        """Update the index for a category."""
        index_file = self.categories[category] / "_index.json"
        
        # Load existing index
        if index_file.exists():
            with open(index_file, 'r') as f:
                index = json.load(f)
        else:
            index = {"category": category, "items": {}, "last_updated": None}
        
        # Update index
        if delete:
            index["items"].pop(key, None)
        else:
            index["items"][key] = {
                "timestamp": data.get("timestamp"),
                "agent_id": data.get("agent_id"),
                "size": len(json.dumps(data.get("data", {}))),
                "has_metadata": bool(data.get("metadata"))
            }
        
        index["last_updated"] = datetime.now().isoformat()
        index["item_count"] = len(index["items"])
        
        # Save updated index
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    async def _update_project_stats(self, category: str, operation: str):
        """Update project-level statistics."""
        metadata_file = self.workspace_dir / "project_meta.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"statistics": {"total_saves": 0, "total_loads": 0, "total_deletes": 0}}
        
        # Update stats
        if operation == "save":
            metadata["statistics"]["total_saves"] = metadata["statistics"].get("total_saves", 0) + 1
        elif operation == "load":
            metadata["statistics"]["total_loads"] = metadata["statistics"].get("total_loads", 0) + 1
        elif operation == "delete":
            metadata["statistics"]["total_deletes"] = metadata["statistics"].get("total_deletes", 0) + 1
        
        metadata["last_updated"] = datetime.now().isoformat()
        metadata["last_operation"] = {"type": operation, "category": category, "timestamp": datetime.now().isoformat()}
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2) 