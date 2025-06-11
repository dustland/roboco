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


class AddMemoryTool:
    """Tool for adding memories to the system."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "add_memory"
        self.description = "Add new content to memory with automatic intelligent extraction"

    def __call__(
        self,
        content: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add content to memory."""
        try:
            result = self.memory_manager.add_memory(
                content=content,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                metadata=metadata
            )
            
            if result.get("success", True):
                return f"Memory added successfully. Results: {result}"
            else:
                return f"Failed to add memory: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            return f"Error adding memory: {str(e)}"


class SearchMemoryTool:
    """Tool for searching memories."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "search_memory"
        self.description = "Search memories using semantic similarity matching"

    def __call__(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 5
    ) -> str:
        """Search for relevant memories."""
        try:
            memories = self.memory_manager.search_memory(
                query=query,
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                limit=limit
            )
            
            if not memories:
                return "No relevant memories found."
            
            result = f"Found {len(memories)} relevant memories:\n\n"
            for i, memory in enumerate(memories, 1):
                result += f"{i}. ID: {memory['id']}\n"
                result += f"   Content: {memory['content']}\n"
                if memory.get('metadata'):
                    result += f"   Metadata: {memory['metadata']}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error searching memories: {str(e)}"


class ListMemoriesTool:
    """Tool for listing memories with optional filtering."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.name = "list_memories"
        self.description = "List memories with optional filtering by user, agent, or session"

    def __call__(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """List memories with optional filtering."""
        try:
            memories = self.memory_manager.list_memories(
                user_id=user_id,
                agent_id=agent_id,
                run_id=run_id,
                limit=limit
            )
            
            if not memories:
                filters = []
                if user_id:
                    filters.append(f"user_id={user_id}")
                if agent_id:
                    filters.append(f"agent_id={agent_id}")
                if run_id:
                    filters.append(f"run_id={run_id}")
                
                filter_str = f" (filters: {', '.join(filters)})" if filters else ""
                return f"No memories found{filter_str}."
            
            result = f"Found {len(memories)} memories:\n\n"
            for i, memory in enumerate(memories, 1):
                result += f"{i}. ID: {memory['id']}\n"
                result += f"   Content: {memory['content'][:100]}{'...' if len(memory['content']) > 100 else ''}\n"
                if memory.get('user_id'):
                    result += f"   User: {memory['user_id']}\n"
                if memory.get('agent_id'):
                    result += f"   Agent: {memory['agent_id']}\n"
                if memory.get('run_id'):
                    result += f"   Session: {memory['run_id']}\n"
                if memory.get('created_at'):
                    result += f"   Created: {memory['created_at']}\n"
                result += "\n"
            
            return result
            
        except Exception as e:
            return f"Error listing memories: {str(e)}"


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


def create_memory_tools(memory_manager: MemoryManager) -> List[Any]:
    """Create all memory tools for an agent."""
    return [
        AddMemoryTool(memory_manager),
        SearchMemoryTool(memory_manager),
        ListMemoriesTool(memory_manager),
        GetMemoryTool(memory_manager),
        UpdateMemoryTool(memory_manager),
        DeleteMemoryTool(memory_manager),
        ClearMemoriesTool(memory_manager),
        MemoryStatsTool(memory_manager),
    ] 