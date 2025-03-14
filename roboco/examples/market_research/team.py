"""
Market Research Team Module

This module defines the ResearchTeam class that coordinates CEO and Product Manager agents 
for researching cutting-edge embodied AI technologies using the AG2 framework.
"""

import os
import sys
import tomli
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
from loguru import logger

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import AG2 components directly from autogen
import autogen
from autogen import (
    AssistantAgent,
    ConversableAgent,
    UserProxyAgent,
    initiate_chats,
    config_list_from_json,
    config_list_from_dotenv
)

# Import roboco specific components
from roboco.core.ag2_integration import load_config_from_toml

# Import tools
from roboco.tools.web_search import WebSearchTool
from roboco.tools.base import Tool

class ResearchTeam:
    """
    A team of agents for conducting market research on embodied AI technologies
    using the AG2 framework.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the research team with AG2 agents.
        
        Args:
            config_path: Path to the configuration file
        """
        # Load configuration
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.toml")
        self.config = self._load_config()
        
        # Get the AG2-compatible config
        self.llm_config = load_config_from_toml(self.config_path)
        
        # Create CEO agent
        self.ceo = AssistantAgent(
            name="CEO",
            system_message="""You are the CEO of a cutting-edge robotics company.
You are interested in the latest developments in embodied AI applications.
Your role is to ask strategic questions about emerging technologies and market opportunities.
You should evaluate the research provided by your team and ask follow-up questions.
Focus on business impact, competitive advantage, and potential applications of new technologies.
""",
            llm_config=self.llm_config
        )
        
        # Create Product Manager agent with tools
        self.product_manager = AssistantAgent(
            name="ProductManager",
            system_message="""You are a Product Manager at a cutting-edge robotics company.
Your expertise is in market research, technology trends, and product strategy.
Your role is to research emerging technologies and market opportunities in embodied AI.
When asked to research a topic, you should:
1. Define the scope of the research
2. Gather information using available tools, especially web_search
3. Analyze the current state of the technology
4. Identify key trends and opportunities
5. Write a comprehensive research report with the following sections:
   - Executive Summary
   - Current State of Technology
   - Key Players and Products
   - Technical Approaches
   - Market Opportunities
   - Recommendations

Your research should be data-driven, insightful, and actionable.
Always save your final research report to a markdown file in the reports/ directory.
""",
            llm_config=self.llm_config
        )
        
        # Initialize and register tools
        self._register_tools()
                
        logger.info("Initialized Market Research Team with AG2 framework")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from the TOML file."""
        try:
            with open(self.config_path, "rb") as f:
                config = tomli.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _register_tools(self) -> None:
        """Register tools with the Product Manager agent."""
        # Create web search tool
        web_search_tool = WebSearchTool()
        
        # Register the tool functions with the Product Manager
        for func_name, func in web_search_tool.get_functions().items():
            self.product_manager.register_function(
                function_map={func_name: func}
            )
        
        # Add a file saving function
        def save_report(content: str, filename: str) -> str:
            """
            Save a research report to a file.
            
            Args:
                content: Content of the report
                filename: Name of the file (without directory)
                
            Returns:
                Path where the file was saved
            """
            # Ensure the reports directory exists
            reports_dir = Path(__file__).parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            
            # Add a timestamp if no extension is provided
            if "." not in filename:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{filename}_{timestamp}.md"
            
            # Save the file
            file_path = reports_dir / filename
            with open(file_path, "w") as f:
                f.write(content)
            
            return str(file_path)
        
        # Register the file saving function
        self.product_manager.register_function(
            function_map={"save_report": save_report}
        )
        
        logger.info("Registered tools with the Product Manager agent")
    
    def run_scenario(self, query: str) -> Dict[str, Any]:
        """
        Run the research scenario.
        
        Args:
            query: The initial query or research request
            
        Returns:
            Dictionary containing the conversation history and any generated reports
        """
        logger.info(f"Starting research scenario with query: {query}")
        
        # Create a UserProxyAgent to start the conversation
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False},
            llm_config=False,  # No LLM for user proxy
            system_message="Representing the company's management"
        )
        
        # Set up the conversation
        user_proxy.initiate_chat(
            recipient=self.ceo,
            message=query
        )
        
        # Get the conversation history
        chat_history = user_proxy.chat_messages[self.ceo]
        
        # Process results
        result = {
            "conversation": chat_history,
            "agents": [self.ceo.name, self.product_manager.name],
            "query": query
        }
        
        logger.info(f"Research scenario completed with {len(chat_history)} message exchanges")
        return result