"""
This example demonstrates a multi-agent team collaborating to write a blog post.

The workflow is as follows:
1.  A User Proxy Agent receives the initial request from the user.
2.  A Planner agent creates a detailed outline for the blog post.
3.  A Writer agent takes the outline and writes the full content of the post.
4.  A Reviewer agent checks the written content for quality, style, and accuracy.
5.  The final output is presented to the user.

This scenario showcases agent collaboration, state management (passing the plan and draft between agents),
and the power of a config-driven multi-agent system.
"""

import asyncio

from roboco.teams import Team

def run_writing_scenario():
    """Sets up and runs the blog post writing scenario."""
    print("Initializing the blog post writing team...")

    # In a real implementation, this would load a team configuration from a YAML file.
    # For this example, we define it programmatically.
    writing_team_config = {
        "name": "Blog Writing Team",
        "agents": [
            {
                "name": "Planner",
                "role": "Outline the structure of a blog post on a given topic.",
                "llm_config": {"model": "gpt-4o"}
            },
            {
                "name": "Writer",
                "role": "Write the full content of the blog post based on a provided outline.",
                "llm_config": {"model": "gpt-4o"}
            },
            {
                "name": "Reviewer",
                "role": "Review the blog post for clarity, grammar, and style. Provide feedback for revisions.",
                "llm_config": {"model": "gpt-4o"}
            }
        ],
        "workflow": [
            {"from": "UserProxy", "to": "Planner", "context": "topic"},
            {"from": "Planner", "to": "Writer", "context": "outline"},
            {"from": "Writer", "to": "Reviewer", "context": "draft"},
            {"from": "Reviewer", "to": "UserProxy", "context": "final_post"}
        ]
    }

    # Create the team from the configuration
    writing_team = Team.from_config(writing_team_config)

    topic = "The Future of AI: A Multi-Agent Approach"
    print(f"\nTopic: {topic}\n")

    # Run the team's workflow
    # The `chat` method would trigger the defined workflow.
    # The following is a mock execution for demonstration purposes.
    print("--- Workflow Started ---")
    print("1. Planner is creating the outline...")
    outline = "1. Intro to AI\n2. Rise of Multi-Agent Systems\n3. Benefits\n4. Conclusion"
    print(f"   - Outline created: \n{outline}\n")

    print("2. Writer is drafting the blog post...")
    draft = f"# {topic}\n\nThis is a draft about multi-agent systems..."
    print(f"   - Draft completed.\n")

    print("3. Reviewer is checking the draft...")
    feedback = "Looks good. Suggest adding a section on challenges."
    print(f"   - Feedback received: {feedback}\n")

    print("4. Writer is revising the draft (mocked)...")
    final_post = f"# {topic}\n\nThis is the final, revised post about multi-agent systems, including challenges."
    print("   - Revision complete.\n")

    print("--- Workflow Finished ---")
    print("\nFinal Blog Post:")
    print("--------------------")
    print(final_post)
    print("--------------------")

if __name__ == "__main__":
    run_writing_scenario()
