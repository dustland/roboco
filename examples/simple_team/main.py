#!/usr/bin/env python3
"""
Simple Team Demo - Writer + Reviewer Collaboration

Shows basic multi-agent collaboration with handoffs.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from agentx import execute_task


async def main():
    """Simple team collaboration demo."""
    print("🤖 Simple Team Demo - Writer + Reviewer\n")
    
    # Configuration and prompt
    config_path = str(Path(__file__).parent / "config" / "team.yaml")
    prompt = """Write a short article about remote work benefits."""
    
    print("🎬 Starting collaboration...\n")
    
    try:
        # Execute with streaming
        async for update in execute_task(prompt, config_path, stream=True):
            update_type = update.get("type")
            
            if update_type == "content":
                print(update["content"], end="", flush=True)
                
            elif update_type == "handoff":
                from_agent = update["from_agent"]
                to_agent = update["to_agent"]
                print(f"\n\n🔄 HANDOFF: {from_agent} → {to_agent}\n")
                
            elif update_type == "routing_decision":
                if update["action"] == "complete":
                    print(f"\n\n🎉 Task completed!")
                    break
        
        print(f"\n\n✅ Collaboration finished!")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 