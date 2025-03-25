"""Example demonstrating a custom Agent class in the Roboco framework."""

import asyncio
from typing import List, Dict, Any
from loguru import logger

from roboco.core import Agent, AgentFactory, TeamBuilder


class DataAnalystAgent(Agent):
    """A specialized agent for data analysis tasks."""
    
    def __init__(self, name: str, **kwargs):
        # Extract specialized config values
        self.data_sources = kwargs.pop("data_sources", [])
        self.analysis_methods = kwargs.pop("analysis_methods", ["descriptive"])
        self.visualization_types = kwargs.pop("visualization_types", ["chart"])
        
        # Initialize base agent
        super().__init__(name, **kwargs)
    
    async def generate(self, messages: List[Dict[str, Any]]) -> str:
        """Generate response with data analysis capabilities."""
        # Check if asking about capabilities
        last_message = messages[-1]["content"] if messages else ""
        if "capabilities" in last_message.lower() or "what can you do" in last_message.lower():
            return self._describe_capabilities()
        
        # Use LLM for general responses and enhance with data context
        base_response = await super().generate(messages)
        return f"{base_response}\n\nAvailable data sources: {', '.join(self.data_sources)}"
    
    def _describe_capabilities(self) -> str:
        """Describe specialized capabilities."""
        return (
            f"I am a Data Analyst with access to: {', '.join(self.data_sources)}.\n"
            f"I can perform {', '.join(self.analysis_methods)} analysis and create "
            f"{', '.join(self.visualization_types)} visualizations."
        )


async def main():
    """Run the example."""
    # Register our custom DataAnalystAgent with the AgentFactory singleton
    factory = AgentFactory.get_instance()
    factory.register_agent_class("data_analyst", DataAnalystAgent)
    
    # Create team with custom config for the data analyst using TeamBuilder
    team = TeamBuilder.create_team(
        "data_team",
        agent_configs={
            "data_analyst": {
                "name": "DataAnalyst",
                "data_sources": ["CSV", "SQL", "Excel"],
                "analysis_methods": ["descriptive", "predictive"],
                "visualization_types": ["charts", "graphs"]
            }
        }
    )
    
    # Find and interact with the data analyst agent
    data_analyst = next(
        (agent for agent in team.agents.values() if hasattr(agent, 'data_sources')),
        None
    )
    
    if data_analyst:
        response = await data_analyst.generate([{
            "role": "user", 
            "content": "What can you do as a data analyst?"
        }])
        print(f"\nResponse from {data_analyst.name}:\n{response}")


if __name__ == "__main__":
    asyncio.run(main()) 