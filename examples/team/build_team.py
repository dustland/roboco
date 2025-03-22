#!/usr/bin/env python
"""
Planning Team Example

This script demonstrates how to use the PlanningTeam class with a simple TeamConfig.
"""

import os
import asyncio
from loguru import logger
from pathlib import Path

import sys
from roboco.core import TeamBuilder
from roboco.core.schema import TeamConfig
from roboco.teams.planning import PlanningTeam

async def main():
    """Run the planning team example."""
    
    # Create output directory
    output_dir = "workspace/plan"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a custom team configuration
    team_config = TeamConfig(
        name="CustomPlanningTeam",
        description="Custom planning team with specialized configuration",
        roles=["executive", "product_manager", "software_engineer", "report_writer"],
        tool_executor="human_proxy",
        output_dir=output_dir
    )
    
    # Create a planning team with the custom configuration
    planning_team = PlanningTeam(
        output_dir=output_dir,
        team_config=team_config
    )
    
    # Run the team to create a planning suite
    vision = "Create a robot control system that can adapt to different environments and learn from experience"
    logger.info(f"Starting planning process with vision: {vision[:50]}...")
    
    result = await planning_team.create_planning_suite(vision)
    
    # Print results
    logger.info(f"Planning process completed with {result['swarm_rounds']} swarm rounds")
    logger.info(f"Created {len(result['created_files'])} planning documents:")
    for filename in result['created_files']:
        logger.info(f"  - {filename}")
    
    # Example of improving a document
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