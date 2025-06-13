"""
Memory Tools - Decorator-based implementation using the new Tool system.
"""

import os
from typing import Annotated, Optional
from roboco.tool.base import Tool, tool

# Global memory manager instance
_memory_manager = None

def set_memory_manager(manager):
    """Set the global memory manager instance."""
    global _memory_manager
    _memory_manager = manager

def get_memory_manager():
    """Get the global memory manager instance."""
    return _memory_manager

class MemoryTool(Tool):
    """Memory management capabilities using the new decorator-based system."""
    
    def __init__(self, memory_manager=None):
        super().__init__()
        self.memory_manager = memory_manager or get_memory_manager()
        if not self.memory_manager:
            raise ValueError("Memory manager is required")
    
    @tool(name="add_memory", description="Add content to persistent memory with automatic intelligent extraction")
    async def add_memory(
        self,
        task_id: str,
        agent_id: str,
        content: Annotated[str, "Content to store in memory"]
    ) -> str:
        """Store content in persistent memory with intelligent extraction."""
        try:
            # Use task_id as run_id for Mem0 compatibility
            result = await self.memory_manager.add(
                content=content,
                run_id=task_id,
                metadata={"agent_id": agent_id}
            )
            
            if isinstance(result, dict) and 'id' in result:
                memory_id = result['id']
                return f"✅ Memory added successfully with ID: {memory_id}"
            else:
                return f"✅ Memory added successfully: {str(result)}"
                
        except Exception as e:
            return f"❌ Failed to add memory: {str(e)}"
    
    @tool(name="search_memory", description="Search memories using semantic similarity matching")
    async def search_memory(
        self,
        task_id: str,
        agent_id: str,
        query: Annotated[str, "Search query for finding relevant memories"],
        limit: Annotated[int, "Maximum number of memories to return"] = 5
    ) -> str:
        """Search for relevant memories using semantic similarity."""
        try:
            # Use task_id as run_id for Mem0 compatibility
            results = await self.memory_manager.search(
                query=query,
                run_id=task_id,
                limit=limit
            )
            
            if not results:
                return "🔍 No relevant memories found for your query."
            
            # Format results for display
            formatted_results = []
            for i, memory in enumerate(results, 1):
                if isinstance(memory, dict):
                    content = memory.get('memory', memory.get('content', str(memory)))
                    score = memory.get('score', 'N/A')
                    formatted_results.append(f"{i}. {content} (relevance: {score})")
                else:
                    formatted_results.append(f"{i}. {str(memory)}")
            
            return f"🔍 Found {len(results)} relevant memories:\n\n" + "\n".join(formatted_results)
            
        except Exception as e:
            return f"❌ Failed to search memories: {str(e)}"
    
    @tool(name="list_memories", description="List recent memories from the current task session")
    async def list_memories(
        self,
        task_id: str,
        agent_id: str,
        limit: Annotated[int, "Maximum number of memories to list"] = 10
    ) -> str:
        """List recent memories from the current task session."""
        try:
            # Use task_id as run_id for Mem0 compatibility
            memories = await self.memory_manager.get_all(
                run_id=task_id,
                limit=limit
            )
            
            if not memories:
                return f"📝 No memories found for task: {task_id}"
            
            # Format memories for display
            formatted_memories = []
            for i, memory in enumerate(memories, 1):
                if isinstance(memory, dict):
                    content = memory.get('memory', memory.get('content', str(memory)))
                    created_at = memory.get('created_at', 'Unknown time')
                    formatted_memories.append(f"{i}. {content} (created: {created_at})")
                else:
                    formatted_memories.append(f"{i}. {str(memory)}")
            
            return f"📝 Recent memories for task {task_id}:\n\n" + "\n".join(formatted_memories)
            
        except Exception as e:
            return f"❌ Failed to list memories: {str(e)}"
    
    @tool(name="get_memory_stats", description="Get statistics about the memory system")
    async def get_memory_stats(
        self,
        task_id: str,
        agent_id: str
    ) -> str:
        """Get statistics about the memory system."""
        try:
            # Get task-specific memory count
            task_memories = await self.memory_manager.get_all(run_id=task_id)
            task_count = len(task_memories) if task_memories else 0
            
            # Get total memory count (if supported)
            try:
                all_memories = await self.memory_manager.get_all()
                total_count = len(all_memories) if all_memories else 0
            except:
                total_count = "Unknown"
            
            stats = [
                f"📊 Memory System Statistics:",
                f"",
                f"Current Task ({task_id}):",
                f"  • Memories: {task_count}",
                f"",
                f"System Total:",
                f"  • Total memories: {total_count}",
                f"  • Memory provider: {type(self.memory_manager).__name__}"
            ]
            
            return "\n".join(stats)
            
        except Exception as e:
            return f"❌ Failed to get memory stats: {str(e)}"

# Create a default instance for backward compatibility
def create_memory_tool(memory_manager=None):
    """Create a memory tool instance."""
    return MemoryTool(memory_manager)

# Export the tool class
__all__ = ['MemoryTool', 'create_memory_tool', 'set_memory_manager', 'get_memory_manager'] 