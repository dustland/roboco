#!/usr/bin/env python3
"""Simple example demonstrating web research capabilities."""

from roboco.agents import ProductManager, HumanProxy

def main():
    """Run the example."""
    # Create agents
    researcher = ProductManager()
    user = HumanProxy(
        human_input_mode="NEVER",  # Disable human input for automation
        terminate_msg="Thank you for the research summary."  # End conversation after getting response
    )
    
    # Start a simple research conversation
    user.initiate_chat(
        researcher,
        message="What are the latest developments in humanoid robotics? Please provide a brief summary."
    )

if __name__ == "__main__":
    main()