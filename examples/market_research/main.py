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
from roboco.core import load_env_variables
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
    
    # Handle AG2's ChatResult object
    if hasattr(result, "chat_history"):
        logger.debug("Processing AG2 ChatResult object")
        try:
            # Convert chat history to a list if it's not already
            chat_history = list(result.chat_history)
            # Look for messages from the ReportWriter agent that contain a report
            for message in chat_history:
                content = getattr(message, "content", "")
                sender = getattr(message, "sender", "")
                if isinstance(content, str) and "report" in content.lower():
                    logger.info(f"Found report in ChatResult history from {sender}")
                    return content
        except Exception as e:
            logger.error(f"Error processing ChatResult: {e}")
    
    # Handle dictionary result from run_swarm
    if isinstance(result, dict):
        logger.debug("Processing dictionary result")
        
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
        
        # Check if the result contains chat history that might have the report
        if "chat_history" in result:
            logger.debug("Searching for report in chat history dictionary")
            chat_history = result["chat_history"]
            
            # If chat_history is a ChatResult object
            if hasattr(chat_history, "chat_history"):
                try:
                    logger.debug("Chat history is a ChatResult object")
                    messages = list(chat_history.chat_history)
                    for message in messages:
                        content = getattr(message, "content", "")
                        sender = getattr(message, "sender", "")
                        if isinstance(content, str) and "report" in content.lower():
                            logger.info(f"Found report in chat_history.chat_history from {sender}")
                            return content
                except Exception as e:
                    logger.error(f"Error processing chat_history.chat_history: {e}")
            
            # If chat_history is a list
            elif isinstance(chat_history, list):
                try:
                    for message in chat_history:
                        if isinstance(message, dict) and "content" in message and "report" in message.get("content", "").lower():
                            logger.info("Found report in chat history list")
                            return message["content"]
                except Exception as e:
                    logger.error(f"Error processing chat history list: {e}")
    
    # If we have a tuple with chat_result, context, and last_agent
    if isinstance(result, tuple) and len(result) >= 2:
        logger.debug("Processing tuple result")
        chat_result, context = result[0], result[1]
        
        # Check if context contains a report
        if isinstance(context, dict) and "report" in context:
            logger.info("Found report in context")
            return context["report"]
        
        # Check if chat_result contains messages that might have the report
        if hasattr(chat_result, "chat_history"):
            logger.debug("Searching for report in chat_result.chat_history")
            try:
                for message in list(chat_result.chat_history):
                    content = getattr(message, "content", "")
                    sender = getattr(message, "sender", "")
                    if isinstance(content, str) and "report" in content.lower():
                        logger.info(f"Found report in chat_result.chat_history from {sender}")
                        return content
            except Exception as e:
                logger.error(f"Error processing chat_result.chat_history: {e}")
    
    logger.warning("No report found in result")
    return None

def run_embodied_research():
    """Run the embodied AI research scenario using AG2's Swarm orchestration."""
    logger.debug("Starting embodied research scenario")
    try:
        # Create the research team with the config.toml in the same directory
        logger.debug("Creating research team")
        team = ResearchTeam()
        logger.debug("Research team created successfully")
        
        # Define the CEO's query
        ceo_query = """
        I need a comprehensive report on cutting-edge embodied AI technologies.
        Focus on:
        1. Current state-of-the-art approaches
        2. Major players and their innovations
        3. Key challenges and limitations
        4. Future directions and potential breakthroughs
        5. Implications for businesses and society
        
        Please provide a well-structured report with clear recommendations.
        """
        
        # Print the query
        print("\n" + "="*80)
        print("CEO QUERY:")
        print("-"*80)
        print(ceo_query)
        print("-"*80)
        
        # Run the scenario using the team's run_research method
        logger.debug("Running research scenario")
        try:
            # Run the research using the team's run_research method
            result = team.run_research(ceo_query)
            logger.debug("Research scenario completed successfully")
            
            # Extract the report from the result
            report = extract_report_from_result(result)
            
        except Exception as e:
            logger.error(f"Error running scenario: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return
        
        # Print a summary
        print("\n" + "="*80)
        print("RESEARCH RESULTS:")
        print("-"*80)
        
        if report:
            print(report)
        elif isinstance(result, dict) and "report_path" in result:
            report_path = result["report_path"]
            print(f"Report saved to: {report_path}")
            
            try:
                with open(report_path, "r") as f:
                    report_content = f.read()
                print("\nREPORT CONTENT:")
                print("-"*80)
                print(report_content)
            except Exception as e:
                print(f"Error reading report file: {e}")
        else:
            print("No report generated.")
            
        print("="*80)
    except Exception as e:
        logger.error(f"Error in run_embodied_research: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run_simple_research(query: str, timeout: int = 60) -> None:
    """
    Run a simple research scenario.
    
    Args:
        query: The research query
        timeout: The timeout in seconds
    """
    logger.info(f"Starting simple research scenario on: {query}")
    
    # Run the research
    report = run_research(query, timeout)
    
    # Process the report
    if report:
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)
        
        # Save the report to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/report_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(report)
        
        logger.info(f"Report saved to {filename}")
    else:
        logger.warning("No report was generated")

def run_research(query: str, timeout: int = 60) -> None:
    """
    Run the research scenario.
    
    Args:
        query: The research query
        timeout: The timeout in seconds
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
        
    # Extract the report from the chat history
    try:
        logger.info("Attempting to extract report from chat history")
        report = team.extract_report_from_chat_history()
        if report:
            logger.info(f"Report extracted successfully: {len(report)} characters")
        else:
            logger.warning("No report found in chat history")
    except Exception as e:
        logger.error(f"Error extracting report: {e}")
        report = None
    
    return report

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run market research")
    parser.add_argument("--query", type=str, required=True, help="The research query")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Run the research
    run_simple_research(args.query, timeout=args.timeout)