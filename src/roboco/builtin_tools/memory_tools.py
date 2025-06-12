"""
Memory Tools

Built-in tools that provide agents access to the memory system.
These tools expose MemoryManager functionality through the tool interface.
"""

from typing import Dict, Any, List, Optional
import json

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig
from roboco.memory.manager import MemoryManager


class AddMemoryTool(AbstractTool):
    """Tool for adding memories to the system."""
    
    def __init__(self, memory_manager: MemoryManager, run_id: Optional[str] = None):
        self.memory_manager = memory_manager
        self.run_id = run_id

    @property
    def name(self) -> str:
        return "add_memory"

    @property
    def description(self) -> str:
        return "Add new content to memory with automatic intelligent extraction"

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="content",
                type="string",
                description="The content to store in memory",
                required=True
            ),
            ToolParameterConfig(
                name="agent_id",
                type="string",
                description="Agent identifier for this memory",
                required=False,
                default=None
            ),
            ToolParameterConfig(
                name="run_id",
                type="string",
                description="Task/session identifier for this memory",
                required=False,
                default=None
            ),
            ToolParameterConfig(
                name="metadata",
                type="object",
                description="Optional metadata to associate with the memory",
                required=False,
                default=None
            )
        ]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "description": "Memory tool requires no additional configuration"
        }

    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add content to memory."""
        try:
            # Use provided run_id or fall back to tool's run_id
            run_id = input_data.get("run_id") or self.run_id
            
            result = self.memory_manager.add_memory(
                content=input_data.get("content"),
                agent_id=input_data.get("agent_id"),
                run_id=run_id,
                metadata=input_data.get("metadata")
            )
            
            if result.get("success", True):
                return {"success": True, "message": "Memory added successfully", "result": result}
            else:
                return {"success": False, "error": result.get('error', 'Unknown error')}
                
        except Exception as e:
            return {"success": False, "error": f"Error adding memory: {str(e)}"}

    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None):
        """Stream memory addition result."""
        result = await self.run(input_data, config)
        yield result


class SearchMemoryTool(AbstractTool):
    """Tool for searching memories."""
    
    def __init__(self, memory_manager: MemoryManager, run_id: Optional[str] = None):
        self.memory_manager = memory_manager
        self.run_id = run_id

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Search memories using semantic similarity matching"

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="query",
                type="string",
                description="The search query",
                required=True
            ),
            ToolParameterConfig(
                name="run_id",
                type="string",
                description="Task/session identifier to filter by",
                required=False,
                default=None
            ),
            ToolParameterConfig(
                name="agent_id",
                type="string",
                description="Agent identifier to filter by",
                required=False,
                default=None
            ),
            ToolParameterConfig(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=5
            )
        ]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "description": "Memory tool requires no additional configuration"
        }

    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for relevant memories."""
        try:
            # Use provided run_id or fall back to tool's run_id
            run_id = input_data.get("run_id") or self.run_id
            agent_id = input_data.get("agent_id")
            
            # If no filtering parameters provided, use run_id for session isolation
            if not run_id and not agent_id:
                run_id = self.run_id
            
            memories = self.memory_manager.search_memory(
                query=input_data.get("query"),
                run_id=run_id,
                agent_id=agent_id,
                limit=input_data.get("limit", 5)
            )
            
            if not memories:
                return {"success": True, "message": "No relevant memories found", "memories": []}
            
            return {
                "success": True,
                "message": f"Found {len(memories)} relevant memories",
                "memories": memories
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error searching memories: {str(e)}"}

    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None):
        """Stream memory search results."""
        result = await self.run(input_data, config)
        yield result


class ListMemoriesTool(AbstractTool):
    """Tool for listing memories with optional filtering."""
    
    def __init__(self, memory_manager: MemoryManager, run_id: Optional[str] = None):
        self.memory_manager = memory_manager
        self.run_id = run_id

    @property
    def name(self) -> str:
        return "list_memories"

    @property
    def description(self) -> str:
        return "List memories with optional filtering"

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="run_id",
                type="string",
                description="Task/session identifier to filter by",
                required=False,
                default=None
            ),
            ToolParameterConfig(
                name="agent_id",
                type="string",
                description="Agent identifier to filter by",
                required=False,
                default=None
            ),
            ToolParameterConfig(
                name="limit",
                type="integer",
                description="Maximum number of results to return",
                required=False,
                default=10
            )
        ]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "description": "Memory tool requires no additional configuration"
        }

    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """List memories with optional filtering."""
        try:
            # Use provided run_id or fall back to tool's run_id
            run_id = input_data.get("run_id") or self.run_id
            agent_id = input_data.get("agent_id")
            
            # If no filtering parameters provided, use run_id for session isolation
            if not run_id and not agent_id:
                run_id = self.run_id
            
            memories = self.memory_manager.list_memories(
                run_id=run_id,
                agent_id=agent_id,
                limit=input_data.get("limit", 10)
            )
            
            if not memories:
                return {"success": True, "message": "No memories found", "memories": []}
            
            return {
                "success": True,
                "message": f"Found {len(memories)} memories",
                "memories": memories
            }
            
        except Exception as e:
            return {"success": False, "error": f"Error listing memories: {str(e)}"}

    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None):
        """Stream memory listing results."""
        result = await self.run(input_data, config)
        yield result


class GetMemoryTool:
    """Tool for retrieving a specific memory by ID."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "get_memory"
        self.description = "Retrieve a specific memory by its ID"

    def __call__(self, memory_id: str) -> str:
        """Get a specific memory by ID."""
        try:
            memory = self.memory_manager.get_memory(memory_id)
            
            if not memory:
                return f"Memory with ID {memory_id} not found."
            
            result = f"Memory ID: {memory['id']}\n"
            result += f"Content: {memory['content']}\n"
            if memory.get('user_id'):
                result += f"User: {memory['user_id']}\n"
            if memory.get('agent_id'):
                result += f"Agent: {memory['agent_id']}\n"
            if memory.get('run_id'):
                result += f"Session: {memory['run_id']}\n"
            if memory.get('metadata'):
                result += f"Metadata: {memory['metadata']}\n"
            if memory.get('created_at'):
                result += f"Created: {memory['created_at']}\n"
            if memory.get('updated_at'):
                result += f"Updated: {memory['updated_at']}\n"
            
            return result
            
        except Exception as e:
            return f"Error retrieving memory: {str(e)}"


class UpdateMemoryTool:
    """Tool for updating existing memories."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "update_memory"
        self.description = "Update the content of an existing memory"

    def __call__(self, memory_id: str, content: str) -> str:
        """Update a memory's content."""
        try:
            result = self.memory_manager.update_memory(memory_id, content)
            
            if result.get("success", True):
                return f"Memory {memory_id} updated successfully."
            else:
                return f"Failed to update memory: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error updating memory: {str(e)}"


class DeleteMemoryTool:
    """Tool for deleting memories."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "delete_memory"
        self.description = "Delete a specific memory by its ID"

    def __call__(self, memory_id: str) -> str:
        """Delete a memory by ID."""
        try:
            result = self.memory_manager.delete_memory(memory_id)
            
            if result.get("success", False):
                return f"Memory {memory_id} deleted successfully."
            else:
                return f"Failed to delete memory: {result.get('error', 'Memory not found')}"
                
        except Exception as e:
            return f"Error deleting memory: {str(e)}"


class ClearMemoriesTool:
    """Tool for clearing multiple memories."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "clear_memories"
        self.description = "Clear memories with optional filtering by user, agent, or session"

    def __call__(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        confirm: bool = False
    ) -> str:
        """Clear memories with optional filtering."""
        if not confirm:
            return "Warning: This will permanently delete memories. Set confirm=True to proceed."
        
        try:
            result = self.memory_manager.clear_memories(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id
            )
            
            if result.get("success", False):
                filters = []
                if user_id:
                    filters.append(f"user_id={user_id}")
                if agent_id:
                    filters.append(f"agent_id={agent_id}")
                if run_id:
                    filters.append(f"run_id={run_id}")
                
                filter_str = f" (filters: {', '.join(filters)})" if filters else " (all memories)"
                return f"Memories cleared successfully{filter_str}."
            else:
                return f"Failed to clear memories: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error clearing memories: {str(e)}"


class MemoryStatsTool:
    """Tool for getting memory system statistics."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "memory_stats"
        self.description = "Get statistics about the memory system"

    def __call__(self) -> str:
        """Get memory system statistics."""
        try:
            stats = self.memory_manager.get_stats()
            
            result = "Memory System Statistics:\n"
            result += f"Total Memories: {stats.get('total_memories', 0)}\n"
            result += f"Backend: {stats.get('backend', 'unknown')}\n"
            result += f"Version: {stats.get('version', 'unknown')}\n"
            
            if 'error' in stats:
                result += f"Warning: {stats['error']}\n"
            
            return result
            
        except Exception as e:
            return f"Error getting memory stats: {str(e)}"


def create_memory_tools(memory_manager: MemoryManager, run_id: Optional[str] = None) -> List[AbstractTool]:
    """
    Create memory tools with optional run_id for session isolation.
    
    Args:
        memory_manager: The memory manager instance
        run_id: Optional task/session identifier for memory isolation
        
    Returns:
        List of memory tools
    """
    return [
        AddMemoryTool(memory_manager, run_id),
        SearchMemoryTool(memory_manager, run_id),
        ListMemoriesTool(memory_manager, run_id)
    ] 