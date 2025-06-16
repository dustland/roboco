#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agentx import start_task

async def main():
    print("🤖 AgentX Chat (type 'quit' to exit)\n")
    task = start_task("hi")
    user_input = None

    while not task.is_complete:
        print("🤖 Assistant: ", end="", flush=True)
        
        async for chunk in task.step(user_input=user_input, stream=True):
            if chunk.get("type") == "content":
                print(chunk.get("content", ""), end="", flush=True)
        
        if not task.is_complete:
            user_input = input("👤 You: ").strip()

if __name__ == "__main__":
    asyncio.run(main()) 