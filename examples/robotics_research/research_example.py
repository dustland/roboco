"""
Robotics Research Example

This script demonstrates how to use the RoboticsScientistAgent
to research cutting-edge technologies for embodied AI.
"""

import asyncio
import argparse
import json
from pathlib import Path

from roboco.core.config import load_config
from roboco.core.logger import get_logger
from roboco.agents.robotics_scientist import RoboticsScientistAgent, ResearchItem

logger = get_logger("research_example")

# Research domains for robotics
RESEARCH_DOMAINS = [
    "legged robot locomotion",
    "robotic manipulation and grasping",
    "humanoid robot control",
    "embodied AI for robotics",
    "robotic perception and sensing",
    "human-robot interaction",
]

async def research_specific_topic(topic: str, output_dir: str):
    """Research a specific topic in robotics and save results.
    
    Args:
        topic: Topic to research
        output_dir: Directory to save research results
    """
    config = load_config()
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting research on: {topic}")
    
    # Initialize the scientist agent
    scientist = RoboticsScientistAgent(llm_config=config.llm)
    await scientist.initialize()
    
    try:
        # Run the full research pipeline
        results = await scientist.run_research_pipeline(topic)
        
        # Save research report
        report_data = results["report"].dict()
        report_path = Path(output_dir) / f"{topic.replace(' ', '_')}_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Research report saved to: {report_path}")
        
        # Print summary
        logger.info(f"Research overview: {results['report'].overview}")
        
        # List key recommendations by category
        categories = results["categories"]
        for category, items in categories.items():
            if items:
                logger.info(f"\n--- {category.upper()} TECHNOLOGIES ({len(items)}) ---")
                for item in items[:3]:  # Show top 3 for each category
                    logger.info(f"• {item.title}: {item.summary[:100]}...")
    
    finally:
        # Clean up resources
        await scientist.cleanup()

async def comprehensive_robotics_research(output_dir: str):
    """Perform comprehensive research across all domains of robotics.
    
    Args:
        output_dir: Directory to save research results
    """
    for domain in RESEARCH_DOMAINS:
        await research_specific_topic(domain, output_dir)

async def compare_technologies(tech1: str, tech2: str, output_dir: str):
    """Compare two robotics technologies.
    
    Args:
        tech1: First technology to compare
        tech2: Second technology to compare
        output_dir: Directory to save comparison results
    """
    config = load_config()
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Comparing technologies: {tech1} vs {tech2}")
    
    # Initialize the scientist agent
    scientist = RoboticsScientistAgent(llm_config=config.llm)
    await scientist.initialize()
    
    try:
        # Research both technologies
        tech1_result = await scientist.create_research_report(tech1)
        tech2_result = await scientist.create_research_report(tech2)
        
        # Compare research findings
        comparison_task = f"Compare the technologies {tech1} and {tech2} for robotics applications. Analyze their strengths, weaknesses, and best use cases."
        comparison_result = await scientist.browser_tool.browser_use(comparison_task)
        
        # Save comparison results
        comparison_path = Path(output_dir) / f"comparison_{tech1.replace(' ', '_')}_vs_{tech2.replace(' ', '_')}.txt"
        
        with open(comparison_path, 'w') as f:
            f.write(f"COMPARISON: {tech1} vs {tech2}\n\n")
            f.write(f"{comparison_result.final_result}\n\n")
            f.write("EXTRACTED CONTENT:\n")
            for content in comparison_result.extracted_content:
                f.write(f"{content}\n\n")
        
        logger.info(f"Comparison saved to: {comparison_path}")
        logger.info(f"Summary: {comparison_result.final_result[:200]}...")
    
    finally:
        # Clean up resources
        await scientist.cleanup()

def setup_argparse():
    """Set up command-line argument parsing."""
    parser = argparse.ArgumentParser(description="Robotics Research Tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Research topic command
    topic_parser = subparsers.add_parser("topic", help="Research a specific topic")
    topic_parser.add_argument("topic", help="Topic to research")
    topic_parser.add_argument("--output-dir", default="research_results", help="Output directory for results")
    
    # Comprehensive research command
    comprehensive_parser = subparsers.add_parser("comprehensive", help="Comprehensive robotics research")
    comprehensive_parser.add_argument("--output-dir", default="research_results", help="Output directory for results")
    
    # Compare technologies command
    compare_parser = subparsers.add_parser("compare", help="Compare two technologies")
    compare_parser.add_argument("tech1", help="First technology to compare")
    compare_parser.add_argument("tech2", help="Second technology to compare")
    compare_parser.add_argument("--output-dir", default="research_results", help="Output directory for results")
    
    return parser

async def main():
    """Main entry point for the robotics research example."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command == "topic":
        await research_specific_topic(args.topic, args.output_dir)
    elif args.command == "comprehensive":
        await comprehensive_robotics_research(args.output_dir)
    elif args.command == "compare":
        await compare_technologies(args.tech1, args.tech2, args.output_dir)
    else:
        # Default to researching a single topic if no command is provided
        await research_specific_topic("humanoid robot embodied AI", "research_results")

if __name__ == "__main__":
    asyncio.run(main()) 