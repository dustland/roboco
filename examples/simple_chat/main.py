#!/usr/bin/env python3
import asyncio
from pathlib import Path
from agentx.core.task import TaskExecutor

async def main():
    config_path = Path(__file__).parent / "config" / "team.yaml"
    
    # Create a single TaskExecutor instance for the entire conversation
    task_executor = TaskExecutor(str(config_path))
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'q']:
            break
        
        print("Assistant: ", end="", flush=True)
        async for chunk in task_executor.execute_task(user_input, stream=True):
            if chunk.get("type") == "content":
                print(chunk.get("content", ""), end="", flush=True)
        print()

if __name__ == "__main__":
    asyncio.run(main()) 