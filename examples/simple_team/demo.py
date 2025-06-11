#!/usr/bin/env python3
"""
Demo script showing Roboco's multi-agent collaboration with Mem0 memory integration.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from roboco.core.team_builder import TeamBuilder
from roboco.memory.manager import MemoryManager
from roboco.config.models import MemoryConfig


def demo_memory_system():
    """Demonstrate Mem0 memory system capabilities."""
    print("=== Roboco Memory System Demo (Mem0) ===\n")
    
    try:
        # Initialize memory manager with embedded vector store
        print("1. Initializing Mem0 memory system...")
        
        # Configure to use ChromaDB (embedded, no server required)
        memory_config = MemoryConfig()
        memory_config.vector_store = {
            "provider": "chroma",
            "config": {
                "collection_name": "roboco_demo",
                "path": "./demo_memory_db"  # Local file-based storage
            }
        }
        
        memory_manager = MemoryManager(memory_config)
        print("✓ Memory system initialized with Mem0 backend (ChromaDB)\n")
        
        # Test adding memories
        print("2. Adding memories...")
        
        # Add a conversation memory
        conversation = [
            {"role": "user", "content": "I love Italian food, especially pasta carbonara"},
            {"role": "assistant", "content": "That's great! Carbonara is a classic Roman dish with eggs, cheese, and pancetta."}
        ]
        
        result1 = memory_manager.add_memory(
            content=conversation,
            user_id="demo_user",
            metadata={"topic": "food_preferences", "cuisine": "italian"}
        )
        print(f"Added conversation memory: {result1}")
        
        # Add individual facts
        result2 = memory_manager.add_memory(
            content="User prefers working in the morning and takes breaks every 2 hours",
            user_id="demo_user",
            metadata={"topic": "work_habits"}
        )
        print(f"Added work habits memory: {result2}")
        
        result3 = memory_manager.add_memory(
            content="The user mentioned they are learning Python and interested in AI development",
            agent_id="assistant_agent",
            metadata={"topic": "learning_goals"}
        )
        print(f"Added learning goals memory: {result3}\n")
        
        # Test searching memories
        print("3. Searching memories...")
        
        search_results = memory_manager.search_memory(
            query="What kind of food does the user like?",
            user_id="demo_user",
            limit=3
        )
        
        print(f"Search results for food preferences:")
        for i, memory in enumerate(search_results, 1):
            print(f"  {i}. {memory['content']}")
        print()
        
        # Test listing memories
        print("4. Listing all user memories...")
        user_memories = memory_manager.list_memories(user_id="demo_user", limit=10)
        print(f"Found {len(user_memories)} memories for demo_user:")
        for i, memory in enumerate(user_memories, 1):
            print(f"  {i}. {memory['content'][:80]}{'...' if len(memory['content']) > 80 else ''}")
        print()
        
        # Test agent memories
        print("5. Listing agent memories...")
        agent_memories = memory_manager.list_memories(agent_id="assistant_agent", limit=10)
        print(f"Found {len(agent_memories)} memories for assistant_agent:")
        for i, memory in enumerate(agent_memories, 1):
            print(f"  {i}. {memory['content'][:80]}{'...' if len(memory['content']) > 80 else ''}")
        print()
        
        # Get memory stats
        print("6. Memory system statistics...")
        stats = memory_manager.get_stats()
        print(f"Backend: {stats.get('backend', 'unknown')}")
        print(f"Total memories: {stats.get('total_memories', 0)}")
        print(f"Version: {stats.get('version', 'unknown')}")
        
        if 'error' in stats:
            print(f"Note: {stats['error']}")
        
        print("\n✓ Memory system demo completed successfully!")
        
    except ImportError as e:
        print(f"❌ Memory system requires additional dependencies: {e}")
        print("Install with: pip install mem0ai")
        return False
    except Exception as e:
        print(f"❌ Error during memory demo: {e}")
        return False
    
    return True


def demo_team_builder():
    """Demonstrate team building with memory integration."""
    print("\n=== Team Builder Demo ===\n")
    
    try:
        # Initialize team builder
        print("1. Initializing team builder...")
        config_path = Path(__file__).parent / "config"
        team_builder = TeamBuilder(config_path)
        print("✓ Team builder initialized\n")
        
        # Load team configuration
        print("2. Loading team configuration...")
        team_config_path = config_path / "team.yaml"
        
        if not team_config_path.exists():
            print(f"❌ Team config not found at {team_config_path}")
            return False
        
        team = team_builder.build_team(str(team_config_path))
        print(f"✓ Team loaded: {len(team.agents)} agents")
        
        # List agents
        for i, (name, agent) in enumerate(team.agents.items(), 1):
            print(f"  {i}. {name} ({type(agent).__name__})")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during team demo: {e}")
        return False


async def main():
    """Main demo function."""
    print("🤖 Welcome to Roboco Demo!\n")
    
    # Check for OpenAI API key if using default config
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Note: Set OPENAI_API_KEY environment variable for full functionality")
        print("   Some features may not work without proper API keys\n")
    
    # Run memory system demo
    memory_success = demo_memory_system()
    
    # Run team builder demo
    team_success = demo_team_builder()
    
    # Summary
    print("\n" + "="*50)
    print("Demo Summary:")
    print(f"  Memory System: {'✓ Success' if memory_success else '❌ Failed'}")
    print(f"  Team Builder:  {'✓ Success' if team_success else '❌ Failed'}")
    
    if memory_success and team_success:
        print("\n🎉 All demos completed successfully!")
        print("   You can now use Roboco with intelligent memory capabilities!")
    else:
        print("\n⚠️  Some demos failed. Check the error messages above.")
    
    print("\nNext steps:")
    print("  1. Explore the config files in examples/simple_team/config/")
    print("  2. Customize team configurations for your use case")
    print("  3. Integrate memory tools with your agents")
    print("  4. Check out the documentation for advanced features")


if __name__ == "__main__":
    asyncio.run(main()) 