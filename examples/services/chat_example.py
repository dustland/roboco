#!/usr/bin/env python
"""
Chat API Example

This example demonstrates how to use the chat API to process a query,
which will generate and execute tasks using the VersatileTeam.
"""

import os
import sys
import asyncio
import argparse
from typing import Dict, Any, Optional

# Add parent directory to path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Initialize logging with default settings first
from loguru import logger
logger.info("Starting chat example application...")

# Import core configuration
from roboco.core.config import load_config
from roboco.core.logger import load_config_settings

# After importing configuration modules, load logging settings from config
logger.info("Loading configuration...")
config = load_config()
load_config_settings()  # Configure logging based on config.yaml

# Now it's safe to import service modules
from roboco.services.project_service import ProjectService
from roboco.services.api_service import ApiService
from roboco.core.models.chat import ChatRequest

logger.info("All modules imported successfully")


async def start_chat(query: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a query to the chat API and process the response.
    
    Args:
        query: The user's query to process
        conversation_id: Optional ID to continue an existing conversation
        
    Returns:
        The response from the chat API
    """
    # Create the domain service
    project_service = ProjectService()
    
    # Create the API service
    api_service = ApiService(project_service)
    
    # Create the chat request
    chat_request = ChatRequest(
        query=query,
        teams=["versatile"],
        conversation_id=conversation_id
    )
    
    # Process the chat request
    print(f"Sending query: '{query}'")
    print("This will plan the project and execute tasks using VersatileTeam...")
    print("Please wait, this may take a few minutes...")
    
    # Send the request
    logger.info(f"Processing chat request: {query}")
    response = await api_service.start_chat(chat_request)
    logger.info("Chat request processed successfully")
    
    return response


async def run_example(query: str):
    """Run the chat API example."""
    print("=" * 80)
    print("  Chat API Example")
    print("=" * 80)
    print("This example demonstrates how to use the chat API to process a query,")
    print("which will generate and execute tasks using the VersatileTeam.")
    print("=" * 80)
    
    # Process the query
    response = await start_chat(query)
    
    # Display the response
    print("\n" + "=" * 80)
    print("  Response")
    print("=" * 80)
    print(f"Conversation ID: {response.conversation_id}")
    if response.project_id:
        print(f"Project ID: {response.project_id}")
    print(f"Status: {response.status}")
    print("\nMessage:")
    print("-" * 40)
    print(response.message)
    print("-" * 40)
    
    # If a project was created, show its details
    if response.project_details:
        print("\nProject Details:")
        for key, value in response.project_details.items():
            print(f"  {key}: {value}")
    
    print("\nYou can continue this conversation by providing the conversation ID:")
    print(f"python examples/services/chat_example.py --id {response.conversation_id} --query \"Tell me more about the project\"")
    
    # Return the conversation ID for potential continued conversation
    return response.conversation_id


async def continue_conversation(conversation_id: str, query: str):
    """Continue an existing conversation."""
    print("=" * 80)
    print("  Continuing Conversation")
    print("=" * 80)
    print(f"Conversation ID: {conversation_id}")
    print(f"Query: {query}")
    print("=" * 80)
    
    # Process the query
    response = await start_chat(query, conversation_id)
    
    # Display the response
    print("\n" + "=" * 80)
    print("  Response")
    print("=" * 80)
    print(f"Status: {response.status}")
    print("\nMessage:")
    print("-" * 40)
    print(response.message)
    print("-" * 40)
    
    # Return the conversation ID for potential continued conversation
    return response.conversation_id


def main():
    parser = argparse.ArgumentParser(description="Chat API Example")
    parser.add_argument("--query", "-q", type=str, default="Create a simple web crawler that can download and save webpage content",
                      help="Query to process")
    parser.add_argument("--id", type=str, help="Conversation ID to continue")
    
    args = parser.parse_args()
    
    if not args.query:
        parser.error("Please provide a query with --query")
        return
    
    # Run the async example
    if args.id:
        asyncio.run(continue_conversation(args.id, args.query))
    else:
        asyncio.run(run_example(args.query))


if __name__ == "__main__":
    main() 