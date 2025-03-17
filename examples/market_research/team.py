"""
Market Research Team Implementation - Simplified
"""

import os
from typing import Dict, Any, Optional
from loguru import logger
from autogen import initiate_swarm_chat, register_hand_off, AfterWork, AfterWorkOption
from roboco.core import Team
from roboco.tools import WebSearchTool
from roboco.agents import ProductManager, Researcher, ReportWriter, HumanProxy

class ResearchTeam(Team):
    """A simplified team for market research using AG2's Swarm pattern."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the research team with agents."""
        super().__init__(name="ResearchTeam", agents={}, config_path=config_path)
        self.enable_swarm(shared_context={"report_content": ""})
        
        # Create agents
        self.product_manager = self.create_agent(ProductManager, "ProductManager")
        self.tool_executor = HumanProxy(name="ToolExecutor", human_input_mode="NEVER")
        self.add_agent("ToolExecutor", self.tool_executor)
        self.researcher = self.create_agent(Researcher, "Researcher")
        self.report_writer = self.create_agent(ReportWriter, "ReportWriter")
        
        # Create and register the WebSearchTool with agents
        web_search_tool = WebSearchTool(
            api_key=os.environ.get("TAVILY_API_KEY", ""),
            search_config={"max_results": 5}
        )
        
        # Register the tool with each agent that needs it
        for agent in [self.product_manager, self.researcher, self.report_writer]:
            web_search_tool.register_with_agents(
                caller_agent=agent,
                executor_agent=self.tool_executor
            )
        
        # Configure handoff chain: PM -> Researcher -> ToolExecutor -> ReportWriter -> PM
        # Using the updated register_hand_off format with AfterWork
        self._register_handoffs()
    
    def _register_handoffs(self):
        """Register handoffs between agents in the correct order."""
        agents = [self.product_manager, self.researcher, self.tool_executor, self.report_writer]
        
        # Create circular handoffs
        for i, agent in enumerate(agents):
            next_agent = agents[(i + 1) % len(agents)]
            register_hand_off(
                agent=agent,
                hand_to=[AfterWork(agent=next_agent)]
            )
        
        logger.info(f"Registered handoffs between {len(agents)} agents")
    
    def run_research(self, query: str) -> Dict[str, Any]:
        """Run a research scenario with the given query."""
        result = self.run_swarm(
            initial_agent_name="ProductManager",
            query=query,
            max_rounds=10
        )
        return result
    
    def run_swarm(self, 
                initial_agent_name: str, 
                query: str, 
                context_variables: Optional[Dict[str, Any]] = None,
                max_rounds: int = 10) -> Dict[str, Any]:
        """Run the swarm with the given query."""
        initial_message = f"Please conduct market research on: {query}"
        
        # Get all agents
        agents = [self.product_manager, self.researcher, self.tool_executor, self.report_writer]
        
        # Get the initial agent
        initial_agent = self.get_agent(initial_agent_name)
        if not initial_agent:
            initial_agent = self.product_manager
        
        # Prepare context
        context = context_variables or {}
        context.update({"query": query, "report_content": ""})
        
        # Run the swarm
        logger.info(f"Running swarm with query: {query}")
        chat_result = initiate_swarm_chat(
            initial_agent=initial_agent,
            agents=agents,
            messages=[initial_message],
            context_variables=context,
            max_rounds=max_rounds,
            after_work=AfterWorkOption.TERMINATE
        )
        logger.info(f"Swarm completed, chat_result type: {type(chat_result)}")
        
        # Return the result
        return {"chat_result": chat_result}