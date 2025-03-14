"""
Embodied AI Market Research Example

This example demonstrates a scenario where a CEO asks about cutting-edge embodied AI
technologies, and a Product Manager researches and creates a comprehensive report.

The scenario uses AG2 to create a team of agents with specialized roles and tools.
"""

import os
import sys
import time
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Load environment variables from .env file
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info(f"Loaded environment variables from {env_path}")
else:
    logger.warning("No .env file found, using existing environment variables")

# Set up OpenAI API key for testing (in production, use environment variables)
if not os.environ.get("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY environment variable not set")

# Import the research team from our module
from team import ResearchTeam

def run_embodied_research():
    """Run the embodied AI research scenario using the AG2 framework."""
    # Create the research team with the config.toml in the same directory
    team = ResearchTeam()
    
    # Define the CEO's query
    ceo_query = """
    I've been hearing a lot about cutting-edge embodied AI applications lately. 
    I want to understand the current state of the technology, who the key players are,
    and what opportunities exist for our company to develop innovative products in this space.
    
    Can you research this topic and provide me with a comprehensive report on cutting-edge
    embodied AI applications, including technical approaches, market opportunities, and
    strategic recommendations?
    """
    
    # Run the scenario
    result = team.run_scenario(ceo_query)
    
    # Print a summary
    print("\n" + "="*80)
    print("RESEARCH SCENARIO COMPLETED")
    print("="*80)
    print(f"Conversation had {len(result['conversation'])} turns")
    print(f"Research report has been saved to the reports/ directory")
    print("="*80)

if __name__ == "__main__":
    run_embodied_research()