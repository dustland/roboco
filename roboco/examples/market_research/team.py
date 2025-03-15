"""
Market Research Team Implementation

This module implements a specialized team for conducting market research using AG2's Swarm pattern.
"""

import os
from typing import Dict, Any, List, Optional, Union
from loguru import logger

import autogen
from autogen import ConversableAgent

from roboco.core import Team
from roboco.agents import ProductManager, Researcher, ReportWriter, ToolUser


class ResearchTeam(Team):
    """
    A team specialized for market research, comprising of product and research roles
    using AG2's Swarm pattern for better collaboration.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the research team with agents.

        Args:
            config_path: Path to the configuration file
        """
        # Set default config path if not provided
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.toml")

        # Initialize the base team
        super().__init__(config_path=config_path)

        # Enable swarm orchestration
        self.enable_swarm(shared_context={
            "search_results": [],
            "analysis": [],
            "report_content": "",
            "status": "in_progress"
        })

        # Create the ProductManager agent (the main agent that directs research)
        product_manager = self.create_agent(ProductManager, "ProductManager")
        
        # Create a ToolUser agent for tool execution
        tool_user = ToolUser(
            name="ToolUser",
            human_input_mode="NEVER",
            code_execution_config={"last_n_messages": 3, "work_dir": "workspace", "use_docker": False},
            llm_config=self.llm_config
        )
        self.add_agent("ToolUser", tool_user)
        
        # Create a researcher agent to help with analyzing data
        researcher = self.create_agent(Researcher, "Researcher")
        
        # Create a report writer agent
        report_writer = self.create_agent(ReportWriter, "ReportWriter")
        
        # Register tools with all agents
        self._register_tools()
        
        # Configure the swarm handoffs
        self._configure_swarm_handoffs()
        
        logger.info("Research team initialized with Swarm pattern")
    
    def _register_tools(self) -> None:
        """Register tools with all agents."""
        # Define available tools
        available_tools = ["WebSearchTool", "FileSystemTool"]
        
        # Register tools with all agents
        for agent_name in self.agents:
            self.register_tools_from_factory(
                tool_names=available_tools,
                agent_name=agent_name
            )
            logger.info(f"Registered tools with {agent_name}")
    
    def _configure_swarm_handoffs(self) -> None:
        """Configure the swarm handoffs between agents."""
        # Define handoffs from ProductManager
        self.register_handoff(
            agent_name="ProductManager",
            target_agent_name="Researcher",
            condition="When search results need to be analyzed or insights need to be extracted.",
            context_key="pm_to_researcher"
        )
        
        self.register_handoff(
            agent_name="ProductManager",
            target_agent_name="ReportWriter",
            condition="When analysis is complete and a report needs to be created.",
            context_key="pm_to_report_writer"
        )
        
        self.register_default_handoff(
            agent_name="ProductManager",
            target_agent_name=None  # Terminate when no conditions are met
        )
        
        # Define handoffs from Researcher
        self.register_handoff(
            agent_name="Researcher",
            target_agent_name="ProductManager",
            condition="When data analysis is complete and insights have been extracted.",
            context_key="researcher_to_pm"
        )
        
        self.register_handoff(
            agent_name="Researcher",
            target_agent_name="ReportWriter",
            condition="When analysis is complete and ready to be formatted into a report.",
            context_key="researcher_to_report_writer"
        )
        
        self.register_default_handoff(
            agent_name="Researcher",
            target_agent_name="ProductManager"  # Default to ProductManager
        )
        
        # Define handoffs from ReportWriter
        self.register_handoff(
            agent_name="ReportWriter",
            target_agent_name="ProductManager",
            condition="When the report is complete and ready for review.",
            context_key="report_writer_to_pm"
        )
        
        self.register_handoff(
            agent_name="ReportWriter",
            target_agent_name="Researcher",
            condition="When more analysis or data interpretation is needed to complete the report.",
            context_key="report_writer_to_researcher"
        )
        
        self.register_default_handoff(
            agent_name="ReportWriter",
            target_agent_name=None  # Terminate when no conditions are met
        )
        
        # Configure all handoffs with AG2
        self.configure_swarm_handoffs()
        
        logger.info("Swarm handoffs configured")

    def save_report(self, report_content: str) -> str:
        """
        Save the research report to a file.
        
        Args:
            report_content: The content of the report
            
        Returns:
            Path to the saved report
        """
        filename = f"research_report_{len(self.artifacts)}.md"
        
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)
        
        # Save the file directly
        report_path = os.path.join("reports", filename)
        with open(report_path, "w") as f:
            f.write(report_content)
        
        # Add the report to artifacts
        self.artifacts[filename] = {
            "name": filename,
            "content": report_content,
            "type": "report",
            "path": report_path
        }
        
        return report_path

    def run_scenario(self, query: str) -> Dict[str, Any]:
        """
        Run the research scenario using AG2's Swarm pattern.

        Args:
            query: The initial query or research request

        Returns:
            Dictionary containing the conversation history and any generated reports
        """
        # Format the initial message with clear instructions
        initial_message = f"""
        # Market Research Request
        
        Please conduct comprehensive market research on the following topic:
        
        **Topic**: {query}
        
        ## Research Guidelines:
        1. Begin by searching for relevant information using the WebSearchTool
        2. Analyze the data and extract key insights
        3. Prepare a well-structured report with your findings
        4. Include market trends, competitor analysis, and recommendations
        5. Save the final report using the FileSystemTool
        
        Please collaborate with the Researcher and ReportWriter agents as needed to complete this task.
        """
        
        # Define context variables for this specific research scenario
        context_variables = {
            "query": query,
            "search_results": [],
            "analysis": [],
            "report_content": "",
            "status": "in_progress"
        }
        
        # Run the swarm scenario using the base implementation with swarm mode
        result = super().run_scenario(
            prompt=initial_message,
            receiver_agent_name="ProductManager",
            use_swarm=True,
            context_variables=context_variables
        )
        
        # Process the results
        updated_context = result.get("context", {})
        
        # Save the report if it exists
        report_content = updated_context.get("report_content", "")
        if report_content:
            report_path = self.save_report(report_content)
            result["report_path"] = report_path
            logger.info(f"Research report saved to {report_path}")
            
            # Update status
            result["status"] = "success"
        else:
            result["status"] = "incomplete"
        
        return result