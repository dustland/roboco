"""
Market Research Team Implementation

This module implements a specialized team for conducting market research using AG2's Swarm pattern.
"""

import os
import logging
import traceback
from typing import Dict, Any, List, Optional, Union, Callable, Type
from loguru import logger
import inspect

# ag2 and autogen are identical packages
import autogen
from autogen import ConversableAgent, initiate_swarm_chat, register_hand_off, OnCondition, AfterWorkOption, AfterWork

from roboco.core import Team
from roboco.core.tool_factory import ToolFactory
from roboco.agents import ProductManager, Researcher, ReportWriter, HumanProxy
from roboco.core.config import get_llm_config


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
        
        # Initialize with empty agents dictionary - we'll add them after initialization
        logger.debug("Initializing base Team class")
        super().__init__(name="ResearchTeam", agents={}, config_path=config_path)
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
        
        # Create a common LLM config for all agents
        self.common_llm_config = {
            "config_list": [{"model": "gpt-4o", "api_key": os.environ.get("OPENAI_API_KEY")}],
            "temperature": 0.7,
            "max_tokens": 8000
        }
        
        # Create the agents and store them as member variables
        self.product_manager = self._create_product_manager()
        self.tool_executor = self._create_tool_executor()
        self.researcher = self._create_researcher()
        self.report_writer = self._create_report_writer()
        
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
    
    def _create_product_manager(self):
        """Create the ProductManager agent."""
        logger.debug("Creating ProductManager agent")
        return self.create_agent(ProductManager, "ProductManager", terminate_msg=None)
    
    def _create_tool_executor(self):
        """Create the ToolExecutor agent (HumanProxy)."""
        logger.debug("Creating HumanProxy agent for tool execution")
        
        tool_executor = HumanProxy(
            name="ToolExecutor",
            human_input_mode="NEVER",  # Disable human input for automation
            llm_config=self.common_llm_config  # Use the common LLM config
        )
        self.add_agent("ToolExecutor", tool_executor)
        return tool_executor
    
    def _create_researcher(self):
        """Create the Researcher agent."""
        logger.debug("Creating Researcher agent")
        return self.create_agent(Researcher, "Researcher", terminate_msg=None)
    
    def _create_report_writer(self):
        """Create the ReportWriter agent."""
        logger.debug("Creating ReportWriter agent")
        return self.create_agent(ReportWriter, "ReportWriter", terminate_msg=None)
    
    def _register_tools(self) -> None:
        """Register tools with all agents.
        
        This follows AG2's pattern where:
        1. Regular agents (ProductManager, Researcher, ReportWriter) are suggestors/callers
        2. HumanProxy (ToolExecutor) is the sole executor
        3. Tools are registered exclusively through ToolFactory
        """
        # Register BrowserTool with all agents
        caller_agents = [
            ("ProductManager", self.product_manager),
            ("Researcher", self.researcher),
            ("ReportWriter", self.report_writer)
        ]
        
        for agent_name, agent in caller_agents:
            try:
                # Register BrowserTool with the agent as caller and ToolExecutor as executor
                ToolFactory.register_tool(
                    caller_agent=agent,
                    executor_agent=self.tool_executor,
                    tool_name="BrowserTool"
                )
                logger.debug(f"Registered BrowserTool with {agent_name} (caller) and ToolExecutor (executor)")
            except Exception as e:
                logger.error(f"Error registering BrowserTool with {agent_name}: {e}")
        
        logger.info("Registered BrowserTool with all caller agents")
            
    def _configure_swarm_handoffs(self) -> None:
        """Configure handoffs between agents for the swarm pattern."""
        # Define the research workflow with specific conditions using the recommended pattern
        register_hand_off(
            agent=self.product_manager,
            hand_to=[
                OnCondition(
                    target=self.researcher, 
                    condition="When the ProductManager needs research on a topic"
                ),
                AfterWork(self.researcher)  # After work, go to Researcher
            ]
        )
        logger.debug("Registered handoff from ProductManager to Researcher")
        
        register_hand_off(
            agent=self.researcher,
            hand_to=[
                OnCondition(
                    target=self.tool_executor, 
                    condition="When Researcher needs to use tools to gather information"
                ),
                AfterWork(self.tool_executor)  # After work, go to ToolExecutor
            ]
        )
        logger.debug("Registered handoff from Researcher to ToolExecutor")
        
        register_hand_off(
            agent=self.tool_executor,
            hand_to=[
                OnCondition(
                    target=self.report_writer, 
                    condition="When ToolExecutor has gathered information and a report needs to be created"
                ),
                AfterWork(self.report_writer)  # After work, go to ReportWriter
            ]
        )
        logger.debug("Registered handoff from ToolExecutor to ReportWriter")
        
        register_hand_off(
            agent=self.report_writer,
            hand_to=[
                OnCondition(
                    target=self.product_manager, 
                    condition="When ReportWriter has completed the report and needs review"
                ),
                AfterWork(self.product_manager)  # After work, go to ProductManager
            ]
        )
        logger.debug("Registered handoff from ReportWriter to ProductManager")
        
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
        Run a research scenario with the given query.
        
        Args:
            query: The research query to investigate
            
        Returns:
            Dictionary containing the research results
        """
        logger.info(f"Running research on: {query}")
        
        # Run the swarm
        result = self.run_swarm(query)
        
        # Check if the report was extracted
        if "context" in result and "report_content" in result["context"] and result["context"]["report_content"]:
            logger.info("Report found in context")
            # Save the report to a file if not already saved
            if "report_path" not in result:
                report_path = self.save_report(result["context"]["report_content"])
                result["report_path"] = report_path
                logger.info(f"Research report saved to {report_path}")
            return result
        
        # Try to extract the report from the chat history
        report_content = self.extract_report_from_chat_history(result)
        if report_content:
            logger.info("Report extracted from chat history")
            if "context" in result:
                result["context"]["report_content"] = report_content
            # Save the report to a file
            report_path = self.save_report(report_content)
            result["report_path"] = report_path
            logger.info(f"Research report saved to {report_path}")
            return result
        
        # If no report was found, check the raw chat result
        if hasattr(self, "_last_chat_result"):
            logger.debug("Checking raw chat result for report")
            chat_result = self._last_chat_result
            
            # Try to extract report directly from the chat result
            try:
                # First, try to iterate through the chat_result as a list
                logger.debug("Trying to iterate through chat_result as a list")
                try:
                    # Get the length of chat_result
                    chat_result_length = len(chat_result)
                    logger.debug(f"Chat result length: {chat_result_length}")
                    
                    # Iterate through the chat_result directly
                    for i in range(chat_result_length):
                        try:
                            message = chat_result[i]
                            logger.debug(f"Examining message {i}: {type(message)}")
                            
                            # Check if this is a message from ReportWriter
                            sender = getattr(message, "sender", None)
                            if sender == "ReportWriter":
                                logger.debug(f"Found message from ReportWriter at index {i}")
                                content = getattr(message, "content", "")
                                if isinstance(content, str):
                                    logger.debug(f"Message content length: {len(content)}")
                                    # Check if content contains a markdown heading or looks like a report
                                    if "#" in content or "Trends in AI Assistants" in content:
                                        logger.info(f"Found report in chat_result[{i}] from ReportWriter")
                                        report_content = content
                                        if "context" in result:
                                            result["context"]["report_content"] = report_content
                                        # Save the report
                                        report_path = self.save_report(report_content)
                                        result["report_path"] = report_path
                                        logger.info(f"Research report saved to {report_path}")
                                        return result
                        except (IndexError, AttributeError) as e:
                            logger.debug(f"Error accessing chat_result[{i}]: {e}")
                except Exception as e:
                    logger.error(f"Error iterating through chat_result as a list: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # If that didn't work, try to convert chat_result to a list
                logger.debug("Trying to convert chat_result to a list")
                try:
                    # Convert chat_result to a list if it's not already
                    if not isinstance(chat_result, list):
                        chat_result_list = list(chat_result)
                        logger.debug(f"Converted chat_result to list with {len(chat_result_list)} items")
                    else:
                        chat_result_list = chat_result
                        logger.debug(f"Chat result is already a list with {len(chat_result_list)} items")
                    
                    # Look for ReportWriter's message
                    for i, message in enumerate(chat_result_list):
                        if hasattr(message, 'content') and hasattr(message, 'sender'):
                            if message.sender == "ReportWriter" and isinstance(message.content, str):
                                content = message.content
                                logger.debug(f"Found message from ReportWriter at index {i}")
                                # Check if content contains a markdown heading or looks like a report
                                if "#" in content or "Trends in AI Assistants" in content:
                                    logger.info(f"Found report in chat_result_list[{i}] from ReportWriter")
                                    report_content = content
                                    if "context" in result:
                                        result["context"]["report_content"] = report_content
                                    # Save the report
                                    report_path = self.save_report(report_content)
                                    result["report_path"] = report_path
                                    logger.info(f"Research report saved to {report_path}")
                                    return result
                except Exception as e:
                    logger.error(f"Error converting chat_result to list: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                
                # If still no report, try to access the chat_result's attributes
                logger.debug("Trying to access chat_result's attributes")
                try:
                    # Check if chat_result has a messages attribute
                    if hasattr(chat_result, 'messages'):
                        logger.debug(f"Found messages attribute with {len(chat_result.messages)} items")
                        for i, message in enumerate(chat_result.messages):
                            if hasattr(message, 'content') and hasattr(message, 'sender'):
                                if message.sender == "ReportWriter" and isinstance(message.content, str):
                                    content = message.content
                                    logger.debug(f"Found message from ReportWriter at index {i}")
                                    # Check if content contains a markdown heading or looks like a report
                                    if "#" in content or "Trends in AI Assistants" in content:
                                        logger.info(f"Found report in chat_result.messages[{i}] from ReportWriter")
                                        report_content = content
                                        if "context" in result:
                                            result["context"]["report_content"] = report_content
                                        # Save the report
                                        report_path = self.save_report(report_content)
                                        result["report_path"] = report_path
                                        logger.info(f"Research report saved to {report_path}")
                                        return result
                except Exception as e:
                    logger.error(f"Error accessing chat_result's attributes: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            except Exception as e:
                logger.error(f"Error extracting report from raw chat result: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # If still no report, log a warning
        logger.warning("No report found in research results")
        
        logger.info("Research completed")
        return result

    def _format_research_prompt(self, query: str) -> str:
        """
        Format the research prompt with the given query.
        
        Args:
            query: The research query
            
        Returns:
            The formatted research prompt
        """
        return f"""Please conduct market research on: {query}
        
        This research should include gathering real information from the web, analyzing the findings, and creating a comprehensive report.
        """

    def extract_report_from_chat_history(self, result=None):
        """
        Extract the report content from the chat history or context.
        
        Args:
            result: The result from the swarm execution (optional)
            
        Returns:
            The report content as a string, or None if no report was found
        """
        logger.debug("Extracting report from chat history or context")
        
        # Use provided result or stored result
        if result is None:
            if hasattr(self, "_last_swarm_result") and self._last_swarm_result is not None:
                result = self._last_swarm_result
            else:
                logger.warning("No result available")
                return None
        
        # Check if the context contains report_content
        if isinstance(result, dict) and "context" in result:
            context = result["context"]
            if isinstance(context, dict) and "report_content" in context and context["report_content"]:
                logger.info("Found report in context's report_content")
                return context["report_content"]
        
        # Get the chat history
        chat_history = []
        if isinstance(result, dict) and "chat_history" in result:
            chat_history = result["chat_history"]
        elif hasattr(result, "chat_history") and result.chat_history is not None:
            # Handle the case where result is a ChatResult object
            try:
                chat_history = []
                for message in result.chat_history:
                    # Convert message to dictionary
                    message_dict = {
                        "role": getattr(message, "role", "unknown"),
                        "name": getattr(message, "sender", "unknown"),
                        "content": getattr(message, "content", ""),
                    }
                    chat_history.append(message_dict)
            except Exception as e:
                logger.error(f"Error converting chat history: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # If we still don't have chat history, try to get it from the swarm manager
        if not chat_history and hasattr(self, "_swarm_manager") and self._swarm_manager is not None:
            try:
                if hasattr(self._swarm_manager, "chat_history"):
                    logger.debug("Getting chat history from swarm manager")
                    for message in self._swarm_manager.chat_history:
                        message_dict = {
                            "role": getattr(message, "role", "unknown"),
                            "name": getattr(message, "sender", "unknown"),
                            "content": getattr(message, "content", ""),
                        }
                        chat_history.append(message_dict)
            except Exception as e:
                logger.error(f"Error getting chat history from swarm manager: {e}")
        
        if not chat_history:
            logger.warning("No chat history found")
            return None
        
        # Look for report content in the chat history
        for message in chat_history:
            if isinstance(message, dict) and message.get("name") == "ReportWriter":
                content = message.get("content", "")
                if isinstance(content, str) and "#" in content:
                    # Check if content contains a markdown heading
                    lines = content.strip().split("\n")
                    for line in lines:
                        if line.strip().startswith("#"):
                            logger.debug("Found report in chat history")
                            return content
        
        logger.warning("No report found in chat history")
        return None

    def run_swarm(self, query: str, max_rounds: int = 10) -> Dict[str, Any]:
        """
        Run the swarm with the given query.
        
        Args:
            query: The research query to investigate
            max_rounds: Maximum number of rounds for the swarm conversation
            
        Returns:
            Dictionary containing the chat history and context variables
        """
        logger.info(f"Running swarm with query: {query}")
        
        # Format a simple initial message
        initial_message = f"Please conduct market research on: {query}"
        
        # Create context variables
        context_variables = {
            "query": query,
            "search_results": [],
            "analysis": [],
            "report_content": "",
            "status": "in_progress"
        }
        
        # Get all agents for the swarm
        agents = [
            self.product_manager,
            self.researcher,
            self.tool_executor,
            self.report_writer
        ]
        
        # Log the agents that will be included in the swarm
        agent_names = [agent.name for agent in agents]
        logger.debug(f"Agents in swarm: {agent_names}")
        
        # Add a message handler to capture the ReportWriter's message
        report_content = [None]  # Use a list to allow modification in the inner function
        
        def message_handler(sender, recipient, message):
            logger.debug(f"Message from {sender} to {recipient}: {message[:100]}...")
            if sender == "ReportWriter" and isinstance(message, str) and "#" in message:
                logger.info(f"Captured report from ReportWriter: {message[:100]}...")
                report_content[0] = message
                # Store the report in context variables
                context_variables["report_content"] = message
        
        # Register the message handler with each agent
        for agent in agents:
            if hasattr(agent, "register_message_handler"):
                agent.register_message_handler(message_handler)
                logger.debug(f"Registered message handler with {agent.name}")
        
        # Run the swarm
        try:
            # Get LLM config for swarm manager
            llm_config = self.product_manager.llm_config
            
            # Use AG2's initiate_swarm_chat
            logger.info("Starting swarm chat with initiate_swarm_chat")
            chat_result = initiate_swarm_chat(
                initial_agent=self.product_manager,  # Start with ProductManager
                agents=agents,
                messages=initial_message,  # Simple initial message
                context_variables=context_variables,
                max_rounds=max_rounds,
                swarm_manager_args={"llm_config": llm_config},  # Add swarm manager config
                after_work=AfterWorkOption.TERMINATE,  # Use TERMINATE to ensure agents complete their work
                user_agent=self.tool_executor  # Use the existing tool_executor as the user_agent
            )
            
            # Store the raw chat result for later use
            self._last_chat_result = chat_result
            
            # Debug: Print chat result attributes
            logger.debug(f"Chat result attributes: {dir(chat_result)}")
            
            # Store the swarm manager if available
            if hasattr(chat_result, "swarm_manager"):
                self._swarm_manager = chat_result.swarm_manager
                logger.debug("Stored swarm manager for later access")
            elif hasattr(chat_result, "_swarm_manager"):
                self._swarm_manager = chat_result._swarm_manager
                logger.debug("Stored swarm manager from _swarm_manager attribute")
            else:
                logger.warning("No swarm manager found in chat result")
            
            # Extract the results and convert to a dictionary
            try:
                # Access the chat history directly from the chat manager if available
                chat_manager = None
                if hasattr(chat_result, "chat_manager"):
                    chat_manager = chat_result.chat_manager
                    logger.debug("Found chat_manager in chat_result")
                elif hasattr(chat_result, "_chat_manager"):
                    chat_manager = chat_result._chat_manager
                    logger.debug("Found _chat_manager in chat_result")
                
                # Extract chat history
                chat_history = []
                
                # Check if we captured a report from the message handler
                if report_content[0]:
                    logger.info("Using report captured by message handler")
                    context_variables["report_content"] = report_content[0]
                
                # Try to get chat history from chat manager first
                if chat_manager and hasattr(chat_manager, "messages"):
                    logger.debug("Getting chat history from chat manager messages")
                    for i, message in enumerate(chat_manager.messages):
                        if hasattr(message, "content") and hasattr(message, "role") and hasattr(message, "name"):
                            message_dict = {
                                "role": message.role,
                                "name": message.name,
                                "content": message.content,
                            }
                            chat_history.append(message_dict)
                            
                            # Check if this message is from ReportWriter and contains a report
                            if message.name == "ReportWriter" and isinstance(message.content, str) and "#" in message.content:
                                logger.debug(f"Found potential report in message {i} from ReportWriter")
                                # Check if content contains a markdown heading
                                lines = message.content.strip().split("\n")
                                for line in lines:
                                    if line.strip().startswith("#"):
                                        logger.info(f"Found report with heading: {line.strip()}")
                                        context_variables["report_content"] = message.content
                                        break
                
                # If no chat history from chat manager, try from chat_result
                if not chat_history and hasattr(chat_result, "chat_history") and chat_result.chat_history is not None:
                    logger.debug("Getting chat history from chat_result.chat_history")
                    for message in chat_result.chat_history:
                        # Convert message to dictionary
                        message_dict = {
                            "role": getattr(message, "role", "unknown"),
                            "name": getattr(message, "sender", "unknown"),
                            "content": getattr(message, "content", ""),
                        }
                        chat_history.append(message_dict)
                        
                        # Check if this message contains a report
                        content = getattr(message, "content", "")
                        sender = getattr(message, "sender", "unknown")
                        if sender == "ReportWriter" and isinstance(content, str) and "#" in content:
                            logger.debug(f"Found potential report in message from {sender}")
                            # Check if content contains a markdown heading
                            lines = content.strip().split("\n")
                            for line in lines:
                                if line.strip().startswith("#"):
                                    logger.info(f"Found report with heading: {line.strip()}")
                                    context_variables["report_content"] = content
                                    break
                
                # If still no chat history, try to get it from the swarm manager
                if not chat_history and hasattr(self, "_swarm_manager") and self._swarm_manager is not None:
                    try:
                        if hasattr(self._swarm_manager, "chat_history"):
                            logger.debug("Getting chat history from swarm manager")
                            for message in self._swarm_manager.chat_history:
                                message_dict = {
                                    "role": getattr(message, "role", "unknown"),
                                    "name": getattr(message, "sender", "unknown"),
                                    "content": getattr(message, "content", ""),
                                }
                                chat_history.append(message_dict)
                                
                                # Check if this message contains a report
                                content = getattr(message, "content", "")
                                sender = getattr(message, "sender", "unknown")
                                if sender == "ReportWriter" and isinstance(content, str) and "#" in content:
                                    logger.debug(f"Found potential report in message from swarm manager: {sender}")
                                    # Check if content contains a markdown heading
                                    lines = content.strip().split("\n")
                                    for line in lines:
                                        if line.strip().startswith("#"):
                                            logger.info(f"Found report with heading: {line.strip()}")
                                            context_variables["report_content"] = content
                                            break
                    except Exception as e:
                        logger.error(f"Error getting chat history from swarm manager: {e}")
                
                # If still no report, try to directly iterate through the chat_result as a list
                if not context_variables["report_content"]:
                    logger.debug("Trying to directly iterate through chat_result as a list")
                    try:
                        # Iterate through the chat_result directly
                        for i in range(len(chat_result)):
                            try:
                                message = chat_result[i]
                                # Check if this is a message from ReportWriter
                                sender = getattr(message, "sender", None)
                                if sender == "ReportWriter":
                                    content = getattr(message, "content", "")
                                    if isinstance(content, str) and "#" in content:
                                        logger.info(f"Found report in chat_result[{i}] from ReportWriter")
                                        context_variables["report_content"] = content
                                        break
                            except (IndexError, AttributeError) as e:
                                logger.debug(f"Error accessing chat_result[{i}]: {e}")
                    except Exception as e:
                        logger.error(f"Error iterating through chat_result: {e}")
                
                # If still no report, try to extract it from the log file
                if not context_variables["report_content"]:
                    logger.debug("Trying to extract report from log file")
                    try:
                        report = self.extract_report_from_log()
                        if report:
                            logger.info("Found report in log file")
                            context_variables["report_content"] = report
                    except Exception as e:
                        logger.error(f"Error extracting report from log file: {e}")
                
                # Extract context variables
                updated_context = context_variables
                if hasattr(chat_result, "context") and chat_result.context is not None:
                    updated_context = chat_result.context
                
                # Extract last agent
                last_agent = None
                if hasattr(chat_result, "last_agent") and chat_result.last_agent is not None:
                    last_agent = chat_result.last_agent.name
                
                # Create a dictionary result
                result_dict = {
                    "chat_history": chat_history,
                    "context": updated_context,
                    "last_agent": last_agent
                }
                
                # Store the dictionary result for later use
                self._last_swarm_result = result_dict
                
                # Update status
                updated_context["status"] = "completed"
                
                # If we found a report, save it to a file
                if updated_context["report_content"]:
                    report_path = self.save_report(updated_context["report_content"])
                    result_dict["report_path"] = report_path
                    logger.info(f"Research report saved to {report_path}")
                else:
                    # Try one more time to extract report from chat history
                    report_content = self.extract_report_from_chat_history(result_dict)
                    if report_content:
                        updated_context["report_content"] = report_content
                        report_path = self.save_report(report_content)
                        result_dict["report_path"] = report_path
                        logger.info(f"Research report saved to {report_path} (extracted from chat history)")
                
                return result_dict
                
            except Exception as e:
                logger.error(f"Error processing chat result: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Return the raw chat result as a fallback
                return {
                    "chat_result": chat_result,
                    "context": context_variables,
                    "error": str(e)
                }
            
        except Exception as e:
            logger.error(f"Error in swarm chat: {e}")
            import traceback
            logger.error(traceback.format_exc())
            context_variables["status"] = "error"
            raise
            
    def extract_report_from_log(self) -> Optional[str]:
        """
        Extract the report from the log file.
        
        Returns:
            The report content if found, None otherwise
        """
        logger.debug("Extracting report from log file")
        try:
            # Check if there's a log file in the current directory
            log_files = ["research_output.log", "research_output_new.log"]
            for log_file in log_files:
                if os.path.exists(log_file):
                    logger.debug(f"Found log file: {log_file}")
                    with open(log_file, "r") as f:
                        log_content = f.read()
                    
                    # Look for the ReportWriter's message
                    report_start = log_content.find("ReportWriter (to chat_manager):")
                    if report_start != -1:
                        logger.debug(f"Found ReportWriter message at position {report_start}")
                        # Find the start of the report (# Trends in AI Assistants)
                        report_content_start = log_content.find("# Trends in AI Assistants", report_start)
                        if report_content_start != -1:
                            logger.debug(f"Found report content at position {report_content_start}")
                            # Find the end of the report (I will now transfer this report)
                            report_content_end = log_content.find("I will now transfer this report", report_content_start)
                            if report_content_end != -1:
                                logger.debug(f"Found report end at position {report_content_end}")
                                # Extract the report content
                                report_content = log_content[report_content_start:report_content_end].strip()
                                logger.info(f"Extracted report from log file: {report_content[:100]}...")
                                return report_content
            
            logger.warning("No report found in log files")
            return None
        except Exception as e:
            logger.error(f"Error extracting report from log file: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def create_agent(self, agent_class: Type, name: str, **kwargs) -> Any:
        """
        Create an agent with the given class and add it to the team.
        
        Args:
            agent_class: The agent class to instantiate
            name: Name for the agent
            **kwargs: Additional arguments to pass to the agent constructor
            
        Returns:
            The created agent instance
        """
        # Remove llm_config from kwargs if it exists to avoid conflicts
        if 'llm_config' in kwargs:
            del kwargs['llm_config']
            
        # Create the agent
        agent = agent_class(name=name, **kwargs)
        
        # Add to the team
        self.add_agent(name, agent)
        
        return agent