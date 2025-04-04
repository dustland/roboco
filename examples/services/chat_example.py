#!/usr/bin/env python
"""
Chat API Example

This example demonstrates how to use the chat API to process a query,
which will generate and execute tasks using the VersatileTeam.
It also shows how to track the status of ongoing conversations.
"""

import os
import sys
import asyncio
import argparse
import time
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

# Now it's safe to import service modules directly
from roboco.services.chat_service import ChatService
from roboco.core.models.chat import ChatRequest
from roboco.utils import generate_short_id

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
    # Create the chat service directly
    chat_service = ChatService()
    
    # Create the chat request
    chat_request = ChatRequest(
        query=query,
        task_id=None  # Not using task_id as it's not in the example's parameters
    )
    
    # Process the chat request
    print(f"Sending query: '{query}'")
    print("This will plan the project and execute tasks using VersatileTeam...")
    print("Please wait, this may take a few minutes...")
    
    # Send the request
    logger.info(f"Processing chat request: {query}")
    response = await chat_service.start_chat(chat_request)
    logger.info("Chat request processed successfully")
    
    return response


async def check_chat_status(conversation_id: str) -> Dict[str, Any]:
    """
    Check the status of a chat conversation.
    
    Args:
        conversation_id: ID of the conversation to check
        
    Returns:
        The status response from the chat API
    """
    # Create the chat service directly
    chat_service = ChatService()
    
    # Get conversation status
    print(f"Checking status for conversation: {conversation_id}")
    
    # Get the status
    logger.info(f"Getting status for conversation: {conversation_id}")
    response = await chat_service.get_conversation_status(conversation_id)
    
    if not response:
        # Try getting the conversation history
        history = await chat_service.get_conversation_history(conversation_id)
        if not history:
            logger.error(f"Conversation {conversation_id} not found")
            print(f"Conversation {conversation_id} not found")
            return {"status": "not_found", "conversation_id": conversation_id}
        
        # Return basic info from history
        return {
            "conversation_id": history.conversation_id,
            "status": history.status,
            "message": history.messages[-1].content if history.messages else "",
            "created_at": history.created_at,
            "updated_at": history.updated_at
        }
    
    logger.info(f"Got status for conversation: {conversation_id}")
    return response.dict() if hasattr(response, 'dict') else response


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
    print(f"python roboco/examples/services/chat_example.py --id {response.conversation_id} --query \"Tell me more about the project\"")
    print(f"Or check the status of this conversation with:")
    print(f"python roboco/examples/services/chat_example.py --id {response.conversation_id} --check-status")
    print(f"Or monitor the conversation status until completion:")
    print(f"python roboco/examples/services/chat_example.py --id {response.conversation_id} --monitor")
    
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


async def display_status(conversation_id: str):
    """Display the status of a conversation."""
    print("=" * 80)
    print("  Conversation Status")
    print("=" * 80)
    print(f"Conversation ID: {conversation_id}")
    print("=" * 80)
    
    # Get the status
    response = await check_chat_status(conversation_id)
    
    if response.get("status") == "not_found":
        print(f"Conversation {conversation_id} not found")
        return
    
    # Display the status
    print("\n" + "=" * 80)
    print("  Status")
    print("=" * 80)
    print(f"Status: {response.get('status')}")
    
    # Display timing information if available
    if "created_at" in response and "updated_at" in response:
        print(f"Created at: {response.get('created_at')}")
        print(f"Last updated: {response.get('updated_at')}")
        
    if "progress" in response and response.get("progress") is not None:
        print(f"Progress: {response.get('progress')}%")
    
    if response.get('project_id'):
        print(f"Project ID: {response.get('project_id')}")
    
    print("\nLatest Message:")
    print("-" * 40)
    print(response.get("message", "No message available"))
    print("-" * 40)
    
    # If project details are available, show them
    if response.get("project_details"):
        print("\nProject Details:")
        for key, value in response.get("project_details", {}).items():
            print(f"  {key}: {value}")


async def monitor_conversation(conversation_id: str, interval: int = 2, max_time: int = 300):
    """
    Monitor a conversation until it completes or times out.
    
    Args:
        conversation_id: The ID of the conversation to monitor
        interval: How often to check status (in seconds)
        max_time: Maximum time to monitor (in seconds)
    """
    print("=" * 80)
    print("  Monitoring Conversation")
    print("=" * 80)
    print(f"Conversation ID: {conversation_id}")
    print(f"Checking every {interval} seconds (max {max_time} seconds)")
    print("=" * 80)
    
    start_time = time.time()
    last_status = None
    last_message = None
    
    try:
        while time.time() - start_time < max_time:
            # Get status
            status_data = await check_chat_status(conversation_id)
            
            # If status changed or message changed, display update
            current_status = status_data.get("status", "unknown")
            current_message = status_data.get("message", "")
            
            if current_status != last_status or current_message != last_message:
                print(f"\nStatus: {current_status}")
                print(f"Message: {current_message}")
                
                # Show progress if available
                if "progress" in status_data and status_data.get("progress") is not None:
                    print(f"Progress: {status_data.get('progress')}%")
                
                last_status = current_status
                last_message = current_message
            else:
                # Just print a progress indicator
                print(".", end="", flush=True)
            
            # If completed or error, break
            if current_status in ["completed", "failed", "not_found"]:
                print("\nConversation has finished.")
                await display_status(conversation_id)
                break
            
            # Wait for next check
            await asyncio.sleep(interval)
        else:
            print("\nMonitoring timed out. Final status:")
            await display_status(conversation_id)
    
    except KeyboardInterrupt:
        print("\nMonitoring cancelled by user. Final status:")
        await display_status(conversation_id)


def main():
    parser = argparse.ArgumentParser(description="Chat API Example")
    parser.add_argument("--query", "-q", type=str, default="Create a simple web crawler that can download and save webpage content",
                      help="Query to process")
    parser.add_argument("--id", type=str, help="Conversation ID to continue")
    parser.add_argument("--check-status", action="store_true", help="Check conversation status instead of sending a query")
    parser.add_argument("--monitor", action="store_true", help="Monitor conversation status until completion")
    
    args = parser.parse_args()
    
    # Run the async example
    if args.monitor:
        if not args.id:
            parser.error("Please provide a conversation ID with --id when using --monitor")
            return
        asyncio.run(monitor_conversation(args.id))
    elif args.check_status:
        if not args.id:
            parser.error("Please provide a conversation ID with --id when using --check-status")
            return
        asyncio.run(display_status(args.id))
    elif args.id:
        if not args.query:
            parser.error("Please provide a query with --query when continuing a conversation")
            return
        asyncio.run(continue_conversation(args.id, args.query))
    else:
        if not args.query:
            parser.error("Please provide a query with --query")
            return
        asyncio.run(run_example(args.query))


if __name__ == "__main__":
    main() 