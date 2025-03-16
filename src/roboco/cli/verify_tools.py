#!/usr/bin/env python
"""
Tool verification script for Roboco

This script verifies all tools in the Roboco project by using the
standard tool discovery process to find and initialize them.
"""

import logging
import json
from typing import Dict, Any, Callable
import inspect
import textwrap
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("verify_tools")


def main():
    """Main entry point for the tool verification script."""
    from roboco.core.tool_factory import ToolFactory
    from roboco.core.tool import Tool
    
    print("\n=== ROBOCO TOOL VERIFICATION ===\n")
    
    # Step 1: Discover tools
    print("Step 1: Discovering tools...")
    tool_classes = ToolFactory.discover_tools()
    
    # Print discovered tools
    print(f"\nDiscovered {len(tool_classes)} tools:")
    for i, (tool_name, tool_class) in enumerate(tool_classes.items(), 1):
        module_name = tool_class.__module__
        print(f"{i}. {tool_name:<25} | {module_name}")
    
    # Step 2: Initialize tools
    print("\nStep 2: Initializing tools...")
    tools = {}
    for tool_name, tool_class in tool_classes.items():
        try:
            # Try to initialize the tool
            tool = tool_class()
            tools[tool_name] = tool
            print(f"✅ {tool_name:<25} | Successfully initialized")
        except Exception as e:
            # Log initialization errors
            print(f"❌ {tool_name:<25} | Error initializing: {e}")
            print(f"   Traceback: {traceback.format_exc().splitlines()[-3:]}")  # Show last 3 lines of traceback
    
    # Step 3: Extract functions
    print("\nStep 3: Extracting functions...")
    print()
    
    all_functions = []
    
    # For each tool, extract and print functions
    for tool_name, tool in tools.items():
        # Get function definitions
        try:
            functions = tool.get_function_definitions()
            
            # Print tool information
            print(f"📦 Tool: {tool_name}")
            print(f"   Description: {tool.description}")
            print(f"   Functions ({len(functions)}):")
            
            # Extract and print function details
            for function in functions:
                name = function.get("name", "No name")
                description = function.get("description", "No description")
                
                # Print function name and description
                print(f"   - {name:<20} | {description}")
                
                # Print full description if available
                print(f"     Full Description: {description}")
                
                # Print parameters if available
                parameters = function.get("parameters", {}).get("properties", {})
                if parameters:
                    print(f"     Parameters:")
                    
                    # Calculate the maximum length of parameter names for alignment
                    max_param_length = max([len(param) for param in parameters.keys()], default=10)
                    
                    for param_name, param_info in parameters.items():
                        param_type = param_info.get("type", "unknown")
                        param_desc = param_info.get("description", "No description")
                        
                        # Format the parameter description to wrap at 80 characters
                        wrapped_desc = textwrap.fill(
                            param_desc, 
                            width=40, 
                            initial_indent="",
                            subsequent_indent=" " * (max_param_length + 15)
                        )
                        
                        # Print parameter information
                        print(f"     • {param_name:<{max_param_length}} | {param_type:<10} | {wrapped_desc}")
                        
                        # If there's an enum, print allowed values
                        if "enum" in param_info:
                            enum_values = param_info["enum"]
                            enum_str = ", ".join([f"'{val}'" for val in enum_values])
                            print(f"       Allowed values: {enum_str}")
                
                # Add function to the list of all functions
                all_functions.append(name)
            
            print()
            
        except Exception as e:
            print(f"❌ Error extracting functions from {tool_name}: {e}")
            print(f"   Traceback: {traceback.format_exc().splitlines()[-3:]}")
    
    # Step 4: Create function map
    print("Step 4: Creating function map...")
    function_map = ToolFactory.create_function_map(tools)
    
    # Print function map
    print(f"Created function map with {len(function_map)} functions:")
    for i, function_name in enumerate(sorted(function_map.keys()), 1):
        print(f"{i}. {function_name}")
    
    # Print diagnostic information about environment variables
    print("\nStep 5: Environment Diagnostics...")
    
    # Check for important environment variables
    env_vars = {
        "OPENAI_API_KEY": "Required for LLM functionality",
        "TAVILY_API_KEY": "Required for WebSearchTool",
        "PYTHONPATH": "Python module search path"
    }
    
    for var_name, description in env_vars.items():
        value = os.environ.get(var_name)
        if value:
            # Mask API keys for security
            if "API_KEY" in var_name:
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                print(f"✅ {var_name:<20} | Set ({masked_value}) - {description}")
            else:
                print(f"✅ {var_name:<20} | Set - {description}")
        else:
            if "API_KEY" in var_name:
                print(f"❌ {var_name:<20} | Not set - {description}")
            else:
                print(f"ℹ️ {var_name:<20} | Not set - {description}")
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"✓ Discovered {len(tool_classes)} tools")
    print(f"✓ Successfully initialized {len(tools)} tools")
    print(f"✓ Extracted {len(all_functions)} functions")
    print(f"✓ Created function map with {len(function_map)} functions")
    
    print("\n=== VERIFICATION COMPLETE ===")


if __name__ == "__main__":
    main()
