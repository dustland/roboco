"""
Time Tool for Roboco

This module provides a tool for getting the current time and date.
"""

import datetime
from loguru import logger

from roboco.core.tool import Tool


class TimeTool(Tool):
    """
    A tool for getting the current time and date.
    
    This tool provides a simple interface for retrieving the current time
    in various formats.
    """
    
    def __init__(self):
        """
        Initialize the TimeTool.
        """
        # Define the get_time function
        def get_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
            """
            Get the current time in the specified format.
            
            Args:
                format_str: The format string for the datetime (default: "%Y-%m-%d %H:%M:%S")
                
            Returns:
                The current time as a formatted string
            """
            try:
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime(format_str)
                logger.info(f"Retrieved current time: {formatted_time}")
                return formatted_time
            except Exception as e:
                logger.error(f"Error getting time: {e}")
                return f"Error: {str(e)}"
        
        # Initialize the Tool parent class with the get_time function
        super().__init__(
            name="get_time",
            description="Get the current time in the specified format",
            func_or_tool=get_time
        )
        
        logger.info("Initialized TimeTool") 