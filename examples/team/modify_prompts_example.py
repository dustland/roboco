#!/usr/bin/env python
"""
Modify Prompts Example

This script demonstrates how to modify existing prompts or create new prompt files
for agent roles before team creation.
"""

import os
import asyncio
from loguru import logger

from roboco.core.team_builder import TeamBuilder
from roboco.teams.planning import PlanningTeam

async def create_or_update_prompt(role_key, content, prompts_dir="config/prompts"):
    """Create or update a prompt file for a specific role.
    
    Args:
        role_key: The key/name of the role (e.g., "executive")
        content: The markdown content for the prompt
        prompts_dir: Directory where prompt files are stored
    """
    # Ensure prompts directory exists
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Create or update the prompt file
    file_path = os.path.join(prompts_dir, f"{role_key}.md")
    with open(file_path, "w") as f:
        f.write(content)
    
    logger.info(f"Created/updated prompt for {role_key} at {file_path}")
    
    return file_path

async def main():
    """Run the modify prompts example."""
    
    # Create output directory for planning documents
    output_dir = "workspace/modified_plan"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a custom prompts directory for this example
    custom_prompts_dir = "workspace/modified_prompts"
    os.makedirs(custom_prompts_dir, exist_ok=True)
    
    # 1. Copy existing prompts to our custom directory
    from shutil import copyfile
    for role in ["executive", "product_manager", "software_engineer", "report_writer", "human_proxy"]:
        source_path = f"config/prompts/{role}.md"
        dest_path = f"{custom_prompts_dir}/{role}.md"
        try:
            copyfile(source_path, dest_path)
            logger.info(f"Copied prompt: {source_path} -> {dest_path}")
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {source_path}")
    
    # 2. Modify the executive prompt to add a focus on sustainability
    executive_prompt = """
    # Executive
    
    You are the Executive responsible for overall project vision, strategy, and final approval.
    
    ## Your Responsibilities
    
    - Establish the strategic direction and vision
    - Evaluate proposals and plans for alignment with business goals
    - Make final decisions on resource allocation and priorities
    - Ensure accountability for project outcomes
    - **Champion sustainability initiatives and environmental responsibility**
    
    ## Your Approach
    
    You take a holistic view of the organization's needs and market position.
    You balance short-term goals with long-term strategy.
    You consider financial, technical, human, and **environmental** factors in decision-making.
    
    ## Communication Style
    
    You communicate with clarity and authority.
    You focus on outcomes rather than implementation details.
    You ask probing questions to test assumptions and reveal potential issues.
    You emphasize the importance of measurable results and **sustainable practices**.
    """
    
    await create_or_update_prompt("executive", executive_prompt, custom_prompts_dir)
    
    # 3. Create a new prompt for a sustainability expert
    sustainability_expert_prompt = """
    # Sustainability Expert
    
    You are a Sustainability Expert responsible for ensuring projects meet environmental 
    and social responsibility standards.
    
    ## Your Responsibilities
    
    - Evaluate plans for environmental impact and sustainability
    - Recommend eco-friendly approaches and technologies
    - Identify opportunities to reduce carbon footprint and resource usage
    - Ensure compliance with environmental regulations and best practices
    
    ## Your Approach
    
    You take a systems thinking approach to sustainability challenges.
    You balance immediate business needs with long-term environmental impact.
    You focus on practical, measurable improvements rather than theoretical ideals.
    
    ## Communication Style
    
    You are data-driven and evidence-based in your recommendations.
    You translate complex environmental concepts into actionable business terms.
    You highlight both risks and opportunities related to sustainability.
    You are persuasive but realistic about what can be achieved.
    """
    
    await create_or_update_prompt("sustainability_expert", sustainability_expert_prompt, custom_prompts_dir)
    
    # 4. Create a team with the modified prompts using TeamBuilder
    builder = TeamBuilder(
        prompts_dir=custom_prompts_dir,
        roles_config_path="config/roles.yaml",
        use_specialized_agents=True
    )
    
    # Add the sustainability expert to the standard planning team
    builder.with_roles(
        "executive",
        "product_manager", 
        "software_engineer",
        "sustainability_expert",  # New role!
        "report_writer"
    )
    
    # Set up the tool executor
    builder.with_tool_executor("human_proxy")
    
    # Define a modified workflow that includes the sustainability expert
    builder.with_circular_workflow(
        "product_manager",
        "software_engineer",
        "sustainability_expert",  # Include in the workflow
        "report_writer",
        "executive"
    )
    
    # Build the team
    team = builder.build(name="SustainablePlanningTeam")
    
    logger.info(f"Created team with modified prompts: {team.name}")
    logger.info(f"Agents: {', '.join(team.agents.keys())}")
    
    # Run the team with a sustainability-focused vision
    vision = """
    Create a robot control system that minimizes energy consumption and environmental impact
    while adapting to different environments and learning from experience.
    """
    
    start_agent = team.get_agent("Product Manager")
    
    if start_agent:
        # Run the planning request
        logger.info(f"Starting planning process with sustainability focus...")
        
        result = team.run_swarm(
            initial_agent_name=start_agent.name,
            query=f"""
            Create a complete planning document suite in {output_dir} with the following:
            
            1. vision.md - A detailed vision with objectives and success criteria
            2. technical_strategy.md - Technical approach with sustainability considerations
            3. implementation_plan.md - Phased implementation plan with environmental metrics
            4. sustainability_assessment.md - Assessment of environmental impact and improvements
            
            Start with this vision statement:
            
            {vision}
            
            Each document should incorporate sustainability principles and environmental considerations.
            """
        )
        
        logger.info(f"Planning process completed with {result.get('rounds', 0)} rounds")
        
        # List the created documents
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('.md')]
            if files:
                logger.info(f"Created documents in {output_dir}: {', '.join(files)}")
            else:
                logger.warning(f"No documents created in {output_dir}")
    else:
        logger.error("Product Manager agent not found")

if __name__ == "__main__":
    asyncio.run(main()) 