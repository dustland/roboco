#!/usr/bin/env python
"""
Planning Team Example

This script demonstrates how to use the PlanningTeam class with markdown-based prompts.
"""

import os
import asyncio
from loguru import logger

from roboco.teams.planning import PlanningTeam

async def main():
    """Run the planning team example."""
    
    # Create output directory
    output_dir = "workspace/plan"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a planning team with markdown-based prompts
    planning_team = PlanningTeam(
        roles_config_path="config/roles.yaml",
        prompts_dir="config/prompts",
        output_dir=output_dir,
        use_specialized_agents=True
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
    if "implementation_plan.md" in result['created_files']:
        feedback = """
        The implementation plan needs more detail in the following areas:
        1. Add specific milestones with dates
        2. Include more specific success metrics
        3. Add a section on team roles and responsibilities
        """
        
        logger.info("Improving implementation plan based on feedback...")
        improve_result = await planning_team.improve_planning_document("implementation_plan.md", feedback)
        
        if improve_result['success']:
            logger.info("Implementation plan successfully improved")
        else:
            logger.error(f"Failed to improve implementation plan: {improve_result.get('error', 'Unknown error')}")
    
if __name__ == "__main__":
    asyncio.run(main()) 