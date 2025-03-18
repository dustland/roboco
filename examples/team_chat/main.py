#!/usr/bin/env python
"""
Team Chat Example

This example demonstrates how to use the roboco Team class to create a team of agents
and initiate a chat with automatic handoffs between them.
"""

from typing import Dict, Any

from roboco.core import Team, Agent, get_logger

# Get logger for this module
logger = get_logger("team_chat")

def main():
    """
    Main function to demonstrate the team chat functionality.
    """
    logger.info("Starting team chat example")
    
    # Create a team with an empty dictionary of agents
    team = Team(name="ChatTeam", agents={})
    
    # Create agents with specific roles using create_agent
    # The Agent class will load default configs automatically from config.toml
    team.create_agent(
        agent_class=Agent,
        name="Planner",
        system_message="You are a strategic planner. Your role is to create high-level plans and strategies. When the plan is ready and research is needed, hand off to the Researcher."
    )
    
    team.create_agent(
        agent_class=Agent,
        name="Researcher",
        system_message="You are a researcher. Your role is to gather and analyze information. When research is complete and implementation is needed, hand off to the Implementer."
    )
    
    team.create_agent(
        agent_class=Agent,
        name="Implementer",
        system_message="You are an implementer. Your role is to execute plans and implement solutions. When implementation is complete and a new plan is needed, hand off to the Planner."
    )
    
    # Enable swarm orchestration
    team.enable_swarm()
    
    # Register handoffs between agents using default behavior
    team.register_handoffs()
    
    # Initiate a chat with a query
    query = "Develop a strategy for launching a new mobile app"
    logger.info(f"Initiating chat with query: {query}")
    
    # Run the chat and print the whole result directly
    result = team.initiate_chat("Planner", query)
    logger.info(f"Result: {result}")
    
    logger.info("Team chat example completed")

if __name__ == "__main__":
    main() 