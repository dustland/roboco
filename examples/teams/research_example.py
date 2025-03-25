#!/usr/bin/env python
"""
Research Team Example

This example demonstrates how to use the ResearchTeam to conduct research tasks.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from loguru import logger

# Add project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.teams.research import ResearchTeam

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

def print_section(title):
    """Print a section heading."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

async def run_simple_research(workspace_dir, topic):
    """Run a simple research task."""
    print_section(f"Running Basic Research: {topic}")
    
    # Create the research team
    research_team = ResearchTeam(workspace_dir=workspace_dir)
    
    # Run the research chat
    print(f"Starting research on: {topic}")
    results = await research_team.run_chat(topic)
    
    # Print results
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print_section("Research Results")
    print(results["response"])
    
    print(f"\nResults saved to: {results.get('results_path', 'N/A')}")

async def run_comprehensive_research(workspace_dir, topic, output_file):
    """Run comprehensive research with a specific output file."""
    print_section(f"Running Comprehensive Research: {topic}")
    
    # Create the research team
    research_team = ResearchTeam(workspace_dir=workspace_dir)
    
    # Run the comprehensive research
    print(f"Starting comprehensive research on: {topic}")
    results = await research_team.conduct_research(topic, output_file)
    
    # Print results
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print_section("Research Complete")
    print(f"Research report saved to: {results.get('output_file', 'N/A')}")
    
    # Display the start of the report
    if "output_file" in results:
        with open(results["output_file"], "r") as f:
            content = f.read()
            # Print first 500 characters as a preview
            print("\nReport Preview:")
            print("-" * 40)
            print(content[:500] + ("..." if len(content) > 500 else ""))
            print("-" * 40)

async def main():
    """Run the research team example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run research tasks with the ResearchTeam")
    parser.add_argument("--workspace", "-w", type=str, default="workspace/research", help="Workspace directory")
    parser.add_argument("--topic", "-t", type=str, required=True, help="Research topic")
    parser.add_argument("--output", "-o", type=str, help="Output file path (relative to workspace)")
    parser.add_argument("--comprehensive", "-c", action="store_true", help="Run comprehensive research")
    
    args = parser.parse_args()
    
    # Create workspace directory if it doesn't exist
    os.makedirs(args.workspace, exist_ok=True)
    
    if args.comprehensive:
        output_file = args.output or "research_report.md"
        await run_comprehensive_research(args.workspace, args.topic, output_file)
    else:
        await run_simple_research(args.workspace, args.topic)
    
    print_section("Research Task Completed")

if __name__ == "__main__":
    asyncio.run(main()) 