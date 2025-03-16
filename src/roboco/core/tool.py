"""
Tool Module

This module defines the base Tool class that all specialized tools inherit from.
Tools are designed to be compatible with AG2's function calling mechanism.
"""

from typing import Dict, Any, Callable, Optional, List
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
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """
        Get definitions for all functions provided by this tool.
        
        Override this method in subclasses to provide custom function definitions.
        
        Returns:
            List of function definitions, each containing:
            - name: Function name
            - function: The callable function
            - description: Function description
            - parameters: Function parameters schema
        """
        # Default implementation: extract public methods
        definitions = []
        
        for attr_name in dir(self):
            # Skip special methods, private methods, and known non-function attributes
            if (attr_name.startswith('_') or 
                attr_name in ['name', 'description', 'get_function_definitions']):
                continue
                
            attr = getattr(self, attr_name)
            if callable(attr):
                # Extract description from docstring
                docstring = attr.__doc__ or f"Function {attr_name} from {self.name} tool"
                description = docstring.strip().split('\n')[0]  # First line of docstring
                
                # Create a simple parameters schema
                # Tools should override this method to provide proper schemas
                parameters = {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
                
                definitions.append({
                    'name': attr_name,
                    'function': attr,
                    'description': description,
                    'parameters': parameters
                })
                
        return definitions
