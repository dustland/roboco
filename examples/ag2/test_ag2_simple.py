#!/usr/bin/env python3
"""
Simple AG2 Iteration Test
Demonstrates basic multi-agent collaboration and iteration
"""

import asyncio
import os
from autogen import ConversableAgent, LLMConfig

async def main():
    """Main test runner"""
    
    llm_config = LLMConfig(
        api_type="openai",                      # The provider
        model="gpt-4o-mini",                    # The specific model
        api_key=os.environ["OPENAI_API_KEY"],   # Authentication
    )
    
    agent = ConversableAgent(name="Assistant", llm_config=llm_config, system_message="You are an assistant for the user")
    
    response = agent.run(
        message="Hello, how are you?",
        max_turns=10,
        user_input=True,
    )
    
    for event in response.events:
        print(event)

        if event.type == "input_request":
            event.content.respond("exit")
    
if __name__ == "__main__":
    asyncio.run(main()) 