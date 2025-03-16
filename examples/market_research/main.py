"""
Embodied AI Market Research Example

This example demonstrates a scenario where a CEO asks about cutting-edge embodied AI
technologies, and a research team collaborates using AG2's Swarm orchestration to create
a comprehensive report.
"""

import os
import sys
import json
import threading
import traceback
from pathlib import Path
from loguru import logger
from datetime import datetime
from typing import Dict, Any
import argparse

# Configure logger to be more verbose
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.debug("Starting market research module")

# Add src directory to Python path if needed
project_root = Path(__file__).parent.parent.parent.absolute()
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
    logger.debug(f"Added {src_path} to Python path")

# Load environment variables
from roboco.core.config import load_env_variables
logger.debug("Loading environment variables")
load_env_variables(project_root)
logger.debug("Environment variables loaded")

# Check for API key
if not os.environ.get("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY environment variable not set")
else:
    logger.debug("OPENAI_API_KEY is set")

def test_openai_connection():
    """Test the OpenAI API connection."""
    logger.debug("Testing OpenAI API connection")
    try:
        import openai
        client = openai.OpenAI()
        models = client.models.list()
        logger.debug(f"OpenAI API connection successful. Available models: {len(models.data)}")
        return True
    except Exception as e:
        logger.error(f"Error connecting to OpenAI API: {e}")
        return False

def test_autogen_import():
    """Test importing autogen modules."""
    logger.debug("Testing autogen imports")
    try:
        import autogen
        logger.debug(f"Autogen version: {autogen.__version__}")
        from autogen import ConversableAgent, AssistantAgent, UserProxyAgent
        logger.debug("Successfully imported autogen modules")
        return True
    except Exception as e:
        logger.error(f"Error importing autogen: {e}")
        return False

# Import the research team from our module
logger.debug("Importing ResearchTeam")
from examples.market_research.team import ResearchTeam
logger.debug("ResearchTeam imported")

def extract_report_from_result(result):
    """
    Extract the report content from the swarm result.
    
    Args:
        result: The result from the swarm execution (ChatResult, dict, or tuple)
        
    Returns:
        The report content as a string, or None if no report was found
    """
    logger.debug("Extracting report from result")
    
    # Debug: Print result structure
    if isinstance(result, dict):
        logger.debug(f"Result keys: {result.keys()}")
        if "context" in result and isinstance(result["context"], dict):
            logger.debug(f"Context keys: {result['context'].keys()}")
    
    # First check if result is a dictionary with context containing report_content
    if isinstance(result, dict):
        logger.debug("Processing dictionary result")
        
        # Check if the context contains report_content
        if "context" in result and isinstance(result["context"], dict):
            context = result["context"]
            if "report_content" in context and context["report_content"]:
                logger.info("Found report in context's report_content")
                return context["report_content"]
        
        # Check if the result contains a report_path
        if "report_path" in result:
            logger.info(f"Report path found: {result['report_path']}")
            try:
                with open(result['report_path'], 'r') as f:
                    report_content = f.read()
                    logger.debug(f"Report content loaded: {len(report_content)} characters")
                    return report_content
            except Exception as e:
                logger.error(f"Error reading report file: {e}")
        
        # Directly check chat history in the result
        if "chat_history" in result and isinstance(result["chat_history"], list):
            logger.debug(f"Checking chat history directly (length: {len(result['chat_history'])})")
            for i, message in enumerate(result["chat_history"]):
                if isinstance(message, dict):
                    sender = message.get("name", "unknown")
                    content = message.get("content", "")
                    logger.debug(f"Message {i} from {sender}: {content[:50]}...")
                    
                    if sender == "ReportWriter" and "#" in content:
                        # Check if content contains a markdown heading
                        lines = content.strip().split("\n")
                        for line in lines:
                            if line.strip().startswith("#"):
                                logger.info(f"Found report with heading: {line.strip()}")
                                return content
    
    # Handle AG2's ChatResult object
    if hasattr(result, "chat_history"):
        logger.debug("Processing AG2 ChatResult object")
        try:
            # Convert chat history to a list if it's not already
            chat_history = list(result.chat_history)
            logger.debug(f"Chat history length: {len(chat_history)}")
            
            # Debug: Print each message in the chat history
            for i, message in enumerate(chat_history):
                sender = getattr(message, "sender", "unknown")
                content = getattr(message, "content", "")[:100]
                logger.debug(f"Message {i} from {sender}: {content}...")
            
            # Look for messages from the ReportWriter agent that contain a markdown heading
            for message in chat_history:
                content = getattr(message, "content", "")
                sender = getattr(message, "sender", "")
                if isinstance(content, str) and "#" in content:
                    # Check if content contains a markdown heading
                    lines = content.strip().split("\n")
                    for line in lines:
                        if line.strip().startswith("#"):
                            logger.info(f"Found report with markdown heading in ChatResult history from {sender}")
                            return content
        except Exception as e:
            logger.error(f"Error processing ChatResult: {e}")
    
    # Handle dictionary result with chat_history
    if isinstance(result, dict) and "chat_history" in result:
        chat_history = result["chat_history"]
        
        # If chat_history is a ChatResult object
        if hasattr(chat_history, "chat_history"):
            try:
                logger.debug("Chat history is a ChatResult object")
                messages = list(chat_history.chat_history)
                for message in messages:
                    content = getattr(message, "content", "")
                    sender = getattr(message, "sender", "")
                    if isinstance(content, str) and "#" in content:
                        # Check if content contains a markdown heading
                        lines = content.strip().split("\n")
                        for line in lines:
                            if line.strip().startswith("#"):
                                logger.info(f"Found report with markdown heading in chat_history.chat_history from {sender}")
                                return content
            except Exception as e:
                logger.error(f"Error processing chat_history.chat_history: {e}")
        
        # If chat_history is a list
        elif isinstance(chat_history, list):
            try:
                for message in chat_history:
                    if isinstance(message, dict) and "content" in message:
                        content = message.get("content", "")
                        if isinstance(content, str) and "#" in content:
                            # Check if content contains a markdown heading
                            lines = content.strip().split("\n")
                            for line in lines:
                                if line.strip().startswith("#"):
                                    logger.info("Found report with markdown heading in chat history list")
                                    return content
            except Exception as e:
                logger.error(f"Error processing chat history list: {e}")
    
    # If we have a tuple with chat_result, context, and last_agent
    if isinstance(result, tuple) and len(result) >= 2:
        logger.debug("Processing tuple result")
        chat_result, context = result[0], result[1]
        
        # Check if context contains a report
        if isinstance(context, dict):
            if "report_content" in context and context["report_content"]:
                logger.info("Found report_content in context")
                return context["report_content"]
            elif "report" in context:
                logger.info("Found report in context")
                return context["report"]
        
        # Check if chat_result contains messages that might have the report
        if hasattr(chat_result, "chat_history"):
            logger.debug("Searching for report in chat_result.chat_history")
            try:
                for message in list(chat_result.chat_history):
                    content = getattr(message, "content", "")
                    sender = getattr(message, "sender", "")
                    if isinstance(content, str) and "#" in content:
                        # Check if content contains a markdown heading
                        lines = content.strip().split("\n")
                        for line in lines:
                            if line.strip().startswith("#"):
                                logger.info(f"Found report with markdown heading in chat_result.chat_history from {sender}")
                                return content
            except Exception as e:
                logger.error(f"Error processing chat_result.chat_history: {e}")
    
    logger.warning("No report found in result")
    return None

def run_embodied_research(query):
    """
    Run a research scenario using the embodied AI approach with AG2's Swarm orchestration.
    
    Args:
        query: The research query to investigate
        
    Returns:
        The research report as a string
    """
    logger.debug("Starting embodied research scenario")
    
    try:
        # Create the research team
        logger.debug("Creating research team")
        team = ResearchTeam()
        logger.debug("Research team created successfully")
        
        # Print the CEO query
        print("\n" + "=" * 80)
        print("CEO QUERY:")
        print("-" * 80)
        print("\n" + query + "\n")
        print("-" * 80)
        
        # Run the research scenario
        logger.debug("Running research scenario")
        result = team.run_research(query)
        logger.debug("Research scenario completed successfully")
        
        # Extract the report from the result
        report = extract_report_from_result(result)
        
        # Print a summary
        print("\n" + "=" * 80)
        print("RESEARCH RESULTS:")
        print("-" * 80)
        
        if report:
            print(report)
        elif isinstance(result, dict) and "report_path" in result:
            report_path = result["report_path"]
            print(f"Report saved to: {report_path}")
            
            try:
                with open(report_path, "r") as f:
                    report_content = f.read()
                print("\nREPORT CONTENT:")
                print("-" * 80)
                print(report_content)
                report = report_content
            except Exception as e:
                print(f"Error reading report file: {e}")
                logger.error(f"Error reading report file: {e}")
        else:
            print("No report generated. The research process completed but no report was found.")
            logger.warning("No report was extracted from the research results")
            
        print("=" * 80)
        return report
        
    except Exception as e:
        logger.error(f"Error in run_embodied_research: {e}")
        import traceback
        logger.error(traceback.format_exc())
        print("\n" + "=" * 80)
        print("ERROR RUNNING RESEARCH:")
        print("-" * 80)
        print(f"An error occurred: {e}")
        print("=" * 80)
        return None

def run_simple_research(query: str, timeout: int = 60) -> None:
    """
    Run a simple research scenario.
    
    Args:
        query: The research query
        timeout: The timeout in seconds
    """
    logger.info(f"Starting simple research scenario on: {query}")
    
    # Run the research
    result = run_research(query, timeout)
    
    # Extract report from result if available
    report = None
    if isinstance(result, dict) and "context" in result:
        context = result.get("context", {})
        if "report_content" in context and context["report_content"]:
            report = context["report_content"]
            logger.info("Found report in result context")
    
    # Process the report
    if report:
        try:
            # Create reports directory if it doesn't exist
            os.makedirs("reports", exist_ok=True)
            
            # Save the report to a file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/report_{timestamp}.md"
            
            with open(filename, "w") as f:
                f.write(report)
            
            logger.info(f"Report saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    else:
        logger.warning("No report was generated")

def run_research(query: str, timeout: int = 60) -> Dict[str, Any]:
    """
    Run the research scenario.
    
    Args:
        query: The research query
        timeout: The timeout in seconds
        
    Returns:
        Dictionary containing the research results
    """
    logger.info(f"Starting market research on: {query}")
    
    # Create a research team
    team = ResearchTeam()
    
    # Create an event to signal when research is complete
    research_complete = threading.Event()
    
    # Run the research scenario
    logger.info("Running research scenario with swarm pattern")
    result = team.run_swarm(
        query=query,
        max_rounds=10  # Use a reasonable number of rounds
    )
    
    # Signal that research is complete
    logger.info("Research scenario completed")
    research_complete.set()
    
    # Wait for the research to complete or timeout
    logger.info(f"Waiting for research to complete (timeout: {timeout}s)")
    research_complete.wait(timeout=timeout)
    
    if not research_complete.is_set():
        logger.warning(f"Research timed out after {timeout} seconds")
    else:
        logger.info("Research completed successfully")
        
    # Try to extract report from chat history if not in context
    if isinstance(result, dict) and "context" in result:
        context = result.get("context", {})
        if not context.get("report_content"):
            try:
                logger.info("Attempting to extract report from chat history")
                report = team.extract_report_from_chat_history()
                if report:
                    logger.info(f"Report extracted successfully: {len(report)} characters")
                    # Add the report to the context
                    if "context" in result:
                        result["context"]["report_content"] = report
                else:
                    logger.warning("No report found in chat history")
            except Exception as e:
                logger.error(f"Error extracting report: {e}")
    
    return result

def main():
    """Main entry point for the market research module."""
    parser = argparse.ArgumentParser(description="Run market research")
    parser.add_argument("query", help="The research query to investigate", nargs="?", default=None)
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds for simple research")
    parser.add_argument("--simple", action="store_true", help="Use simple research approach")
    args = parser.parse_args()
    
    # If no query is provided, use a default query
    if args.query is None:
        args.query = """
        I need a comprehensive report on cutting-edge embodied AI technologies.
        Focus on:
        1. Current state-of-the-art approaches
        2. Major players and their innovations
        3. Key challenges and limitations
        4. Future directions and potential breakthroughs
        5. Implications for businesses and society
        
        Please provide a well-structured report with clear recommendations.
        """
    
    # Run the appropriate research function
    if args.simple:
        run_simple_research(args.query, args.timeout)
    else:
        # Run the embodied research
        report = run_embodied_research(args.query)
        
        # Print the report
        print("\n" + "=" * 80)
        print("RESEARCH RESULTS:")
        print("-" * 80)
        
        if report:
            print(report)
        else:
            print("No report generated.")
            
        print("=" * 80)

if __name__ == "__main__":
    main()