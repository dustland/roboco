#!/usr/bin/env python
"""
Custom Prompts Example

This script demonstrates how to use custom prompts in a different directory
for agent creation and team building.
"""

import os
import asyncio
from loguru import logger

from roboco.teams.planning import PlanningTeam
from roboco.core import AgentFactory, TeamBuilder

async def main():
    """Run the custom prompts example."""
    
    # Create a custom prompts directory
    custom_prompts_dir = "workspace/custom_prompts"
    os.makedirs(custom_prompts_dir, exist_ok=True)
    
    # Create a custom prompt for the product manager
    product_manager_prompt = """
    # Product Manager
    
    You are the Product Manager responsible for defining product requirements and vision.
    
    ## Your Responsibilities
    
    - Understand customer needs and market requirements
    - Define product features and prioritize the roadmap
    - Communicate with stakeholders to ensure alignment
    - Work with the engineering team to ensure feasible implementation
    
    ## Your Approach
    
    You focus on creating detailed, actionable specifications that are clear and complete.
    You prioritize features based on customer value and business impact.
    You ensure all requirements are testable and measurable.
    
    ## Communication Style
    
    You are concise, specific, and use examples to illustrate your points.
    You ask clarifying questions when requirements are ambiguous.
    You stay focused on user value and business outcomes.
    """
    
    # Save the custom prompt
    with open(os.path.join(custom_prompts_dir, "product_manager.md"), "w") as f:
        f.write(product_manager_prompt)
    
    logger.info(f"Created custom prompt for Product Manager in {custom_prompts_dir}")
    
    # Create output directory for planning documents
    output_dir = "workspace/custom_plan"
    os.makedirs(output_dir, exist_ok=True)
    
    # Method 1: Direct initialization with custom prompts directory
    planning_team = PlanningTeam(
        name="CustomPromptsTeam",
        roles_config_path="config/roles.yaml",
        prompts_dir=custom_prompts_dir
    )
    
    logger.info(f"Created planning team using custom prompts directory")
    
    # Method 2: Using TeamBuilder with custom prompts directory
    builder = TeamBuilder(
        use_specialized_agents=True,
        prompts_dir=custom_prompts_dir,
        roles_config_path="config/roles.yaml"
    )
    
    # Define the roles in our team
    builder.with_roles(
        "executive",
        "product_manager", 
        "software_engineer",
        "report_writer"
    )
    
    # Set up the tool executor
    builder.with_tool_executor("human_proxy")
    
    # Define a circular workflow
    builder.with_circular_workflow(
        "product_manager",
        "software_engineer", 
        "report_writer",
        "executive"
    )
    
    # Build the team
    custom_team = builder.build(name="CustomBuiltTeam")
    
    logger.info(f"Created team '{custom_team.name}' using TeamBuilder with custom prompts")
    
    # Method 3: Using AgentFactory directly
    agent_factory = AgentFactory(
        roles_config_path="config/roles.yaml",
        prompts_dir=custom_prompts_dir
    )
    
    # Create a product manager agent directly
    product_manager = agent_factory.create_agent("product_manager")
    
    logger.info(f"Created {product_manager.name} agent directly with custom prompt")
    
    # Run a test plan with the custom-prompted team
    vision = "Create a robot control system that can adapt to different environments and learn from experience"
    logger.info(f"Starting planning process with team using custom prompts...")
    
    # Simple example to demonstrate the custom prompt is being used
    starter = planning_team.get_agent("Product Manager")
    if starter:
        result = planning_team.run_swarm(
            starter,
            f"Explain your role as a Product Manager in developing: {vision}"
        )
        logger.info(f"Planning team process completed with custom prompts")
    
if __name__ == "__main__":
    asyncio.run(main()) 