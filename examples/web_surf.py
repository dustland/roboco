#!/usr/bin/env python3
"""Simple example demonstrating web research capabilities."""

import logging
from roboco.agents import ProductManager, HumanProxy
from roboco.core.tool_factory import ToolFactory

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run the example."""
    try:
        logger.info("Creating agents...")
        # Define termination message
        termination_msg = "TERMINATE"
        
        # Create the executor agent
        executor = HumanProxy(
            name="ToolExecutor",
            human_input_mode="NEVER",  # Disable human input for automation
            terminate_msg=termination_msg
        )
        
        # Create the ProductManager agent
        researcher = ProductManager()
        
        # Create the user agent
        user = HumanProxy(
            name="User",
            human_input_mode="NEVER",  # Disable human input for automation
            terminate_msg=termination_msg
        )

        logger.info("Registering tools...")
        # Register the BrowserTool with the agents
        ToolFactory.register_tool(
            caller_agent=researcher,
            executor_agent=executor,
            tool_name="BrowserTool"
        )
        
        logger.info("Starting research conversation...")
        # Use the initiate_chat method with max_turns to ensure it completes
        user.initiate_chat(
            researcher,
            message="What are the latest developments in humanoid robotics? Please provide a brief summary.",
            max_turns=5  # Limit to 5 turns to ensure it completes
        )
        
        logger.info("Research conversation completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()