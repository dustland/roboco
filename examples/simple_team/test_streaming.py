#!/usr/bin/env python3
"""
Quick test script to verify streaming functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import agentx
from agentx.core.team import Team
from agentx.core.orchestrator import Orchestrator


async def test_streaming():
    """Test basic streaming functionality."""
    print("🧪 Testing AgentX Streaming...")
    
    # Initialize framework
    agentx.initialize()
    
    # Load team
    config_path = Path(__file__).parent / "config" / "team.yaml"
    team = Team.from_config_file(str(config_path))
    
    # Create orchestrator
    orchestrator = Orchestrator(team)
    
    # Simple test prompt
    prompt = "Write a short paragraph about the benefits of remote work."
    
    # Start task
    task_id = await orchestrator.start_task(prompt)
    print(f"✅ Task started: {task_id}")
    
    # Test streaming
    chunk_count = 0
    async for update in orchestrator.execute_task_streaming(task_id):
        update_type = update.get("type")
        
        if update_type == "agent_start":
            print(f"\n🤖 {update['agent_name']} starting...")
            
        elif update_type == "response_chunk":
            chunk_count += 1
            print(".", end="", flush=True)
            
        elif update_type == "agent_complete":
            print(f"\n✅ {update['agent_name']} completed")
            
        elif update_type == "task_complete":
            print(f"\n🎉 Task completed!")
            break
    
    print(f"\n📊 Received {chunk_count} streaming chunks")
    print("✅ Streaming test passed!")


if __name__ == "__main__":
    asyncio.run(test_streaming()) 