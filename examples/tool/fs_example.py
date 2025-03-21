#!/usr/bin/env python
"""
File System Tool Example

This example demonstrates how to use the FileSystemTool with dynamic command registration.
It shows basic file operations like creating, reading, and listing files.
It also showcases the new enhanced tool description generation feature.
"""

import os
import sys
import asyncio
from pathlib import Path
from loguru import logger

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.tools.fs import FileSystemTool

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

async def main():
    """Test the FileSystemTool with various file operations."""
    # Create test directory
    test_dir = Path("examples/tool/data")
    if not test_dir.exists():
        test_dir.mkdir(parents=True)
        logger.info(f"Created test directory: {test_dir}")
    
    # Initialize the FileSystemTool
    logger.info("\n=== FileSystemTool with Enhanced Description Generation ===")
    logger.info("This example demonstrates the new auto-generated rich tool descriptions.")
    logger.info("These descriptions help LLMs better understand how to use tools with multiple commands.")
    fs_tool = FileSystemTool()
    logger.info(f"Available commands: {', '.join(fs_tool.commands.keys())}")
    
    # Display the auto-generated tool description
    logger.info("\n=== Auto-generated Tool Description ===")
    if hasattr(fs_tool, '_description'):
        description = fs_tool._description
    else:
        description = fs_tool.description
    
    # Print the description with proper formatting
    for line in description.split('\n'):
        logger.info(line)
    
    # Create test files
    test_files = {
        "hello.txt": "Hello, World!",
        "data.json": '{"name": "Test Data", "values": [1, 2, 3, 4, 5]}',
        "note.md": "# Test Note\n\nThis is a test note created by the FileSystemTool."
    }
    
    # Test save_file command
    logger.info("\n=== Testing save_file command ===")
    for filename, content in test_files.items():
        file_path = test_dir / filename
        result = fs_tool.execute_command(
            command="save_file",
            content=content,
            file_path=str(file_path)
        )
        logger.info(f"Saved {filename}: {result}")
    
    # Test list_directory command
    logger.info("\n=== Testing list_directory command ===")
    result = fs_tool.execute_command(
        command="list_directory",
        directory_path=str(test_dir)
    )
    
    if result["success"]:
        logger.info(f"Directory contents ({result['count']} items):")
        for item in result["contents"]:
            logger.info(f" - {item['name']} ({item['type']})")
    else:
        logger.error(f"Failed to list directory: {result['error']}")
    
    # Test read_file command
    logger.info("\n=== Testing read_file command ===")
    for filename in test_files.keys():
        file_path = test_dir / filename
        result = fs_tool.execute_command(
            command="read_file",
            file_path=str(file_path)
        )
        
        if result["success"]:
            # Truncate content if too long
            content = result["content"]
            if len(content) > 100:
                content = content[:97] + "..."
            logger.info(f"Read {filename}: {content}")
        else:
            logger.error(f"Failed to read {filename}: {result['error']}")
    
    # Test primary command (default command when none specified)
    logger.info("\n=== Testing primary command ===")
    # First, let's find out what the primary command is
    primary_command = fs_tool.primary_command
    logger.info(f"Primary command is: {primary_command}")
    
    # Now test it with appropriate parameters
    if primary_command == "save_file":
        primary_file = test_dir / "primary_test.txt"
        result = fs_tool.execute_command(
            content="This file was created using the primary command.",
            file_path=str(primary_file)
        )
        logger.info(f"Primary command result: {result}")
    elif primary_command == "read_file":
        # Pick an existing file to read
        primary_file = test_dir / "hello.txt"
        result = fs_tool.execute_command(
            file_path=str(primary_file)
        )
        logger.info(f"Primary command result: {result}")
    elif primary_command == "list_directory":
        result = fs_tool.execute_command(
            directory_path=str(test_dir)
        )
        logger.info(f"Primary command result: {result}")
    else:
        logger.warning(f"Unexpected primary command: {primary_command}, skipping test")
    
    # Test error handling
    logger.info("\n=== Testing error handling ===")
    
    # Non-existent command
    try:
        result = fs_tool.execute_command(
            command="delete_file",  # This command doesn't exist
            file_path=str(primary_file)
        )
    except ValueError as e:
        logger.info(f"Expected error (non-existent command): {e}")
    
    # Missing parameters
    try:
        result = fs_tool.execute_command(
            command="save_file"  # Missing required parameters
        )
    except Exception as e:
        logger.info(f"Expected error (missing parameters): {e}")
    
    # Non-existent file
    result = fs_tool.execute_command(
        command="read_file",
        file_path=str(test_dir / "non_existent.txt")
    )
    logger.info(f"Non-existent file result: {result}")
    
    # Add an LLM prompt example
    logger.info("\n=== Example LLM prompt with enhanced tool description ===")
    logger.info("This shows how much easier it is for LLMs to use tools with enhanced descriptions")
    llm_prompt = f"""
    You have access to the {fs_tool.name} tool with the following description:
    
    {description}
    
    Use the tool to:
    1. Create a file named 'test_prompt.txt' with the content "This file was created via an LLM prompt"
    2. List the contents of the directory
    3. Read the newly created file
    """
    
    for line in llm_prompt.split('\n'):
        logger.info(line)
    
    # Highlight key description features
    logger.info("\n=== Key Enhanced Description Features ===")
    logger.info("The new description generator automatically provides:")
    logger.info("1. Detailed command signatures with parameter types and defaults")
    logger.info("2. Comprehensive parameter descriptions from docstrings")
    logger.info("3. Clear return value information")
    logger.info("4. Primary command indication")
    logger.info("5. Usage examples for each command")
    logger.info("6. Overall guidance on how to use commands")
    logger.info(f"Description size: {len(description)} characters")
    logger.info("\nEnhanced descriptions like this make it much easier for LLMs")
    logger.info("to correctly use tools with multiple commands without guessing.")
    
    logger.info("\n=== Test completed successfully ===")
    logger.info("Files are kept in examples/tool/data for inspection.")
    logger.info("You can delete them manually if needed.")

if __name__ == "__main__":
    asyncio.run(main())