"""
Example demonstrating how to create and use custom Agent classes with the configuration-based team system.

This example shows:
1. Creating a custom Agent subclass with specialized behavior
2. Registering it with the AgentFactory
3. Using it in a configuration-based team
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

from roboco.core.agent import Agent
from roboco.core.agent_factory import AgentFactory
from roboco.core.team_loader import TeamLoader


class DataAnalystAgent(Agent):
    """A specialized agent for data analysis tasks.
    
    This agent demonstrates adding custom capabilities beyond what can be expressed
    in a configuration file or prompt.
    """
    
    def __init__(self, name: str, **kwargs):
        """Initialize the data analyst agent.
        
        Args:
            name: Name of the agent
            **kwargs: Additional arguments passed to the Agent constructor
        """
        # Get specialized config values
        self.data_sources = kwargs.pop("data_sources", [])
        self.analysis_methods = kwargs.pop("analysis_methods", ["descriptive", "predictive"])
        self.visualization_types = kwargs.pop("visualization_types", ["chart", "graph"])
        
        # Initialize base agent
        super().__init__(name, **kwargs)
        
        logger.info(f"Initialized DataAnalystAgent with {len(self.data_sources)} data sources")
    
    async def generate_response(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a response using specialized data analysis capabilities.
        
        This method demonstrates customizing the response generation logic.
        In a real implementation, this might connect to data sources,
        run analysis, or create visualizations.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Generated response
        """
        # Get the last message content
        last_message = messages[-1]["content"] if messages else ""
        
        # If we're asked about our capabilities, provide specialized information
        if "capabilities" in last_message.lower() or "what can you do" in last_message.lower():
            return self._describe_capabilities()
        
        # Otherwise use the LLM for general responses, but enhance with data context
        # Call the parent method to use the LLM
        base_response = await super().generate_response(messages)
        
        # Add specialized context about our data analysis capabilities
        enhanced_response = (
            f"{base_response}\n\n"
            f"Note: I have access to these data sources: {', '.join(self.data_sources)}. "
            f"I can perform {', '.join(self.analysis_methods)} analysis and create "
            f"{', '.join(self.visualization_types)} visualizations."
        )
        
        return enhanced_response
    
    def _describe_capabilities(self) -> str:
        """Describe the specialized capabilities of this agent."""
        return f"""
        I am a Data Analyst agent with the following specialized capabilities:
        
        Data Sources:
        {', '.join(self.data_sources) if self.data_sources else "No sources configured"}
        
        Analysis Methods:
        {', '.join(self.analysis_methods)}
        
        Visualization Types:
        {', '.join(self.visualization_types)}
        
        I can analyze data from these sources using the specified methods and create
        visualizations to help interpret the results.
        """


async def create_data_analyst_prompt():
    """Create a custom prompt file for the data analyst."""
    
    # Create prompts directory if it doesn't exist
    os.makedirs("config/prompts", exist_ok=True)
    
    # Define a custom prompt for the data analyst
    data_analyst_prompt = """
    # Data Analyst
    
    You are a Data Analyst responsible for processing, analyzing, and interpreting complex data sets.
    
    ## Your Responsibilities
    
    - Process and clean raw data to ensure accuracy and completeness
    - Apply statistical methods and analytical techniques to extract insights
    - Create visualizations that effectively communicate findings
    - Make recommendations based on data analysis
    
    ## Your Approach
    
    You break down complex problems into manageable components. You are methodical
    and detail-oriented, always ensuring the integrity of your analysis. You validate
    your findings through multiple approaches and are careful to highlight limitations
    and assumptions.
    
    ## Communication Style
    
    You communicate technical concepts clearly and concisely. You focus on the practical
    implications of your analysis, translating data insights into business value. You use
    visualizations to support your explanations and make them accessible to non-technical
    stakeholders.
    """
    
    # Save the prompt to a file
    with open("config/prompts/data_analyst.md", "w") as f:
        f.write(data_analyst_prompt)
    
    logger.info("Created custom prompt for Data Analyst in config/prompts/data_analyst.md")


async def create_team_config():
    """Create a team configuration that includes our custom agent."""
    # Define a team configuration that includes the data analyst
    team_config = {
        "data_team": {
            "name": "DataTeam",
            "description": "A team that works with data analysis",
            "output_dir": "workspace/data_analysis",
            "roles": [
                "product_manager",
                "data_analyst",  # Our custom role
                "report_writer"
            ],
            "workflow": [
                {"from": "product_manager", "to": "data_analyst"},
                {"from": "data_analyst", "to": "report_writer"},
                {"from": "report_writer", "to": "product_manager"}
            ],
            "tools": ["filesystem"]
        }
    }
    
    # Ensure the teams directory exists
    os.makedirs("config/teams", exist_ok=True)
    
    # Write the configuration to a file
    with open("config/teams/data_team.yaml", "w") as f:
        import yaml
        yaml.dump(team_config, f)
    
    logger.info("Created team configuration with custom data analyst role")
    return team_config


async def main():
    """Run the example."""
    # Create a custom prompt for the data analyst
    await create_data_analyst_prompt()
    
    # Create a team configuration
    await create_team_config()
    
    # Create and register our custom agent class with the updated AgentFactory
    factory = AgentFactory(prompts_dir="config/prompts")
    factory.register_agent_class(
        "data_analyst",  # Role key
        DataAnalystAgent  # Class
    )
    
    # Configure with specific settings
    data_analyst_config = {
        "data_sources": ["customer_database", "sales_reports", "market_trends"],
        "analysis_methods": ["descriptive", "predictive", "prescriptive"],
        "visualization_types": ["charts", "dashboards", "interactive_maps"],
        "temperature": 0.5  # LLM parameter
    }
    
    # Create a team loader that knows about our custom agent
    loader = TeamLoader(
        agent_factory_kwargs={
            "prompts_dir": "config/prompts",
            "register_specialized_agents": True
        }
    )
    
    # Check if our team is available
    available_teams = loader.list_available_teams()
    logger.info(f"Available teams: {available_teams}")
    
    # Create the team
    team = loader.create_team(
        "data_team",
        agent_configs={"data_analyst": data_analyst_config}
    )
    
    logger.info(f"Created team {team.name} with {len(team.agents)} agents")
    
    # Verify our custom agent is in the team
    for agent_name, agent in team.agents.items():
        logger.info(f"Agent: {agent_name}, Type: {type(agent).__name__}")
    
    # Use the team for a simple query
    query = "What can the data analyst do?"
    
    # Find the data analyst agent
    data_analyst_agent = next((agent for agent in team.agents.values() 
                          if isinstance(agent, DataAnalystAgent)), None)
    
    if data_analyst_agent:
        # For this example, just query the agent directly
        data_analyst_name = data_analyst_agent.name
        logger.info(f"Sending query to {data_analyst_name}: {query}")
        
        # Get a response that uses our specialized capabilities
        result = await team.run_swarm(
            initial_agent_name=data_analyst_name,
            query=query,
            max_rounds=3
        )
        
        # In a real application, you'd typically return the result
        # to a user interface or take some action based on it
        logger.info(f"Team orchestration completed after {result.get('rounds', 0)} rounds")
    else:
        logger.error("DataAnalystAgent not found in the team")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 