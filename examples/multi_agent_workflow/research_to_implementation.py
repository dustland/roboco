"""
Research to Implementation Workflow

This script demonstrates a collaborative workflow between the RoboticsScientistAgent
and SoftwareDeveloperAgent to research and implement robotics projects.
"""

import asyncio
import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from roboco.core import load_config, get_workspace, Workspace
from roboco.core.logger import get_logger
from roboco.agents.robotics_scientist import RoboticsScientistAgent
from roboco.agents.software_engineer import SoftwareDeveloperAgent, Project

logger = get_logger("research_to_implementation")

# Research topics in cutting-edge robotics
RESEARCH_TOPICS = [
    "humanoid robot locomotion",
    "robotic manipulation with reinforcement learning",
    "vision-based navigation for mobile robots",
    "multi-agent robot coordination",
    "tactile sensing for robotic manipulation"
]

async def run_research_to_implementation_pipeline(topic: str, output_dir: str = None):
    """Run the complete research to implementation pipeline.
    
    Args:
        topic: Topic to research and implement
        output_dir: Directory to save outputs (if None, uses workspace from config)
    """
    # Load configuration
    config = load_config()
    
    # Create workspace
    if output_dir:
        # Use specified output directory
        workspace = Workspace(output_dir)
    else:
        # Use workspace from configuration
        workspace = Workspace.create_from_config()
    
    logger.info(f"Starting research to implementation pipeline for: {topic}")
    logger.info("Phase 1: Initialize agents")
    
    # Initialize agents
    scientist = RoboticsScientistAgent(llm_config=config.llm)
    developer = SoftwareDeveloperAgent(
        llm_config=config.llm,
        github_token=os.environ.get("GITHUB_TOKEN")
    )
    
    await scientist.initialize()
    await developer.initialize()
    
    try:
        # Phase 1: Research
        logger.info("Phase 2: Conducting research")
        research_report = await scientist.run_research_pipeline(topic)
        
        # Save research report to workspace
        report_path = workspace.save_research_report(
            topic, 
            {
                "report": research_report["report"].dict(),
                "recommendations": research_report["recommendations"],
                "categories": {k: [item.dict() for item in v] for k, v in research_report["categories"].items()}
            }
        )
        
        logger.info(f"Research report saved to: {report_path}")
        
        # Phase 2: Development Planning
        logger.info("Phase 3: Development planning")
        project = await developer.generate_project_from_research(research_report)
        
        # Save project plan as documentation
        project_doc = f"# {project.name}\n\n"
        project_doc += f"## Description\n{project.description}\n\n"
        project_doc += f"## Technologies\n" + "\n".join([f"- {tech}" for tech in project.technologies]) + "\n\n"
        project_doc += f"## Tasks\n" + "\n".join([
            f"- {'[x]' if task.status == 'done' else '[ ]'} {task.title}" 
            for task in project.tasks
        ])
        
        doc_path = workspace.save_documentation(
            topic.replace(' ', '_'),
            "project_plan",
            project_doc
        )
        
        logger.info(f"Project plan saved to: {doc_path}")
        
        # Phase 3: Implementation
        logger.info("Phase 4: Implementation")
        
        # Log implementation details
        logger.info(f"Project: {project.name}")
        logger.info(f"Description: {project.description}")
        logger.info(f"Technologies: {', '.join(project.technologies)}")
        
        if project.github_repo:
            logger.info(f"GitHub Repository: {project.github_repo.url}")
        
        logger.info("Development Tasks:")
        for task in project.tasks:
            status_emoji = "✅" if task.status == "done" else "🔄" if task.status == "in_progress" else "⏳"
            logger.info(f"{status_emoji} {task.id}: {task.title}")
            
            # Log artifacts for completed tasks
            if task.artifacts:
                for artifact in task.artifacts:
                    logger.info(f"  📄 {artifact.path}: {artifact.description}")
                    
                    # Save code artifacts to workspace
                    if artifact.content:
                        artifact_path = workspace.save_code_artifact(
                            project.name.replace(' ', '_'),
                            artifact.path,
                            artifact.content
                        )
                        logger.info(f"  💾 Saved to workspace: {artifact_path}")
        
        return {
            "research": research_report,
            "project": project.dict(),
            "workspace_path": str(workspace.root_path)
        }
        
    finally:
        # Clean up resources
        await scientist.cleanup()
        await developer.cleanup()

async def run_multi_agent_collaboration(topic: str, output_dir: str = None):
    """Run a multi-agent collaboration with continuous development.
    
    Args:
        topic: Topic to research and implement
        output_dir: Directory to save outputs (if None, uses workspace from config)
    """
    config = load_config()
    
    # Create workspace
    if output_dir:
        # Use specified output directory
        workspace = Workspace(output_dir)
    else:
        # Use workspace from configuration
        workspace = Workspace.create_from_config()
    
    logger.info(f"Starting multi-agent collaboration for: {topic}")
    
    # Initialize agents
    scientist = RoboticsScientistAgent(llm_config=config.llm)
    developer = SoftwareDeveloperAgent(
        llm_config=config.llm,
        github_token=os.environ.get("GITHUB_TOKEN")
    )
    
    await scientist.initialize()
    await developer.initialize()
    
    try:
        # Use the developer agent's pipeline that integrates research from scientist
        results = await developer.build_development_pipeline([scientist], topic)
        
        # Convert nested models to dictionaries for serialization
        serializable_results = {
            "research": {
                "report": results["research"]["report"].dict(),
                "recommendations": results["research"]["recommendations"],
                "categories": {k: [item.dict() for item in v] for k, v in results["research"]["categories"].items()}
            },
            "project": results["project"].dict(),
            "github_repo": results["github_repo"],
            "tasks": results["tasks"]
        }
        
        # Save research report to workspace
        report_path = workspace.save_research_report(
            topic,
            serializable_results["research"]
        )
        logger.info(f"Research report saved to: {report_path}")
        
        # Save project plan as documentation
        project = results["project"]
        project_doc = f"# {project.name}\n\n"
        project_doc += f"## Description\n{project.description}\n\n"
        project_doc += f"## Technologies\n" + "\n".join([f"- {tech}" for tech in project.technologies]) + "\n\n"
        project_doc += f"## Tasks\n" + "\n".join([
            f"- {'[x]' if task['status'] == 'done' else '[ ]'} {task['title']}" 
            for task in results["tasks"]
        ])
        
        doc_path = workspace.save_documentation(
            topic.replace(' ', '_'),
            "collaboration_results",
            project_doc
        )
        logger.info(f"Project documentation saved to: {doc_path}")
        
        # Save code artifacts
        for task in results["tasks"]:
            if "artifacts" in task and task["artifacts"]:
                for artifact in task["artifacts"]:
                    if "content" in artifact and artifact["content"]:
                        artifact_path = workspace.save_code_artifact(
                            project.name.replace(' ', '_'),
                            artifact["path"],
                            artifact["content"]
                        )
                        logger.info(f"Code artifact saved to: {artifact_path}")
        
        # Log summary of collaboration
        logger.info("\n=== COLLABORATION SUMMARY ===")
        logger.info(f"Research Topic: {topic}")
        logger.info(f"Project: {results['project'].name}")
        logger.info(f"Technologies: {', '.join(results['project'].technologies)}")
        logger.info(f"Workspace: {workspace.root_path}")
        
        if results["github_repo"]:
            logger.info(f"GitHub Repository: {results['github_repo']['url']}")
        
        logger.info(f"Tasks: {len(results['tasks'])}")
        completed_tasks = sum(1 for task in results['tasks'] if task['status'] == 'done')
        logger.info(f"Completed Tasks: {completed_tasks}")
        
        return {
            **serializable_results,
            "workspace_path": str(workspace.root_path)
        }
        
    finally:
        # Clean up resources
        await scientist.cleanup()
        await developer.cleanup()

def setup_argparse():
    """Set up command-line argument parsing."""
    parser = argparse.ArgumentParser(description="Research to Implementation Pipeline")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Basic pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run basic research to implementation pipeline")
    pipeline_parser.add_argument("topic", help="Topic to research and implement")
    pipeline_parser.add_argument("--output-dir", help="Output directory for results (overrides workspace from config)")
    
    # Multi-agent collaboration command
    collab_parser = subparsers.add_parser("collaborate", help="Run multi-agent collaboration")
    collab_parser.add_argument("topic", help="Topic to research and implement")
    collab_parser.add_argument("--output-dir", help="Output directory for results (overrides workspace from config)")
    
    # Batch processing command
    batch_parser = subparsers.add_parser("batch", help="Process multiple topics")
    batch_parser.add_argument("--output-dir", help="Output directory for results (overrides workspace from config)")
    batch_parser.add_argument("--limit", type=int, default=3, help="Number of topics to process")
    
    return parser

async def main():
    """Main entry point for the research to implementation example."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if args.command == "pipeline":
        await run_research_to_implementation_pipeline(args.topic, args.output_dir)
    elif args.command == "collaborate":
        await run_multi_agent_collaboration(args.topic, args.output_dir)
    elif args.command == "batch":
        # Process multiple topics
        for topic in RESEARCH_TOPICS[:args.limit]:
            logger.info(f"\n\n=== Processing topic: {topic} ===\n")
            await run_multi_agent_collaboration(topic, args.output_dir)
    else:
        # Default to running the pipeline on a single topic using workspace from config
        await run_research_to_implementation_pipeline(
            "humanoid robot locomotion with reinforcement learning"
        )

if __name__ == "__main__":
    # Set GitHub token for development (in production, use environment variables)
    if not os.environ.get("GITHUB_TOKEN"):
        os.environ["GITHUB_TOKEN"] = "your_github_token_here"
        
    asyncio.run(main()) 