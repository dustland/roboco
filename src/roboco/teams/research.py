"""
Research Team Module

This module defines the ResearchTeam class, which specializes in research-related tasks
through a team of agents focused on information gathering and analysis.
"""

from typing import Dict, Any, List, Optional
import os
from loguru import logger
import asyncio
import json

from roboco.core.agent import Agent
from roboco.agents.human_proxy import HumanProxy


class ResearchTeam:
    """Team for conducting research and information gathering tasks."""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """Initialize the research team.
        
        Args:
            workspace_dir: Directory for workspace files
        """
        self.workspace_dir = workspace_dir
        
        # Initialize the agents
        analyst = Agent(
            name="analyst",
            system_message="""You are a research analyst that excels at finding and analyzing information.
            Your role is to gather relevant information about topics, analyze the data, 
            and present findings in a clear, structured manner. 
            You are thorough, methodical, and highly skilled at identifying patterns and insights.
            """,
            human_input_mode="NEVER",
            terminate_msg="TERMINATE"
        )
        
        researcher = Agent(
            name="researcher",
            system_message="""You are a skilled researcher who specializes in information gathering and synthesis.
            Your expertise includes finding relevant information, evaluating sources for credibility,
            and organizing information into coherent structures. You excel at breaking down complex
            topics into manageable research tasks and following systematic research methods.
            """,
            terminate_msg=None  # Set to None to prevent premature conversation termination
        )
        
        fact_checker = Agent(
            name="fact_checker",
            system_message="""You are a meticulous fact checker responsible for verifying information accuracy.
            You carefully examine claims, cross-reference sources, and ensure that all information is 
            correct and properly cited. You have high standards for evidence and are skilled at
            identifying inconsistencies or unsubstantiated claims.
            """,
            human_input_mode="NEVER",
            terminate_msg="TERMINATE"
        )
        
        human_proxy = HumanProxy(
            name="human_proxy",
            human_input_mode="TERMINATE"
        )
        
        self.agents = {
            "analyst": analyst,
            "researcher": researcher,
            "fact_checker": fact_checker,
            "human_proxy": human_proxy
        }
        
        # Register tools with agents
        from roboco.tools.fs import FileSystemTool
        fs_tool = FileSystemTool(workspace_dir=workspace_dir)
        
        # Register with all agents
        for agent_name, agent_instance in self.agents.items():
            fs_tool.register_with_agents(agent_instance)
        
        # Register web search tool if available
        try:
            from roboco.tools.web_search import WebSearchTool
            web_search_tool = WebSearchTool()
            web_search_tool.register_with_agents(researcher, analyst)
            logger.info("Registered WebSearchTool with research team")
        except ImportError:
            logger.warning("WebSearchTool not available, research capabilities will be limited")
    
    def get_agent(self, name: str) -> Agent:
        """Get an agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            The agent
            
        Raises:
            ValueError: If the agent is not found
        """
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not found")
        return self.agents[name]
    
    async def run_chat(self, query: str) -> Dict[str, Any]:
        """
        Run a research chat session.
        
        Args:
            query: The research query or task
            
        Returns:
            Dict containing the chat results
        """
        # Get the agents
        analyst = self.get_agent("analyst")
        researcher = self.get_agent("researcher")
        fact_checker = self.get_agent("fact_checker")
        
        # Format the message to create a research-focused approach
        message = f"""
        I need you to help me research the following:
        
        {query}
        
        Please gather relevant information, analyze it thoroughly, and present your findings.
        Make sure to use project files in {self.workspace_dir} for reference if relevant.
        """
        
        try:
            # Start with researcher to gather information
            logger.info(f"Starting research process for query: {query[:50]}...")
            
            # Researcher gathers information
            research_result = analyst.initiate_chat(
                recipient=researcher,
                message=message,
                max_turns=10,
            )
            
            # Fact checker verifies information
            fact_check_message = f"""
            Please fact-check and verify the following research results:
            
            {research_result.summary}
            
            Please be thorough and identify any questionable information.
            """
            
            fact_check_result = researcher.initiate_chat(
                recipient=fact_checker,
                message=fact_check_message,
                max_turns=5,
            )
            
            # Save the research results
            results_path = os.path.join(self.workspace_dir, "research_results.md")
            with open(results_path, "w") as f:
                f.write(f"# Research Results\n\n")
                f.write(f"## Query\n{query}\n\n")
                f.write(f"## Findings\n{research_result.summary}\n\n")
                f.write(f"## Verification\n{fact_check_result.summary}\n\n")
            
            logger.info(f"Research completed and saved to {results_path}")
            
            # Return the chat results
            return {
                "response": fact_check_result.summary,
                "chat_history": research_result.chat_history + fact_check_result.chat_history,
                "results_path": results_path
            }
            
        except Exception as e:
            logger.error(f"Error in research chat: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def conduct_research(self, topic: str, output_file: str = None) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a topic and save results.
        
        Args:
            topic: The research topic
            output_file: Optional output file path (relative to workspace_dir)
            
        Returns:
            Dict containing research results
        """
        # Format the query for thorough research
        research_query = f"""
        Conduct comprehensive research on the following topic:
        
        {topic}
        
        Please follow these research steps:
        1. Define the scope of the research
        2. Gather relevant information
        3. Analyze the information
        4. Synthesize findings
        5. Present conclusions
        
        Your final report should include:
        - Key findings
        - Analysis
        - Recommendations if applicable
        """
        
        # Run the research chat
        results = await self.run_chat(research_query)
        
        # Save to specific output file if provided
        if output_file and "error" not in results:
            full_output_path = os.path.join(self.workspace_dir, output_file)
            os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
            
            with open(full_output_path, "w") as f:
                f.write(f"# Research Report: {topic}\n\n")
                f.write(results["response"])
            
            results["output_file"] = full_output_path
            logger.info(f"Research results saved to {full_output_path}")
        
        return results 