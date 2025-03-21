#!/usr/bin/env python
"""
Planning Team from Configuration Example

This script demonstrates how to create a planning team from a configuration file
and use it to generate planning documents.
"""

import os
import asyncio
from loguru import logger

from roboco.core.team_loader import TeamLoader
from roboco.teams.planning import PlanningTeam

async def main():
    """Run the planning team from configuration example."""
    
    # Create output directory
    output_dir = "workspace/plan"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize team loader
    loader = TeamLoader(
        teams_config_path="config/teams.yaml",
        teams_dir="config/teams",
        agent_factory_kwargs={
            "roles_config_path": "config/roles.yaml",
            "prompts_dir": "config/prompts"
        }
    )
    
    # Create planning team from configuration
    planning_team = loader.create_team(
        "planning",
        output_dir=output_dir,
        name="ProjectPlanningTeam"
    )
    
    # Run planning process
    vision = "Create a robot control system that can adapt to different environments and learn from experience"
    logger.info(f"Starting planning process with vision: {vision[:50]}...")
    
    result = await planning_team.create_planning_suite(vision)
    
    # Print results
    logger.info(f"Planning process completed with {result['swarm_rounds']} swarm rounds")
    logger.info(f"Created {len(result['created_files'])} planning documents in {output_dir}:")
    for filename in result['created_files']:
        logger.info(f"  - {filename}")
    
    # Optionally improve a document
    if "vision.md" in result['created_files']:
        feedback = """
        The vision document needs to be more explicit about:
        1. How success will be measured
        2. Key constraints and assumptions
        3. Target users and their needs
        """
        
        logger.info("Improving vision document based on feedback...")
        improve_result = await planning_team.improve_planning_document("vision.md", feedback)
        
        if improve_result['success']:
            logger.info("Vision document successfully improved")
        else:
            logger.error(f"Failed to improve vision document: {improve_result.get('error', 'Unknown error')}")
    
if __name__ == "__main__":
    asyncio.run(main()) 