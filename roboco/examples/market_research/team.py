"""
Market Research Team Implementation

This module implements a specialized team for conducting market research.
"""

import os
from typing import Dict, Any, List, Optional, Union
from loguru import logger

import autogen
from autogen import ConversableAgent, UserProxyAgent, AssistantAgent

from roboco.core import Team
from roboco.agents import ProductManager, Executive


class ResearchTeam(Team):
    """
    A team specialized for market research, comprising of product and executive roles.
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

        # Create agents using the improved create_agent method
        self.create_agent(ProductManager, "ProductManager")
        
        # Register tools with appropriate agents
        self._register_tools()
        
        logger.info("Research team initialized with Product Manager and tools")

    def _register_tools(self) -> None:
        """Register tools with the Product Manager agent."""
        # Use the new tool factory to automatically register all available tools
        self.register_tools_from_factory(
            tool_names=["WebSearchTool", "BrowserUseTool", "FileSystemTool", "BashTool", "TerminalTool", "RunTool"],  # Register all research tools
            agent_name="ProductManager"
        )
        
        # Alternatively, we could register all available tools:
        # self.register_all_tools(agent_name="ProductManager")

    def run_scenario(self, query: str) -> Dict[str, Any]:
        """
        Run the research scenario.

        Args:
            query: The initial query or research request

        Returns:
            Dictionary containing the conversation history and any generated reports
        """
        # Run the scenario using the base implementation
        result = super().run_scenario(
            prompt=query,
            receiver_agent_name="ProductManager"
        )

        # Save the research report
        if result["status"] == "success":
            conversations = result.get("conversation", {})

            # Extract the last message from the ProductManager
            product_manager_msgs = conversations.get("ProductManager", [])
            if product_manager_msgs:
                last_msg = product_manager_msgs[-1]
                if isinstance(last_msg, dict) and "content" in last_msg:
                    # Save the report
                    report_content = last_msg["content"]
                    filename = f"research_report_{len(self.artifacts)}.md"

                    # Use the Team's save_file_artifact method
                    report_path = self.save_file_artifact(
                        content=report_content,
                        filename=filename,
                        directory="reports"
                    )

                    # Add the report path to the result
                    result["report_path"] = report_path

        return result