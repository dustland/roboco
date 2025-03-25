#!/usr/bin/env python
"""
Planning Team from Configuration Example

This script demonstrates how to create a planning team from a configuration file
and use it to generate planning documents.
"""

import os
import asyncio
import yaml
from pathlib import Path
from loguru import logger

from roboco.core import Team, AgentFactory, TeamBuilder
from roboco.core.schema import TeamConfig
from roboco.teams.planning import PlanningTeam

async def main():
    """Run the planning team from configuration example."""
    
    # Create output directory
    output_dir = "workspace/plan"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create team configuration directly
    team_config = TeamConfig(
        name="ProjectPlanningTeam",
        description="Team of agents that collaborate on planning a project",
        roles=["executive", "product_manager", "software_engineer", "report_writer"],
        tool_executor="human_proxy",
        output_dir=output_dir,
        agent_configs={
            "executive": {"temperature": 0.3, "max_tokens": 2000},
            "product_manager": {"temperature": 0.7, "max_tokens": 4000},
            "software_engineer": {"temperature": 0.5, "max_tokens": 3000},
            "report_writer": {"temperature": 0.6, "max_tokens": 3500},
        }
    )
    
    logger.info(f"Created team configuration with roles: {team_config.roles}")
    
    # Create planning team with the configuration
    planning_team = PlanningTeam(
        output_dir=output_dir,
        team_config=team_config
    )
    
    # Run planning process
    vision = "Create a robot control system that can adapt to different environments and learn from experience"
    logger.info(f"Starting planning process with vision: {vision[:50]}...")
    
    result = await planning_team.create_planning_suite(vision)
    
    # Print results
    logger.info(f"Planning process completed with {result['swarm_rounds']} swarm rounds")
    logger.info(f"Created {len(result['created_files'])} planning documents:")
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