#!/usr/bin/env python
"""
Project Agent Example

This script demonstrates how to use the ProjectAgent to create and manage projects.
It creates a simple team with a human proxy and project agent, then shows how to:

1. Create a new project from a natural language query
2. Explore the generated project structure 
3. View the auto-generated tasks and sprints
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add project root to Python path (if running directly)
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from roboco.core.agent import Agent, HumanProxy
from roboco.agents.project_builder import ProjectAgent
from roboco.core.team import Team
from roboco.core.config import load_config, get_llm_config
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

def print_section(title):
    """Print a section heading."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2, default=str))

class ProjectTeam(Team):
    """A simple team consisting of a human proxy and a project agent."""
    
    def __init__(self, **kwargs):
        """Initialize the team."""
        super().__init__(name="Project Team", **kwargs)
        
        # Initialize agents
        self._setup_agents()
        
        # Set up handoffs between agents
        self._register_handoffs()
        
    def _setup_agents(self):
        """Set up the agents for the team."""
        # Load config for LLM settings
        config = load_config()
        llm_config = get_llm_config(config)
        
        # Create the human proxy agent
        human = HumanProxy(
            name="Human",
            is_termination_msg=lambda x: "TERMINATE" in (x.get("content", "") or ""),
            human_input_mode="TERMINATE",
            code_execution_config={"work_dir": "workspace", "use_docker": False}
        )
        
        # Create the project agent
        project_agent = ProjectAgent(
            name="ProjectManager",
            llm_config=llm_config
        )
        
        # Add the agents to the team
        self.add_agent("human", human)
        self.add_agent("project_agent", project_agent)
    
    def _register_handoffs(self):
        """Register handoffs between agents."""
        # Import autogen's handoff registration
        from autogen import register_hand_off, AfterWork
        
        # Register handoffs for circular conversation flow
        human = self.get_agent("human")
        project_agent = self.get_agent("project_agent")
        
        # Set up handoffs: human -> project_agent -> human
        register_hand_off(
            agent=human,
            hand_to=AfterWork(agent=project_agent)
        )
        
        register_hand_off(
            agent=project_agent,
            hand_to=AfterWork(agent=human)
        )
        
        logger.info("Registered handoffs for ProjectTeam")
    
    async def run_example(self, query):
        """Run the example with a given query."""
        # Get the agents
        human = self.get_agent("human")
        project_agent = self.get_agent("project_agent")
        
        # Start chat with the project agent
        await human.initiate_chat(
            project_agent,
            message=f"""
            I'd like to create a new project based on the following idea:
            
            {query}
            
            Please analyze this request and create an appropriate project structure with:
            - A suitable name and description
            - The right teams assigned based on the nature of the project
            - An initial sprint with relevant tasks
            - A well-organized directory structure
            
            After creating the project, explain the structure you've created and why
            it suits my needs.
            """,
        )

async def main():
    """Run the Project Agent example."""
    print_section("Project Agent Example")
    
    # Create sample queries
    sample_queries = [
        "Research the impact of artificial intelligence on healthcare delivery",
        "Develop a mobile app for tracking personal carbon footprint",
        "Design a user interface for a smart home automation system",
    ]
    
    # Let user select a query or enter a custom one
    print("Select a query to create a project:")
    for i, query in enumerate(sample_queries):
        print(f"{i+1}. {query}")
    print(f"{len(sample_queries)+1}. Enter custom query")
    
    choice = input("\nEnter your choice (1-4): ")
    
    try:
        choice = int(choice)
        if 1 <= choice <= len(sample_queries):
            query = sample_queries[choice-1]
        else:
            query = input("Enter your custom query: ")
    except ValueError:
        query = input("Enter your custom query: ")
    
    # Create the project team
    team = ProjectTeam()
    
    # Run the example
    print_section(f"Creating Project from: '{query}'")
    await team.run_example(query)
    
    print_section("Example Complete")
    print("The project has been created in the workspace directory.")
    print("You can view the project structure and files there.")

if __name__ == "__main__":
    asyncio.run(main()) 