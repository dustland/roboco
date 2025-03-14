"""
Embodied AI Market Research Example

This example demonstrates a scenario where a CEO asks about cutting-edge embodied AI
technologies, and a Product Manager researches and creates a comprehensive report.
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Add src directory to Python path if needed
project_root = Path(__file__).parent.parent.parent.absolute()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Load environment variables
from roboco.core import load_env_variables
load_env_variables(project_root)

# Check for API key
if not os.environ.get("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY environment variable not set")

# Import the research team from our module
from examples.market_research.team import ResearchTeam

def run_embodied_research():
    """Run the embodied AI research scenario."""
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
    if "error" in result:
        print(f"Error: {result['error']}")
        # Show more detailed error if available
        if 'traceback' in result:
            print("\nDetailed error:")
            print(result['traceback'])
    else:
        agents = result.get("agents", [])
        conversations = result.get("conversation", {})
        
        message_count = sum(len(msgs) for msgs in conversations.values())
        print(f"Conversation had {message_count} total messages across {len(agents)} agents")
        print(f"Research report has been saved to the reports/ directory")
    print("="*80)

if __name__ == "__main__":
    run_embodied_research()