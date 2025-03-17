"""
Tool Base Class for Roboco

This module provides a base class for tools in the Roboco system.
It wraps autogen.tools.Tool to provide a consistent interface for all Roboco tools.
"""

from typing import Any, Callable, Dict, Optional
from loguru import logger

from autogen.tools import Tool as AutogenTool


class Tool(AutogenTool):
    """
    Base class for all Roboco tools.
    
    This is a thin wrapper around autogen.tools.Tool that provides a consistent
    interface for all Roboco tools and adds Roboco-specific functionality.
    
    Example:
        ```python
        class MyTool(Tool):
            def __init__(self, param1: str = "default"):
                # Define the function to be called when the tool is invoked
                def my_function(query: str) -> str:
                    '''
                    Process a query.
                    
                    Args:
                        query: The query to process
                        
                    Returns:
                        The processed result
                    '''
                    # Implementation using self.param1
                    return f"Processed {query} with {self.param1}"
                
                # Initialize instance variables
                self.param1 = param1
                
                # Initialize the Tool parent class with the function
                super().__init__(
                    name="my_function",
                    description="Process a query with MyTool",
                    func_or_tool=my_function
                )
        ```
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        func_or_tool: Callable,
        **kwargs
    ):
        """
        Initialize the Tool.
        
        Args:
            name: The name of the tool
            description: A description of what the tool does
            func_or_tool: The function to be called when the tool is invoked
            **kwargs: Additional arguments to pass to the parent class
        """
        super().__init__(
            name=name,
            description=description,
            func_or_tool=func_or_tool,
            **kwargs
        )
        logger.debug(f"Initialized {self.__class__.__name__} tool")
    
    def register_with_agents(self, caller_agent: Any, executor_agent: Any) -> None:
        """
        Register this tool with a caller agent and an executor agent.
        
        This follows AG2's pattern of having a caller agent (that suggests the tool)
        and an executor agent (that executes the tool).
        
        Args:
            caller_agent: The agent that will suggest using the tool
            executor_agent: The agent that will execute the tool
        """
        try:
            # Register the tool with both agents
            self.register_for_llm(caller_agent)
            self.register_for_execution(executor_agent)
            
            # Check if the function was registered correctly
            if hasattr(executor_agent, "_function_map") and self.name in executor_agent._function_map:
                logger.debug(f"{self.name} function successfully registered with executor agent")
            else:
                logger.warning(f"{self.name} function not found in executor_agent._function_map after registration")
                
            logger.info(f"Registered {self.name} from {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error registering {self.name}: {e}")
