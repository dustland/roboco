#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agentx import start_task

async def main():
    print("🤖 AgentX Chat (type 'quit' to exit)\n")
    
    # Start task with team configuration
    config_path = str(Path(__file__).parent / "team.yaml")
    task = start_task("Hi! Let's have a chat.", config_path)
    
    user_input = None

    while not task.is_complete:
        print("🤖 Assistant: ", end="", flush=True)
        
        async for chunk in task.step(user_input=user_input, stream=True):
            if chunk.get("type") == "content":
                print(chunk.get("content", ""), end="", flush=True)
        
        print()  # New line after assistant response
        
        if not task.is_complete:
            user_input = input("👤 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break

if __name__ == "__main__":
    asyncio.run(main()) 