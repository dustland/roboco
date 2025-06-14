"""
Memory Tools - Clean implementation using TaskMemory.
"""

from typing import Annotated, Optional
from ..tool.base import Tool, tool
from ..core.memory import TaskMemory

class MemoryTool(Tool):
    """Memory management capabilities using TaskMemory."""
    
    def __init__(self, task_memory: TaskMemory):
        super().__init__()
        self.task_memory = task_memory
    
    @tool(name="add_memory", description="Add content to persistent memory with automatic intelligent extraction")
    def add_memory(
        self,
        task_id: str,
        agent_id: str,
        content: Annotated[str, "Content to store in memory"]
    ) -> str:
        """Store content in persistent memory with intelligent extraction."""
        try:
            result = self.task_memory.add(
                content=content,
                agent_id=agent_id,
                metadata={"source": "agent_tool"}
            )
            
            if isinstance(result, dict) and result.get("success", True):
                return f"✅ Memory added successfully"
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                return f"❌ Failed to add memory: {error_msg}"
                
        except Exception as e:
            return f"❌ Failed to add memory: {str(e)}"
    
    @tool(name="search_memory", description="Search memories using semantic similarity matching")
    def search_memory(
        self,
        task_id: str,
        agent_id: str,
        query: Annotated[str, "Search query for finding relevant memories"],
        limit: Annotated[int, "Maximum number of memories to return"] = 5
    ) -> str:
        """Search for relevant memories using semantic similarity."""
        try:
            results = self.task_memory.search(
                query=query,
                agent_id=agent_id,
                limit=limit
            )
            
            if not results:
                return "🔍 No relevant memories found for your query."
            
            # Format results for display
            formatted_results = []
            for i, memory in enumerate(results, 1):
                content = memory.get('content', 'No content')
                created_at = memory.get('created_at', 'Unknown time')
                formatted_results.append(f"{i}. {content} (created: {created_at})")
            
            return f"🔍 Found {len(results)} relevant memories:\n\n" + "\n".join(formatted_results)
            
        except Exception as e:
            return f"❌ Failed to search memories: {str(e)}"
    
    @tool(name="list_memories", description="List recent memories from the current task session")
    def list_memories(
        self,
        task_id: str,
        agent_id: str,
        limit: Annotated[int, "Maximum number of memories to list"] = 10
    ) -> str:
        """List recent memories from the current task session."""
        try:
            memories = self.task_memory.get_all(
                agent_id=agent_id,
                limit=limit
            )
            
            if not memories:
                return f"📝 No memories found for agent: {agent_id}"
            
            # Format memories for display
            formatted_memories = []
            for i, memory in enumerate(memories, 1):
                content = memory.get('content', 'No content')
                created_at = memory.get('created_at', 'Unknown time')
                formatted_memories.append(f"{i}. {content} (created: {created_at})")
            
            return f"📝 Recent memories for {agent_id}:\n\n" + "\n".join(formatted_memories)
            
        except Exception as e:
            return f"❌ Failed to list memories: {str(e)}"
    
    @tool(name="get_memory_stats", description="Get statistics about the memory system")
    def get_memory_stats(
        self,
        task_id: str,
        agent_id: str
    ) -> str:
        """Get statistics about the memory system."""
        try:
            stats = self.task_memory.get_stats()
            
            stats_lines = [
                f"📊 Memory System Statistics:",
                f"",
                f"Task ID: {stats.get('task_id', 'Unknown')}",
                f"Total memories: {stats.get('total_memories', 0)}",
                f"Active agents: {len(stats.get('agents', []))}",
            ]
            
            agents = stats.get('agents', [])
            if agents:
                stats_lines.append(f"Agents with memories: {', '.join(agents)}")
            
            return "\n".join(stats_lines)
            
        except Exception as e:
            return f"❌ Failed to get memory stats: {str(e)}"

    @tool(name="clear_memories", description="Clear all memories for the current agent")
    def clear_memories(
        self,
        task_id: str,
        agent_id: str
    ) -> str:
        """Clear all memories for the current agent."""
        try:
            result = self.task_memory.clear(agent_id=agent_id)
            
            if isinstance(result, dict) and result.get("success", True):
                return f"✅ Successfully cleared all memories for {agent_id}"
            else:
                error_msg = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                return f"❌ Failed to clear memories: {error_msg}"
                
        except Exception as e:
            return f"❌ Failed to clear memories: {str(e)}"

# Export the tool class
__all__ = ['MemoryTool'] 