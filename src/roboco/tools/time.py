"""
Time Tool for Roboco

This module provides a tool for getting the current time and date.
"""

import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from roboco.core.tool import Tool
from roboco.core.logger import get_logger
from roboco.core.schema import ToolConfig


class TimeConfig(ToolConfig):
    """Configuration for TimeTool."""
    default_format: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="Default format string for datetime output"
    )
    timezone: Optional[str] = Field(
        default=None,
        description="Timezone to use (defaults to system timezone)"
    )


class TimeTool(Tool):
    """
    A tool for getting the current time and date.
    
    This tool provides a simple interface for retrieving the current time
    in various formats.
    """
    
    def __init__(self, config: Optional[TimeConfig] = None, **kwargs):
        """
        Initialize the TimeTool.
        
        Args:
            config: Configuration for the time tool
            **kwargs: Additional keyword arguments
        """
        super().__init__(config=config, **kwargs)
        
        # Initialize with config
        if config is None:
            config = TimeConfig()
        elif isinstance(config, dict):
            config = TimeConfig(**config)
            
        self.logger = get_logger(__name__)
        self.default_format = config.default_format
        self.timezone = config.timezone
        
        # Define the get_time function
        async def get_time(format_str: Optional[str] = None) -> str:
            """
            Get the current time in the specified format.
            
            Args:
                format_str: The format string for the datetime (optional)
                
            Returns:
                The current time as a formatted string
            """
            try:
                # Use provided format or default from config
                time_format = format_str or self.default_format
                
                current_time = datetime.datetime.now()
                formatted_time = current_time.strftime(time_format)
                
                self.logger.info(f"Retrieved current time: {formatted_time}")
                return formatted_time
                
            except Exception as e:
                self.logger.error(f"Error getting time: {e}")
                return f"Error: {str(e)}"
        
        # Register the get_time function
        self.register_function(
            name="get_time",
            description="Get the current time in the specified format",
            parameters={
                "format_str": {
                    "type": "string",
                    "description": f"Format string for the datetime (default: {self.default_format})",
                    "default": None
                }
            },
            func_or_tool=get_time
        )
        
        self.logger.info("Initialized TimeTool")
    
    @classmethod
    def create_with_config(cls, config: Optional[Dict[str, Any]] = None) -> "TimeTool":
        """Create a new instance of the TimeTool with the given configuration.
        
        Args:
            config: Configuration for the tool.
            
        Returns:
            A new TimeTool instance.
        """
        if config is None:
            config = {}
        return cls(config=TimeConfig(**config)) 