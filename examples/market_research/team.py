"""
Market Research Team Implementation

This module implements a specialized team for conducting market research using AG2's Swarm pattern.
"""

import os
import logging
import traceback
from typing import Dict, Any, List, Optional, Union, Callable
from loguru import logger
import inspect

# ag2 and autogen are identical packages
import autogen
from autogen import ConversableAgent

from roboco.core import Team
from roboco.core.tool_factory import ToolFactory
from roboco.agents import ProductManager, Researcher, ReportWriter, ToolUser
from roboco.tools import BrowserTool


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
        logger.debug("Initializing ResearchTeam")
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.toml")
            logger.debug(f"Using default config path: {config_path}")
        
        # Initialize the base team
        logger.debug("Initializing base Team class")
        super().__init__(config_path=config_path)
        logger.debug("Base Team initialized")
        
        # Enable swarm orchestration
        logger.debug("Enabling swarm orchestration")
        self.enable_swarm(shared_context={
            "search_results": [],
            "analysis": [],
            "report_content": "",
            "status": "in_progress"
        })
        logger.debug("Swarm orchestration enabled")
        
        # Create the ProductManager agent (the main agent that directs research)
        logger.debug("Creating ProductManager agent")
        product_manager = self.create_agent(ProductManager, "ProductManager")
        
        # Create a ToolUser agent for tool execution
        logger.debug("Creating ToolUser agent")
        tool_user = ToolUser(
            name="ToolUser",
            human_input_mode="NEVER",
            code_execution_config={"last_n_messages": 3, "work_dir": "workspace", "use_docker": False},
            llm_config=self.llm_config
        )
        self.add_agent("ToolUser", tool_user)
        
        # Create a researcher agent to help with analyzing data
        logger.debug("Creating Researcher agent")
        researcher = self.create_agent(Researcher, "Researcher")
        
        # Create a report writer agent
        logger.debug("Creating ReportWriter agent")
        report_writer = self.create_agent(ReportWriter, "ReportWriter")
        
        # Register tools with all agents
        logger.debug("Registering tools")
        self._register_tools()
        logger.debug("Tools registered")
        
        # Configure the swarm handoffs
        logger.debug("Configuring swarm handoffs")
        self._configure_swarm_handoffs()
        logger.debug("Swarm handoffs configured")
        
        logger.info("Research team initialized with Swarm pattern")
        logger.debug("ResearchTeam initialization complete")
    
    def _register_tools(self) -> None:
        """Register tools with all agents."""
        # Define available tools
        available_tools = ["FileSystemTool", "BrowserTool"]
        
        # Get the ToolUser agent for tool execution
        tool_user = self.get_agent("ToolUser")
        if not tool_user:
            logger.warning("No ToolUser agent found for executing tools")
            return
            
        # Create tool instances
        tools = []
        for tool_name in available_tools:
            try:
                # Create the tool instance
                tool_instance = ToolFactory.create_tool(tool_name)
                tools.append(tool_instance)
            except Exception as e:
                logger.error(f"Error creating tool '{tool_name}': {e}")
        
        # Register tools with all agents using AG2's function registration
        for tool_instance in tools:
            tool_name = tool_instance.__class__.__name__
            
            # Find all public methods in the tool
            methods = {}
            for method_name, method in inspect.getmembers(tool_instance, inspect.ismethod):
                if not method_name.startswith('_'):
                    methods[method_name] = method
            
            # Register each method as a function with AG2
            for method_name, method in methods.items():
                # Create a function name that includes the tool name for clarity
                function_name = f"{tool_name.lower()}_{method_name}"
                
                # Get the method's docstring for description
                description = inspect.getdoc(method) or f"{method_name} function from {tool_name}"
                
                # Create a wrapper function that calls the method
                def create_wrapper(m):
                    def wrapper(*args: Any, **kwargs: Any) -> Any:
                        return m(*args, **kwargs)
                    return wrapper
                
                # Create a unique wrapper for this method
                wrapper = create_wrapper(method)
                wrapper.__name__ = method_name
                wrapper.__doc__ = description
                
                # Register with all agents
                for agent_name, agent in self.agents.items():
                    try:
                        autogen.register_function(
                            wrapper,  # Use the wrapper instead of the method directly
                            caller=agent,
                            executor=tool_user,
                            name=function_name,
                            description=description
                        )
                        logger.debug(f"Registered {function_name} with {agent_name}")
                    except Exception as e:
                        logger.error(f"Error registering {function_name} with {agent_name}: {e}")
            
            logger.info(f"Registered {tool_name} methods with all agents")
    
    def _configure_swarm_handoffs(self) -> None:
        """Configure handoffs between agents for the swarm pattern."""
        # Get all agents
        product_manager = self.get_agent("ProductManager")
        researcher = self.get_agent("Researcher")
        tool_user = self.get_agent("ToolUser")
        report_writer = self.get_agent("ReportWriter")
        
        # Import necessary components for swarm
        from autogen import OnCondition, AfterWork, AfterWorkOption
        
        # Define the research workflow with specific conditions
        if product_manager and researcher:
            self.register_handoff(
                agent_name="ProductManager",
                target_agent_name="Researcher",
                condition="When the ProductManager needs research on a topic",
                context_key="productmanager_to_researcher"
            )
            logger.debug("Registered handoff from ProductManager to Researcher")
        
        if researcher and tool_user:
            self.register_handoff(
                agent_name="Researcher",
                target_agent_name="ToolUser",
                condition="When Researcher needs to use tools to process or store information",
                context_key="researcher_to_tooluser"
            )
            logger.debug("Registered handoff from Researcher to ToolUser")
        
        if tool_user and report_writer:
            self.register_handoff(
                agent_name="ToolUser",
                target_agent_name="ReportWriter",
                condition="When ToolUser has processed information and a report needs to be created",
                context_key="tooluser_to_reportwriter"
            )
            logger.debug("Registered handoff from ToolUser to ReportWriter")
        
        if report_writer and product_manager:
            self.register_handoff(
                agent_name="ReportWriter",
                target_agent_name="ProductManager",
                condition="When ReportWriter has completed the report and needs review",
                context_key="reportwriter_to_productmanager"
            )
            logger.debug("Registered handoff from ReportWriter to ProductManager")
        
        # Add additional handoffs for flexibility
        agent_names = list(self.agents.keys())
        for i in range(len(agent_names) - 1):
            current_agent = agent_names[i]
            next_agent = agent_names[i + 1]
            self.register_handoff(
                agent_name=current_agent,
                target_agent_name=next_agent,
                condition=f"When {current_agent} needs to hand off to {next_agent}",
                context_key=f"{current_agent.lower()}_to_{next_agent.lower()}"
            )
            logger.debug(f"Registered handoff from {current_agent} to {next_agent}")
        
        logger.info("Configured swarm handoffs between all agents")
    
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

    def run_research(self, query: str) -> Dict[str, Any]:
        """
        Run a research scenario with the team.
        
        Args:
            query: The research query to investigate
            
        Returns:
            Dictionary containing the research results and report
        """
        logger.info(f"Running research on: {query}")
        
        # Create a detailed prompt with instructions
        prompt = self._format_research_prompt(query)
        
        # Run the research scenario using the swarm pattern
        result = self.run_swarm(
            query=query,
            callback=None,
            max_rounds=10  # Use a reasonable number of rounds
        )
        
        logger.info("Research completed")
        return result

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

    def _format_research_prompt(self, query: str) -> str:
        """
        Format the research prompt with the given query.
        
        Args:
            query: The research query
            
        Returns:
            The formatted research prompt
        """
        return f"""
        # Market Research Request

        Please conduct market research on the following topic:
        
        ## Topic
        {query}
        
        ## Research Guidelines:
        1. Begin by collaborating with the WebSurfer agent to gather relevant information
        2. Analyze the data and extract key insights
        3. Prepare a well-structured report with your findings
        4. Include market trends, competitor analysis, and recommendations
        5. Save the final report using the FileSystemTool
        
        ## Expected Workflow:
        1. ProductManager: Define the research scope and delegate tasks
        2. WebSurfer: Browse the web to gather information on the topic
        3. Researcher: Analyze the information gathered by WebSurfer
        4. ToolUser: Execute necessary tools for data collection and file operations
        5. ReportWriter: Compile findings into a comprehensive report

        ## Important Note:
        If the WebSurfer agent encounters issues, please continue with the research using your existing knowledge.
        Do not terminate the session if an agent fails - adapt and proceed with the available information.
        
        ## Agent Handoff Instructions:
        - ProductManager: After defining the research scope, explicitly hand off to the WebSurfer by saying "@WebSurfer, please gather information on {query}."
        - WebSurfer: After gathering information, explicitly hand off to the Researcher by saying "@Researcher, please analyze this information."
        - Researcher: After analyzing the information, explicitly hand off to the ToolUser by saying "@ToolUser, please execute the necessary tools."
        - ToolUser: After executing the tools, explicitly hand off to the ReportWriter by saying "@ReportWriter, please compile the report."
        - ReportWriter: After compiling the report, explicitly hand off to the ProductManager by saying "@ProductManager, please review the report."
        
        ## Specific Instructions for WebSurfer:
        When the ProductManager hands off to you, please:
        1. Use your web browsing capabilities to search for information on {query}
        2. Visit relevant websites and extract key information
        3. Summarize your findings and hand off to the Researcher
        
        ## Specific Instructions for Researcher:
        When the WebSurfer hands off to you, please:
        1. Analyze the information gathered by the WebSurfer
        2. Extract key insights and trends
        3. Hand off to the ToolUser to execute any additional tools needed
        
        ## Specific Instructions for ToolUser:
        When the Researcher hands off to you, please:
        1. Execute any necessary tools to gather additional information
        2. Use the filesystemtool_create_directory function to create a reports directory if needed
        3. Hand off to the ReportWriter to compile the final report
        
        ## Specific Instructions for ReportWriter:
        When the ToolUser hands off to you, please:
        1. Compile a comprehensive report based on the research findings
        2. Save the report using the filesystemtool_save_file function
        3. Hand off to the ProductManager for review
        
        Please ensure a complete research cycle with all agents participating as needed.
        """

    def extract_report_from_chat_history(self) -> str:
        """
        Extract the report from the chat history.
        
        Returns:
            The report content as a string, or None if no report was found
        """
        logger.debug("Extracting report from chat history")
        
        # Get the chat history
        chat_history = self.get_chat_history()
        if not chat_history:
            logger.warning("No chat history found")
            return None
        
        # Look for report content in the chat history
        report_content = None
        for message in reversed(chat_history):
            content = message.get("content", "")
            if isinstance(content, str) and "# Market Research Report" in content:
                logger.debug("Found report in chat history")
                report_content = content
                break
        
        if not report_content:
            # Try looking for content saved with the FileSystemTool
            for message in reversed(chat_history):
                content = message.get("content", "")
                if isinstance(content, str) and "filesystemtool_save_file" in content and ".md" in content:
                    # Extract the file content from the message
                    try:
                        # Look for the content parameter in the function call
                        import re
                        match = re.search(r'content="([^"]+)"', content)
                        if match:
                            report_content = match.group(1)
                            logger.debug("Found report in filesystemtool_save_file call")
                            break
                    except Exception as e:
                        logger.error(f"Error extracting report from filesystemtool_save_file call: {e}")
        
        return report_content

    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Get the chat history from the swarm.
        
        Returns:
            List of chat messages
        """
        logger.debug("Getting chat history from swarm")
        
        # Check if swarm is enabled
        if not hasattr(self, "swarm") or self.swarm is None:
            logger.warning("Swarm is not enabled, no chat history available")
            return []
        
        # Get the chat history from the swarm
        try:
            # Get the chat history from the swarm's chat_result
            if "chat_result" in self.swarm and self.swarm["chat_result"] is not None:
                chat_result = self.swarm["chat_result"]
                if hasattr(chat_result, "chat_history"):
                    # Convert the chat history to a list of dictionaries
                    chat_history = []
                    for message in chat_result.chat_history:
                        # Convert message to dictionary
                        message_dict = {
                            "role": getattr(message, "role", "unknown"),
                            "sender": getattr(message, "sender", "unknown"),
                            "receiver": getattr(message, "receiver", "unknown"),
                            "content": getattr(message, "content", ""),
                        }
                        chat_history.append(message_dict)
                    
                    logger.debug(f"Retrieved {len(chat_history)} messages from chat history")
                    return chat_history
            
            logger.warning("No chat history found in swarm")
            return []
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            logger.error(traceback.format_exc())
            return []

    def run_swarm(self, query: str, max_rounds: int = 50, callback: Optional[Callable] = None) -> Dict:
        """
        Run the research swarm with the given query.
        
        Args:
            query: The research query to investigate
            max_rounds: Maximum number of rounds for the swarm conversation
            callback: Optional callback function to call with the result
            
        Returns:
            Dictionary containing the chat history and context variables
        """
        logger.info(f"Running swarm with query: {query}")
        
        # Ensure handoffs are properly configured
        self._configure_swarm_handoffs()
        
        # Format the research prompt
        prompt = self._format_research_prompt(query)
        
        # Create context variables
        context_variables = {
            "query": query,
            "search_results": [],
            "analysis": [],
            "report_content": "",
            "status": "in_progress"
        }
        
        # Run the swarm with the ProductManager as the initial agent
        logger.info("Starting swarm with ProductManager as initial agent")
        
        # Get all agents
        agents = list(self.agents.values())
        
        # Log the agents that will be included in the swarm
        agent_names = [agent.name for agent in agents]
        logger.debug(f"Agents in swarm: {agent_names}")
        
        # Create a user proxy agent to initiate the conversation
        from autogen import UserProxyAgent
        user_proxy = UserProxyAgent(
            name="_User",
            human_input_mode="NEVER",
            code_execution_config={"use_docker": False}
        )
        
        # Get the ProductManager agent
        product_manager = self.get_agent("ProductManager")
        
        # Get the BrowserTool and register it with the user proxy
        browser_tool = next((tool for tool in self.tools if isinstance(tool, BrowserTool)), None)
        if browser_tool:
            logger.info("BrowserTool found")
            if hasattr(browser_tool, "tools"):
                logger.info("Registering BrowserTool with user proxy")
                for tool in browser_tool.tools:
                    tool.register_for_execution(user_proxy)
                    
            # Log BrowserTool details
            logger.debug(f"BrowserTool type: {type(browser_tool)}")
            logger.debug(f"BrowserTool attributes: {dir(browser_tool)}")
        else:
            logger.warning("BrowserTool not found")
        
        # Add explicit handoff instructions to the prompt
        handoff_instructions = """
        ## Important Handoff Instructions:
        - ProductManager: When you need web information, use the browser_tool to gather information.
        - Researcher: After analysis, say "@ToolUser, please execute the necessary tools."
        - ToolUser: After using tools, say "@ReportWriter, please compile the report."
        - ReportWriter: After writing the report, say "@ProductManager, please review the report."
        """
        
        enhanced_prompt = prompt + "\n\n" + handoff_instructions
        
        # Run the swarm
        try:
            result = self.run_swarm_chat(
                initial_agent_name="ProductManager",
                message=enhanced_prompt,
                context_variables=context_variables,
                max_rounds=max_rounds
            )
            
            # Update status
            context_variables["status"] = "completed"
            
            # Call callback if provided
            if callback:
                callback(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in swarm chat: {e}")
            logger.error(traceback.format_exc())
            context_variables["status"] = "error"
            raise