"""
Embodied AI Market Research Example

This example demonstrates a scenario where a CEO asks about cutting-edge embodied AI
technologies, and a research team collaborates using AG2's Swarm orchestration to create
a comprehensive report.
"""

import os
import sys
import json
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
    """Run the embodied AI research scenario using AG2's Swarm orchestration."""
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
    
    print("\n" + "="*80)
    print("STARTING RESEARCH WITH AG2 SWARM ORCHESTRATION")
    print("="*80)
    print(f"Query: {ceo_query.strip()}")
    print("-"*80)
    print("The research team is collaborating using AG2's Swarm pattern:")
    print("- ProductManager: Coordinates research and defines objectives")
    print("- Researcher: Analyzes data and extracts insights")
    print("- ReportWriter: Creates structured, comprehensive reports")
    print("- ToolUser: Executes web searches and file operations")
    print("-"*80)
    
    # Run the scenario
    result = team.run_scenario(ceo_query)
    
    # Print a summary
    print("\n" + "="*80)
    print("RESEARCH SCENARIO COMPLETED")
    print("="*80)
    
    # Show the research flow
    if "context" in result:
        context = result["context"]
        print("\nRESEARCH PROCESS SUMMARY:")
        print("-"*80)
        
        # Show key metrics
        if "search_results" in context and isinstance(context["search_results"], list):
            print(f"- Search queries executed: {len(context['search_results'])}")
        
        if "analysis" in context and isinstance(context["analysis"], list):
            print(f"- Analysis steps performed: {len(context['analysis'])}")
        
        # Show the last agent that completed the work
        if "last_agent" in result:
            print(f"- Final agent: {result['last_agent']}")
    
    # Show the report path
    if "report_path" in result:
        print("\nRESEARCH REPORT:")
        print("-"*80)
        print(f"Report saved to: {result['report_path']}")
        
        # Display the first few lines of the report
        try:
            with open(result["report_path"], "r") as f:
                report_preview = "\n".join(f.readlines()[:10])
                print("\nReport Preview:")
                print("-"*40)
                print(report_preview)
                print("...")
                print("-"*40)
                print("Open the full report to see complete research findings.")
        except Exception as e:
            print(f"Error previewing report: {e}")
    
    return result

def run_simple_research(query):
    """Run a simple research query."""
    team = ResearchTeam()
    print(f"\nResearching: {query}")
    result = team.run_scenario(query)
    
    if "report_path" in result:
        print(f"Report saved to: {result['report_path']}")
    
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run market research using AG2's Swarm orchestration")
    parser.add_argument("--query", type=str, help="Custom research query")
    args = parser.parse_args()
    
    if args.query:
        run_simple_research(args.query)
    else:
        run_embodied_research()