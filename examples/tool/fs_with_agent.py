#!/usr/bin/env python
"""
File System Tool with Agent Example

This example demonstrates how to use the FileSystemTool with Roboco agents.
It shows how to register tool commands with an agent and have the agent use them
for file system operations.
"""

import os
import sys
import asyncio
from pathlib import Path
from loguru import logger

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.tools.fs import FileSystemTool
from roboco.core.agent import Agent
from roboco.agents.human import HumanProxy

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

async def main():
    """Test the FileSystemTool with Roboco agents."""
    # Create test directory
    test_dir = Path("examples/tool/agent_data")
    if not test_dir.exists():
        test_dir.mkdir(parents=True)
        logger.info(f"Created test directory: {test_dir}")
    
    # Initialize the FileSystemTool
    fs_tool = FileSystemTool()
    logger.info(f"Initialized FileSystemTool with commands: {', '.join(fs_tool.commands.keys())}")
    
    # Initialize the assistant agent
    fs_assistant = Agent(
        name="file_system_assistant",
        terminate_msg="\n\n=== End of conversation ===",
        system_message="""
        You are a helpful assistant with file management capabilities.
        You can create, read, and list files and directories.
        When asked to perform a file operation, use the appropriate file system command.
        """
    )
    
    # Initialize the human proxy agent (for automated testing, we'll set human_input_mode to NEVER)
    human = HumanProxy(
        name="user",
        terminate_msg="\n\n=== End of conversation ===",
        human_input_mode="NEVER"
    )
    
    # Register tool commands with the assistant
    logger.info("\n=== Registering FileSystemTool with assistant ===")
    fs_tool.register_with_agents(fs_assistant, human)
    
    # Prepare file paths for the agent to use
    notes_file = str(test_dir / "meeting_notes.md")
    todo_file = str(test_dir / "todo.txt")
    config_file = str(test_dir / "config.json")
    
    # Function to run a task with the agents
    def run_task(description, message):
        logger.info(f"\n=== {description} ===")
        # Start a chat between the human and assistant
        human.initiate_chat(
            fs_assistant,
            message=message
        )
    
    # Task 1: Create a markdown file with meeting notes
    run_task(
        "Task 1: Creating meeting notes file",
        f"""
        Please create a markdown file with meeting notes at {notes_file}.
        Include the following sections:
        - Attendees
        - Agenda
        - Action Items
        - Next Meeting
        
        Fill in some example content for each section.
        """
    )
    
    # Task 2: Create a todo list file
    run_task(
        "Task 2: Creating todo list file",
        f"""
        Please create a todo list at {todo_file} with the following items:
        1. Complete project proposal
        2. Review code changes
        3. Set up meeting with the team
        4. Update documentation
        5. Prepare for demo
        """
    )
    
    # Task 3: Create a JSON configuration file
    run_task(
        "Task 3: Creating JSON configuration file",
        f"""
        Please create a JSON configuration file at {config_file} with the following content:
        {{
            "appName": "FileSystem Demo",
            "version": "1.0.0",
            "settings": {{
                "theme": "dark",
                "fontSize": 14,
                "enableNotifications": true
            }},
            "plugins": ["fs", "search", "editor"]
        }}
        """
    )
    
    # Task 4: List files in the directory
    run_task(
        "Task 4: Listing files in the directory",
        f"""
        Please list all files in the directory {test_dir}.
        For each file, tell me its name and type.
        """
    )
    
    # Task 5: Read and summarize the meeting notes
    run_task(
        "Task 5: Reading and summarizing the meeting notes",
        f"""
        Please read the meeting notes from {notes_file} and provide a brief summary
        of the key points and action items.
        """
    )
    
    # Task 6: Update the todo list
    run_task(
        "Task 6: Updating the todo list",
        f"""
        Please read the current todo list from {todo_file}, then update it by:
        1. Marking the first item as complete with "[x]"
        2. Adding a new item: "Send progress report to manager"
        Save the updated todo list back to the same file.
        
        After you've completed this task, let me know the todo list has been updated.
        """
    )
    
    logger.info("\n=== Example completed successfully ===")
    logger.info(f"Files are available for inspection in {test_dir}")
    logger.info("You can delete them manually if needed.")

if __name__ == "__main__":
    asyncio.run(main()) 