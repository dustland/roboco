#!/usr/bin/env python
"""
Role-Based LLM Configuration Example

This script demonstrates how to use the role-based LLM configuration approach
with teams in Roboco. Each role has its own LLM configuration defined in roles.yaml,
and the team builder uses this configuration when creating agents.
"""

import os
import asyncio
import yaml
from loguru import logger

from roboco.core import TeamBuilder, AgentFactory
from roboco.teams.planning import PlanningTeam

async def main():
    """Run the role-based LLM configuration example."""
    
    # Create output directory
    output_dir = "workspace/role_llm_example"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the TeamBuilder singleton
    builder = TeamBuilder.get_instance()
    
    # Display available roles and their LLM configurations
    agent_factory = AgentFactory.get_instance()
    roles_config = agent_factory.roles_config
    
    logger.info("Available roles with LLM configurations:")
    for role_key, role_config in roles_config.get("roles", {}).items():
        llm_config = role_config.get("llm", {})
        if llm_config:
            provider = llm_config.get("provider", "default")
            model = llm_config.get("model", "default")
            temp = llm_config.get("temperature", "default")
            logger.info(f"  - {role_key}: provider={provider}, model={model}, temperature={temp}")
        else:
            logger.info(f"  - {role_key}: No LLM configuration")
    
    # Create a planning team that uses roles with different LLM configurations
    # Each role will use its LLM configuration from roles.yaml
    planning_team = PlanningTeam(
        name="RoleLLMPlanningTeam",
        output_dir=output_dir
    )
    
    # This team was created with roles that use different LLM configurations:
    # - executive: Uses default LLM with lower temperature (0.3)
    # - product_manager: Uses OpenAI with higher temperature (0.7) 
    # - software_engineer: Uses DeepSeek coder model
    # - report_writer: Uses default LLM with medium temperature (0.6)
    
    # Run a simple planning task
    logger.info("Running planning task with role-based LLM configurations...")
    result = await planning_team.create_planning_suite(
        vision="Create a robot that can perform basic household tasks"
    )
    
    # Display results
    logger.info(f"Planning completed with {result.get('swarm_rounds')} rounds")
    logger.info(f"Created {len(result.get('created_files', []))} documents:")
    for file in result.get('created_files', []):
        logger.info(f"  - {file}")
    
    # Print location of output files
    logger.info(f"Output files can be found in: {output_dir}")
    
if __name__ == "__main__":
    asyncio.run(main()) 