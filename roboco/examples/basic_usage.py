"""Example script demonstrating basic usage of RoboCo."""

import asyncio
from loguru import logger
from roboco.agents.manager import AgentManager
from roboco.agents.base import AgentRole
from roboco.config import load_config

async def main():
    """Run a basic example of agent interaction."""
    # Load configuration
    config = load_config()
    
    # Initialize agent manager
    agent_manager = AgentManager()
    
    # Example: Human agent sends a task to the Executive Board
    task_message = """
    We need to develop a humanoid robot for a receptionist role.
    Key requirements:
    1. Natural language interaction
    2. Basic movement for greeting visitors
    3. Integration with appointment scheduling system
    """
    
    try:
        # Send message from Human to Executive Board
        logger.info("Sending task from Human to Executive Board")
        response = await agent_manager.send_message(
            AgentRole.HUMAN,
            AgentRole.EXECUTIVE_BOARD,
            task_message
        )
        
        if response:
            logger.info("Received response from Executive Board")
            print("\nExecutive Board Response:")
            print(response)
            
            # Executive Board delegates to Product Manager
            logger.info("Executive Board delegating to Product Manager")
            pm_response = await agent_manager.send_message(
                AgentRole.EXECUTIVE_BOARD,
                AgentRole.PRODUCT_MANAGER,
                response
            )
            
            if pm_response:
                logger.info("Received response from Product Manager")
                print("\nProduct Manager Response:")
                print(pm_response)
            else:
                logger.error("No response from Product Manager")
        else:
            logger.error("No response from Executive Board")
            
    except Exception as e:
        logger.error(f"Error during example run: {str(e)}")

if __name__ == "__main__":
    # Configure logging
    logger.add(
        "logs/example.log",
        rotation="100 MB",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    # Run the example
    asyncio.run(main()) 