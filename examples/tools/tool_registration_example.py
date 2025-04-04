#!/usr/bin/env python3
"""
Tool parameter handling example.

This example demonstrates how different parameter formats are handled by the FileSystemTool,
testing the fixes we've made for parameter processing in the Tool class.
"""

import logging
import os
import sys
import json
from typing import Dict, Any

# Add the project directory to the path so we can import roboco modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.tools.fs import FileSystemTool
from roboco.core.fs import ProjectFS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the tool parameter handling example."""
    logger.info("Starting tool parameter handling example...")
    
    # Create a temporary directory for file operations
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data/tool_registration_test"))
    os.makedirs(test_dir, exist_ok=True)
    
    # Initialize ProjectFS with the test directory path directly since it's an absolute path
    project_fs = ProjectFS(project_id=test_dir)
    
    # Initialize FileSystemTool
    fs_tool = FileSystemTool(fs=project_fs)
    logger.info(f"Initialized FileSystemTool with commands: {', '.join(fs_tool.commands.keys())}")
    
    # Print detailed command registration information
    logger.info(f"\nTool Registration Details:")
    logger.info(f"Tool name: {fs_tool.name}")
    logger.info(f"Tool description: {fs_tool.description}")
    
    # Debug internal attributes
    if hasattr(fs_tool, '_name'):
        logger.info(f"Internal _name attribute: {fs_tool._name}")
    if hasattr(fs_tool, '_description'):
        logger.info(f"Internal _description attribute: {fs_tool._description}")
    
    # Additional attribute checks
    for attr in dir(fs_tool):
        if not attr.startswith('__') and not callable(getattr(fs_tool, attr)):
            if attr not in ['commands', 'fs', 'description', 'registered_with_agents']:  # Skip large attributes
                logger.info(f"Attribute {attr}: {getattr(fs_tool, attr)}")
    
    # Print the command descriptions and parameters in a more readable format
    logger.info(f"\nTool Commands:")
    for command_name in fs_tool.commands:
        logger.info(f"  - {command_name}")
    
    # Print detailed information about each command
    logger.info(f"\nDetailed Command Information:")
    for cmd_name, cmd_func in fs_tool.commands.items():
        # Get the function signature
        import inspect
        sig = inspect.signature(cmd_func)
        params = [f"{name}: {param.annotation.__name__ if hasattr(param.annotation, '__name__') else str(param.annotation).replace('typing.', '')}" 
                 for name, param in sig.parameters.items()]
        
        # Get the command description from docstring
        doc = cmd_func.__doc__ or "No documentation available"
        doc_first_line = doc.strip().split('\n')[0]
        
        logger.info(f"\n  Command: {cmd_name}")
        logger.info(f"  Parameters: {', '.join(params)}")
        logger.info(f"  Description: {doc_first_line}")
        logger.info(f"  Function: {cmd_func.__qualname__}")
    
    logger.info(f"\nTesting tool execution with different parameter formats...")
    
    # Test 1: Direct parameter passing
    try:
        logger.info("Test 1: Direct parameter passing")
        test_file_1 = os.path.join(test_dir, "test1.txt")
        result = fs_tool.execute_command(
            command="save_file",
            content="Hello, world!",
            file_path=test_file_1
        )
        logger.info(f"Result: {result}")
        logger.info(f"File created: {os.path.exists(test_file_1)}")
    except Exception as e:
        logger.error(f"Test 1 failed: {e}")
    
    # Test 2: Nested args format (simulating AutoGen's parameter passing)
    try:
        logger.info("Test 2: Nested args format")
        test_file_2 = os.path.join(test_dir, "test2.txt")
        result = fs_tool.execute_command(
            command="save_file",
            args={
                "content": "Hello from nested args!",
                "file_path": test_file_2
            }
        )
        logger.info(f"Result: {result}")
        logger.info(f"File created: {os.path.exists(test_file_2)}")
    except Exception as e:
        logger.error(f"Test 2 failed: {e}")
    
    # Test 3: Nested kwargs format
    try:
        logger.info("Test 3: Nested kwargs format")
        test_file_3 = os.path.join(test_dir, "test3.txt")
        result = fs_tool.execute_command(
            command="save_file",
            kwargs={
                "content": "Hello from nested kwargs!",
                "file_path": test_file_3
            }
        )
        logger.info(f"Result: {result}")
        logger.info(f"File created: {os.path.exists(test_file_3)}")
    except Exception as e:
        logger.error(f"Test 3 failed: {e}")
    
    # Test 4: Dictionary argument (simulating how AutoGen might call it)
    try:
        logger.info("Test 4: Dictionary argument")
        test_file_4 = os.path.join(test_dir, "test4.txt")
        result = fs_tool.execute_command({
            "command": "save_file",
            "args": {
                "content": "Hello from dictionary argument!",
                "file_path": test_file_4
            }
        })
        logger.info(f"Result: {result}")
        logger.info(f"File created: {os.path.exists(test_file_4)}")
    except Exception as e:
        logger.error(f"Test 4 failed: {e}")
    
    # Test 5: Both args and kwargs nested format
    try:
        logger.info("Test 5: Both args and kwargs nested format")
        test_file_5 = os.path.join(test_dir, "test5.txt")
        result = fs_tool.execute_command(
            command="save_file", 
            args={"content": "Content from args"}, 
            kwargs={"file_path": test_file_5}
        )
        logger.info(f"Result: {result}")
        logger.info(f"File created: {os.path.exists(test_file_5)}")
    except Exception as e:
        logger.error(f"Test 5 failed: {e}")
    
    # Test 6: Single dictionary with combined args/kwargs fields (complex AutoGen format)
    try:
        logger.info("Test 6: Single dictionary with args/kwargs fields")
        test_file_6 = os.path.join(test_dir, "test6.txt")
        result = fs_tool.execute_command({
            "args": ["save_file"],
            "kwargs": {
                "content": "Hello from complex format!",
                "file_path": test_file_6
            }
        })
        logger.info(f"Result: {result}")
        logger.info(f"File created: {os.path.exists(test_file_6)}")
    except Exception as e:
        logger.error(f"Test 6 failed: {e}")
    
    # Print summary
    logger.info("\nSummary of test results:")
    for i in range(1, 7):
        test_file = os.path.join(test_dir, f"test{i}.txt")
        exists = os.path.exists(test_file)
        logger.info(f"Test {i}: {'SUCCESS' if exists else 'FAILED'} - {test_file}")
    
    logger.info("Tool parameter handling example completed.")

if __name__ == "__main__":
    main()
