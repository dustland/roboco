#!/usr/bin/env python3
"""
Memory Backend Demo

Demonstrates the new memory backend architecture with Mem0 integration.
"""

import asyncio
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock agent class for demo
@dataclass
class MockAgent:
    name: str

async def demo_memory_backend():
    """Demonstrate the memory backend system."""
    
    try:
        from src.roboco.memory import create_memory_backend, MemoryQuery, MemoryType
        from src.roboco.config.models import MemoryConfig
        
        print("🧠 Memory Backend Demo")
        print("=" * 50)
        
        # Create memory backend with default config
        print("1. Creating Mem0 memory backend...")
        config = MemoryConfig()
        backend = create_memory_backend(config)
        
        # Check health
        print("2. Checking backend health...")
        health = await backend.health()
        print(f"   Status: {health['status']}")
        print(f"   Backend: {health['backend']}")
        
        # Add some memories
        print("3. Adding memories...")
        
        memory_id1 = await backend.add(
            content="Tesla's market share in EVs is growing rapidly",
            memory_type=MemoryType.TEXT,
            agent_name="researcher",
            metadata={"topic": "tesla", "source": "market_report"},
            importance=0.9
        )
        print(f"   Added memory: {memory_id1}")
        
        memory_id2 = await backend.add(
            content="EV charging infrastructure is expanding globally",
            memory_type=MemoryType.TEXT,
            agent_name="researcher", 
            metadata={"topic": "infrastructure", "source": "industry_news"},
            importance=0.8
        )
        print(f"   Added memory: {memory_id2}")
        
        memory_id3 = await backend.add(
            content="Battery technology improvements reduce costs",
            memory_type=MemoryType.TEXT,
            agent_name="analyst",
            metadata={"topic": "technology", "source": "tech_review"},
            importance=0.85
        )
        print(f"   Added memory: {memory_id3}")
        
        # Query memories
        print("4. Querying memories...")
        
        query = MemoryQuery(
            query="Tesla market trends",
            agent_name="researcher",
            limit=5
        )
        
        results = await backend.query(query)
        print(f"   Found {len(results.items)} memories in {results.query_time_ms:.1f}ms")
        
        for i, item in enumerate(results.items, 1):
            print(f"   {i}. {item.content[:60]}...")
            print(f"      Agent: {item.agent_name}, Importance: {item.importance}")
        
        # Search with filters
        print("5. Searching with metadata filters...")
        
        search_query = MemoryQuery(
            query="technology",
            metadata_filter={"topic": "technology"},
            limit=10
        )
        
        search_results = await backend.search(search_query)
        print(f"   Found {len(search_results.items)} technology-related memories")
        
        # Get statistics
        print("6. Getting memory statistics...")
        stats = await backend.stats()
        print(f"   Total memories: {stats.total_memories}")
        print(f"   Average importance: {stats.avg_importance:.2f}")
        print(f"   Memories by agent: {stats.memories_by_agent}")
        print(f"   Memories by type: {stats.memories_by_type}")
        
        # Count memories
        print("7. Counting memories...")
        total_count = await backend.count()
        researcher_count = await backend.count(agent_name="researcher")
        print(f"   Total memories: {total_count}")
        print(f"   Researcher memories: {researcher_count}")
        
        print("\n✅ Memory backend demo completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure mem0ai is installed: pip install mem0ai")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.exception("Demo error details:")

async def demo_core_memory_integration():
    """Demonstrate the core Memory class with backend integration."""
    
    try:
        from src.roboco.core.memory import Memory
        from src.roboco.config.models import MemoryConfig
        
        print("\n🔗 Core Memory Integration Demo")
        print("=" * 50)
        
        # Create mock agent
        agent = MockAgent(name="demo_agent")
        
        # Create memory with backend
        print("1. Creating Memory instance with backend...")
        config = MemoryConfig()
        memory = Memory(agent, config)
        
        # Save memories (async)
        print("2. Saving memories...")
        
        memory_id1 = await memory.save_async(
            "AI agents are becoming more collaborative",
            metadata={"type": "insight", "domain": "ai"},
            importance=0.9
        )
        print(f"   Saved: {memory_id1}")
        
        await memory.save_async(
            "Multi-agent systems require sophisticated memory management",
            metadata={"type": "requirement", "domain": "architecture"},
            importance=0.85
        )
        
        # Search memories (async)
        print("3. Searching memories...")
        results = await memory.search_async("collaborative AI", limit=5)
        
        for i, item in enumerate(results, 1):
            print(f"   {i}. {item.content}")
            print(f"      Importance: {item.importance}")
        
        # Save specialized memories
        print("4. Saving specialized memories...")
        memory.save_conversation_summary(
            "Discussed memory architecture with team",
            participants=["researcher", "architect", "developer"]
        )
        
        memory.save_learning(
            "Memory backends should be pluggable and configurable",
            topic="architecture"
        )
        
        print("\n✅ Core memory integration demo completed!")
        
    except Exception as e:
        print(f"❌ Integration demo failed: {e}")
        logger.exception("Integration demo error details:")

if __name__ == "__main__":
    print("🚀 Starting Memory Backend Demos\n")
    
    # Run demos
    asyncio.run(demo_memory_backend())
    asyncio.run(demo_core_memory_integration())
    
    print("\n🎉 All demos completed!") 