"""
Base Tool Module

This module defines the base Tool class that all specialized tools inherit from.
Tools are designed to be compatible with AG2's function calling mechanism.
"""

from typing import Dict, Any, List, Optional, Callable
from loguru import logger

class Tool:
    """Base class for all tools that can be used by agents."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize the tool.
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
        """
        self.name = name
        self.description = description
    
    def get_functions(self) -> Dict[str, Callable]:
        """
        Get a dictionary of the tool's functions.
        
        Returns:
            Dictionary mapping function names to callables
        """
        # Get all public methods of the class
        functions = {}
        
        for attr_name in dir(self):
            # Skip special methods, private methods, and known non-function attributes
            if (attr_name.startswith('_') or 
                attr_name in ['name', 'description', 'get_functions']):
                continue
                
            attr = getattr(self, attr_name)
            if callable(attr):
                function_name = f"{self.name}_{attr_name}"
                functions[function_name] = attr
                
        return functions
