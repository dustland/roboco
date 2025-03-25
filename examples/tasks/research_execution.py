#!/usr/bin/env python
"""
Research Task Execution Example

This example demonstrates how to use the ResearchTeam with the task execution architecture
to execute research-focused tasks from a tasks.md file.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from loguru import logger

# Add project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.core.project_executor import ProjectExecutor
from roboco.core.team_assigner import TeamAssigner
from roboco.teams.research import ResearchTeam
from roboco.core.models.phase import Phase

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

def print_section(title):
    """Print a section heading."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

class CustomTeamAssigner(TeamAssigner):
    """Custom TeamAssigner that specifically uses the ResearchTeam for research phases."""
    
    def __init__(self, workspace_dir: str):
        """Initialize the custom team assigner."""
        super().__init__(workspace_dir)
        
        # Add more specific research-related keywords
        self.phase_team_mapping.update({
            "literature": "research",
            "analysis": "research",
            "investigation": "research",
            "review": "research",
            "survey": "research",
            "exploration": "research",
            "data collection": "research"
        })
    
    def _create_team(self, team_type: str) -> Any:
        """Create and configure a team of the specified type."""
        logger.debug(f"Creating team of type '{team_type}'")
        
        if team_type == "research":
            # Always use ResearchTeam for research-type phases
            return ResearchTeam(workspace_dir=self.workspace_dir)
        
        # For other team types, use the parent implementation
        return super()._create_team(team_type)

class ResearchProjectExecutor(ProjectExecutor):
    """ProjectExecutor specialized for research projects."""
    
    def __init__(self, project_dir: str):
        """Initialize the research project executor."""
        # Initialize with parent class but don't create the phase executor yet
        self.project_dir = project_dir
        from roboco.core.task_manager import TaskManager
        self.task_manager = TaskManager()
        
        # Create a custom phase executor with our custom team assigner
        from roboco.core.phase_executor import PhaseExecutor
        self.phase_executor = PhaseExecutor(
            project_dir=project_dir, 
            workspace_dir=project_dir
        )
        
        # Replace the team assigner with our custom version
        self.phase_executor.team_assigner = CustomTeamAssigner(project_dir)
        
        logger.debug(f"Initialized ResearchProjectExecutor for project: {project_dir}")

async def create_sample_research_tasks(project_dir):
    """Create a sample research tasks.md file if it doesn't exist."""
    tasks_path = os.path.join(project_dir, "tasks.md")
    
    if os.path.exists(tasks_path):
        return  # Don't overwrite existing tasks file
    
    content = """# Research Project Tasks

## Research Phase
- [ ] Conduct literature review on machine learning algorithms for natural language processing
- [ ] Gather data on performance metrics of top 5 language models
- [ ] Analyze current trends in AI ethics and governance
- [ ] Investigate the impact of large language models on knowledge work

## Analysis Phase
- [ ] Compare and contrast different large language model architectures
- [ ] Develop a framework for evaluating AI assistant products
- [ ] Identify key success factors for AI deployment in enterprise settings

## Implementation Phase
- [ ] Design a proof-of-concept for a specialized language model
- [ ] Create a testing methodology for evaluating model performance
- [ ] Develop documentation for the research findings
"""
    
    # Create directory if it doesn't exist
    os.makedirs(project_dir, exist_ok=True)
    
    # Write the tasks file
    with open(tasks_path, "w") as f:
        f.write(content)
    
    print(f"Created sample research tasks at: {tasks_path}")

async def main():
    """Run the research task execution example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Execute research tasks from a tasks.md file")
    parser.add_argument("--project", "-p", type=str, default="workspace/research_project", 
                      help="Path to the research project directory")
    parser.add_argument("--phase", "-ph", type=str, help="Execute a specific research phase")
    parser.add_argument("--task", "-t", type=str, help="Execute a specific research task")
    parser.add_argument("--sample", "-s", action="store_true", 
                      help="Create a sample research tasks.md file")
    
    args = parser.parse_args()
    
    # Create sample tasks if requested
    if args.sample:
        await create_sample_research_tasks(args.project)
    
    # Create the research project executor
    executor = ResearchProjectExecutor(args.project)
    
    # Execute based on command line arguments
    if args.task:
        print_section(f"Executing Research Task: {args.task}")
        result = await executor.execute_task(args.task)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Task '{result['task']}' in phase '{result['phase']}' executed successfully")
            
    elif args.phase:
        print_section(f"Executing Research Phase: {args.phase}")
        result = await executor.execute_project(phase_filter=args.phase)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Phase execution completed with status: {result['overall_status']}")
            
    else:
        print_section("Executing All Research Phases")
        result = await executor.execute_project()
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ All phases executed with status: {result['overall_status']}")
            
            # Print phase summary
            for phase_name, phase_result in result["phases"].items():
                completed = sum(1 for task in phase_result["tasks"].values() 
                              if task["status"] in ["completed", "already_completed"])
                total = len(phase_result["tasks"])
                print(f"Phase '{phase_name}': {completed}/{total} tasks completed")
    
    print_section("Research Execution Complete")

if __name__ == "__main__":
    asyncio.run(main()) 