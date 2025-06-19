"""
Context Management Tools - LLM-friendly context tracking and management.

Provides flexible context management with loose JSON parsing and natural language
queries. Designed to work seamlessly with LLM agents without strict formatting.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from ..tool.models import Tool, tool, ToolResult
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ContextTool(Tool):
    """
    Generic context management tool for tracking project state, variables, and metadata.
    
    Features:
    - Loose JSON parsing (handles malformed JSON gracefully)
    - Natural language queries for context retrieval
    - Flexible key-value storage with nested objects
    - Automatic timestamping and versioning
    - File-based persistence with backup
    """
    
    def __init__(self, context_file: str = "context.json", workspace_path: str = "./workspace"):
        super().__init__()
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.context_file = self.workspace_path / context_file
        self.context_data = self._load_context()
    
    def _load_context(self) -> Dict[str, Any]:
        """Load context from file with error handling."""
        if not self.context_file.exists():
            return {
                "_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat()
                }
            }
        
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure metadata exists
                if "_metadata" not in data:
                    data["_metadata"] = {
                        "created_at": datetime.now().isoformat(),
                        "version": "1.0"
                    }
                data["_metadata"]["last_updated"] = datetime.now().isoformat()
                return data
        except Exception as e:
            logger.warning(f"Failed to load context file: {e}. Starting with empty context.")
            return {
                "_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "last_updated": datetime.now().isoformat(),
                    "load_error": str(e)
                }
            }
    
    def _save_context(self) -> bool:
        """Save context to file with backup."""
        try:
            # Create backup if file exists
            if self.context_file.exists():
                backup_file = self.context_file.with_suffix('.json.bak')
                self.context_file.rename(backup_file)
            
            # Update metadata
            self.context_data["_metadata"]["last_updated"] = datetime.now().isoformat()
            self.context_data["_metadata"]["version"] = str(float(self.context_data["_metadata"].get("version", "1.0")) + 0.1)
            
            # Save new file
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    def _parse_loose_json(self, json_str: str) -> Dict[str, Any]:
        """Parse JSON with error tolerance for LLM-generated content."""
        if not json_str.strip():
            return {}
        
        # Try direct JSON parsing first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Try to fix common LLM JSON issues
        try:
            # Remove markdown code blocks
            if json_str.strip().startswith('```'):
                lines = json_str.strip().split('\n')
                json_str = '\n'.join(lines[1:-1]) if len(lines) > 2 else json_str
            
            # Fix single quotes to double quotes
            json_str = json_str.replace("'", '"')
            
            # Try parsing again
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Last resort: extract key-value pairs with regex
        import re
        result = {}
        
        # Match "key": "value" or "key": value patterns
        patterns = [
            r'"([^"]+)":\s*"([^"]*)"',  # "key": "value"
            r'"([^"]+)":\s*([^,}\]]+)',  # "key": value
            r'([a-zA-Z_][a-zA-Z0-9_]*):\s*"([^"]*)"',  # key: "value"
            r'([a-zA-Z_][a-zA-Z0-9_]*):\s*([^,}\]]+)'   # key: value
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, json_str)
            for key, value in matches:
                # Try to parse value as number or boolean
                try:
                    if value.lower() in ['true', 'false']:
                        result[key] = value.lower() == 'true'
                    elif value.isdigit():
                        result[key] = int(value)
                    elif '.' in value and value.replace('.', '').isdigit():
                        result[key] = float(value)
                    else:
                        result[key] = value.strip('"\'')
                except:
                    result[key] = value.strip('"\'')
        
        return result
    
    @tool(description="Update context variables with flexible JSON input")
    async def update_context(
        self,
        updates: str,
        merge_strategy: str = "merge"
    ) -> ToolResult:
        """
        Update context variables with loose JSON parsing.
        
        Args:
            updates: JSON string or key-value pairs to update (flexible format)
            merge_strategy: How to handle updates - "merge", "replace", or "append"
        
        Returns:
            ToolResult with success status and updated context summary
        """
        try:
            # Parse the updates with error tolerance
            update_data = self._parse_loose_json(updates)
            
            if not update_data:
                return ToolResult(
                    success=False,
                    result=None,
                    error="No valid data found in updates"
                )
            
            # Apply updates based on strategy
            if merge_strategy == "replace":
                # Keep metadata but replace everything else
                metadata = self.context_data.get("_metadata", {})
                self.context_data = {"_metadata": metadata}
                self.context_data.update(update_data)
            elif merge_strategy == "append":
                # Append to lists, merge dicts, replace primitives
                for key, value in update_data.items():
                    if key in self.context_data:
                        if isinstance(self.context_data[key], list) and isinstance(value, list):
                            self.context_data[key].extend(value)
                        elif isinstance(self.context_data[key], dict) and isinstance(value, dict):
                            self.context_data[key].update(value)
                        else:
                            self.context_data[key] = value
                    else:
                        self.context_data[key] = value
            else:  # merge (default)
                # Deep merge for nested structures
                self._deep_merge(self.context_data, update_data)
            
            # Save to file
            saved = self._save_context()
            
            # Create summary of what was updated
            updated_keys = list(update_data.keys())
            summary = {
                "updated_keys": updated_keys,
                "total_context_keys": len([k for k in self.context_data.keys() if not k.startswith("_")]),
                "merge_strategy": merge_strategy,
                "saved_to_file": saved
            }
            
            return ToolResult(
                success=True,
                result=summary,
                metadata={"context_file": str(self.context_file)}
            )
            
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Context update failed: {str(e)}"
            )
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge source into target dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    @tool(description="Query context with natural language or specific keys")
    async def get_context(
        self,
        query: str = "",
        keys: Optional[str] = None,
        format_output: str = "json"
    ) -> ToolResult:
        """
        Retrieve context data with flexible querying.
        
        Args:
            query: Natural language query or empty for all context
            keys: Comma-separated list of specific keys to retrieve
            format_output: Output format - "json", "text", or "summary"
        
        Returns:
            ToolResult with requested context data
        """
        try:
            result_data = {}
            
            if keys:
                # Get specific keys
                key_list = [k.strip() for k in keys.split(",")]
                for key in key_list:
                    if key in self.context_data:
                        result_data[key] = self.context_data[key]
            elif query:
                # Natural language query - simple keyword matching
                query_lower = query.lower()
                for key, value in self.context_data.items():
                    if key.startswith("_"):
                        continue
                    
                    # Check if query matches key or value content
                    if (query_lower in key.lower() or 
                        (isinstance(value, str) and query_lower in value.lower()) or
                        (isinstance(value, dict) and any(query_lower in str(v).lower() for v in value.values()))):
                        result_data[key] = value
            else:
                # Return all non-metadata context
                result_data = {k: v for k, v in self.context_data.items() if not k.startswith("_")}
            
            # Format output
            if format_output == "text":
                text_output = []
                for key, value in result_data.items():
                    if isinstance(value, dict):
                        text_output.append(f"{key}:")
                        for sub_key, sub_value in value.items():
                            text_output.append(f"  {sub_key}: {sub_value}")
                    else:
                        text_output.append(f"{key}: {value}")
                formatted_result = "\n".join(text_output)
            elif format_output == "summary":
                formatted_result = {
                    "total_keys": len(result_data),
                    "keys": list(result_data.keys()),
                    "last_updated": self.context_data.get("_metadata", {}).get("last_updated"),
                    "sample_data": {k: v for k, v in list(result_data.items())[:3]}  # First 3 items
                }
            else:  # json
                formatted_result = result_data
            
            return ToolResult(
                success=True,
                result=formatted_result,
                metadata={
                    "query": query,
                    "keys_requested": keys,
                    "format": format_output,
                    "total_matches": len(result_data)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Context retrieval failed: {str(e)}"
            )
    
    @tool(description="Clear context data with optional backup")
    async def clear_context(
        self,
        backup: bool = True,
        keep_metadata: bool = True
    ) -> ToolResult:
        """
        Clear context data with optional backup.
        
        Args:
            backup: Whether to create a backup before clearing
            keep_metadata: Whether to preserve metadata
        
        Returns:
            ToolResult with operation status
        """
        try:
            if backup:
                backup_file = self.context_file.with_suffix(f'.json.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.context_data, f, indent=2, ensure_ascii=False)
            
            if keep_metadata:
                metadata = self.context_data.get("_metadata", {})
                self.context_data = {"_metadata": metadata}
            else:
                self.context_data = {}
            
            saved = self._save_context()
            
            return ToolResult(
                success=True,
                result={
                    "cleared": True,
                    "backup_created": backup,
                    "metadata_preserved": keep_metadata,
                    "saved_to_file": saved
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to clear context: {e}")
            return ToolResult(
                success=False,
                result=None,
                error=f"Context clear failed: {str(e)}"
            )