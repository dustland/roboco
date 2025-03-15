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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("verify_tools")


def main():
    """Verify all tools in the Roboco project."""
    print("\n=== ROBOCO TOOL VERIFICATION ===\n")
    
    # Import tool factory
    from roboco.core.tool_factory import ToolFactory
    from roboco.core.tool import Tool
    
    # Discover all tools
    print("Step 1: Discovering tools...")
    tools = ToolFactory.discover_tools()
    
    if not tools:
        print("❌ No tools were discovered.")
        return
    
    print(f"\nDiscovered {len(tools)} tools:")
    for i, (name, tool_class) in enumerate(tools.items(), 1):
        module_name = tool_class.__module__
        print(f"{i}. {name:<25} | {module_name}")
    
    # Initialize tools
    print("\nStep 2: Initializing tools...")
    tool_instances = {}
    for name, tool_class in tools.items():
        try:
            tool_instances[name] = tool_class()
            print(f"✅ {name:<25} | Successfully initialized")
        except Exception as e:
            print(f"❌ {name:<25} | Failed to initialize: {e}")
    
    # Extract functions from tools
    print("\nStep 3: Extracting functions...")
    all_functions = {}
    
    for name, tool in tool_instances.items():
        try:
            functions = tool.get_functions()
            print(f"\n📦 Tool: {name}")
            print(f"   Description: {tool.description}")
            print(f"   Functions ({len(functions)}):")
            
            # Get function descriptions with parameters
            function_descriptions = tool.get_function_descriptions()
            
            for func_name, func in functions.items():
                # Get description from function docstring
                doc = func.__doc__ or "No description"
                short_doc = doc.strip().split('\n')[0]
                print(f"   - {func_name:<20} | {short_doc}")
                
                # Print parameters if available in function descriptions
                if func_name in function_descriptions:
                    func_desc = function_descriptions[func_name]
                    if "parameters" in func_desc and "properties" in func_desc["parameters"]:
                        params = func_desc["parameters"]["properties"]
                        if params:
                            print(f"     Parameters:")
                            for param_name, param_info in params.items():
                                param_type = param_info.get("type", "any")
                                param_desc = param_info.get("description", "No description")
                                
                                # Wrap long descriptions
                                wrapped_desc = textwrap.fill(
                                    param_desc, 
                                    width=70, 
                                    initial_indent="     • " + f"{param_name:<15} | {param_type:<10} | ",
                                    subsequent_indent="       " + " " * 28
                                )
                                print(wrapped_desc)
                
                # Add to all functions
                all_functions[f"{name}.{func_name}"] = func
        except Exception as e:
            print(f"❌ Error extracting functions from {name}: {e}")
    
    # Create function map
    print(f"\nStep 4: Creating function map...")
    function_map = ToolFactory.create_function_map(
        tool_names=list(tool_instances.keys()),
        tool_instances=tool_instances
    )
    
    print(f"Created function map with {len(function_map)} functions:")
    for i, func_name in enumerate(sorted(function_map.keys()), 1):
        print(f"{i}. {func_name}")
    
    # Summary
    print("\n=== SUMMARY ===")
    print(f"✓ Discovered {len(tools)} tools")
    print(f"✓ Successfully initialized {len(tool_instances)} tools")
    total_functions = sum(len(tool.get_functions()) for tool in tool_instances.values())
    print(f"✓ Extracted {total_functions} functions")
    print(f"✓ Created function map with {len(function_map)} functions")
    
    print("\n=== VERIFICATION COMPLETE ===")


if __name__ == "__main__":
    main()
