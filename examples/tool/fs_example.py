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
from roboco.domain.models.project_manifest import ProjectManifest, ProjectFile

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
    logger.info("\n=== FileSystemTool with Command Decorator Pattern ===")
    logger.info("This example demonstrates the new command decorator pattern for tool methods.")
    logger.info("Methods marked with @command are automatically registered as commands.")
    fs_tool = FileSystemTool()
    logger.info(f"Available commands: {', '.join(fs_tool.commands.keys())}")
    logger.info(f"Primary command: {fs_tool.primary_command}")
    
    # Display the auto-generated tool description
    logger.info("\n=== Auto-generated Tool Description ===")
    logger.info(fs_tool.description)
    
    # Create test files
    logger.info("\n=== Testing File Operations ===")
    
    # Test save_file (primary command)
    test_file = test_dir / "test.txt"
    result = fs_tool.execute_command(
        command="save_file",
        content="This is a test file created by the FileSystemTool.",
        file_path=str(test_file)
    )
    logger.info(f"save_file result: {result}")
    
    # Test read_file
    result = fs_tool.execute_command(
        command="read_file",
        file_path=str(test_file)
    )
    logger.info(f"read_file result: {result}")
    
    # Test list_directory
    result = fs_tool.execute_command(
        command="list_directory",
        directory_path=str(test_dir)
    )
    logger.info(f"list_directory result: {result}")
    
    # Test create_directory
    nested_dir = test_dir / "nested"
    result = fs_tool.execute_command(
        command="create_directory",
        directory_path=str(nested_dir)
    )
    logger.info(f"create_directory result: {result}")
    
    # Test primary command (without specifying command name)
    test_file2 = test_dir / "primary_command_test.txt"
    result = fs_tool.execute_command(
        content="This file was created using the primary command (without specifying command name).",
        file_path=str(test_file2)
    )
    logger.info(f"Primary command result: {result}")
    
    # Test ProjectManifest with execute_project_manifest
    logger.info("\n=== Testing ProjectManifest with Pydantic Models ===")
    
    # Create a test manifest using Pydantic models
    manifest = ProjectManifest(
        name="test-project",
        directories=["examples/tool/data/project/src", "examples/tool/data/project/docs"],
        files=[
            ProjectFile(
                path="examples/tool/data/project/README.md",
                content="# Test Project\n\nThis project was created using the ProjectManifest model."
            ),
            ProjectFile(
                path="examples/tool/data/project/src/main.py",
                content="print('Hello from the test project!')"
            ),
            ProjectFile(
                path="examples/tool/data/project/docs/index.md",
                content="# Documentation\n\nThis is the documentation for the test project."
            )
        ]
    )
    
    # Execute the project manifest
    result = fs_tool.execute_command(
        command="execute_project_manifest",
        manifest=manifest,
        base_path=""  # Use empty string as base path since paths in manifest are already relative
    )
    logger.info(f"execute_project_manifest result: {result}")
    
    # Test with dictionary input (backward compatibility)
    manifest_dict = {
        "name": "dict-project",
        "directories": ["examples/tool/data/dict_project/src"],
        "files": [
            {
                "path": "examples/tool/data/dict_project/README.md",
                "content": "# Dict Project\n\nThis project was created using a dictionary input."
            }
        ]
    }
    
    result = fs_tool.execute_command(
        command="execute_project_manifest",
        manifest=manifest_dict,
        base_path=""
    )
    logger.info(f"execute_project_manifest with dict result: {result}")
    
    logger.info("\n=== All tests completed successfully ===")

if __name__ == "__main__":
    asyncio.run(main())