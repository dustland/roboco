#!/usr/bin/env python
"""
Multi-LLM Team Example

This example demonstrates how to create a team with different agents using different LLM providers.
For example, one agent uses OpenAI GPT-4o, another uses DeepSeek Coder, and a third uses Claude.

This allows optimizing each agent for its specific task:
- Software Engineers use DeepSeek Coder for coding tasks
- Product Managers use OpenAI GPT models for product planning
- Executives use default LLM for strategic thinking
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from roboco.core import Team, TeamBuilder, load_config, setup_logger

# Set up logging
setup_logger()

async def main():
    """Run the Multi-LLM example"""
    print("\n🤖 Starting Multi-LLM Team Example")
    print("==================================\n")
    
    # Create a team with specialized LLM providers for different roles
    team = TeamBuilder.create_team("development")
    
    print(f"\n✅ Created team: {team.name}")
    print(f"Team has {len(team.agents)} agents:")
    
    # Print out each agent and its LLM configuration
    for name, agent in team.agents.items():
        if hasattr(agent, "llm_config") and agent.llm_config:
            llm_info = f"Model: {agent.llm_config.get('model', 'unknown')}"
            if "base_url" in agent.llm_config:
                llm_info += f", Provider: {agent.llm_config['base_url']}"
        else:
            llm_info = "No LLM configuration"
        
        print(f"  - {name}: {llm_info}")
    
    # Start a group chat with a human in the loop
    print("\n🚀 Starting group chat...")
    await team.initiate_chat(
        message="Design and implement a simple weather API with FastAPI"
    )
    
    print("\n💡 Chat completed!")


if __name__ == "__main__":
    asyncio.run(main()) 