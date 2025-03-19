"""
Software Developer Agent

This module provides a Software Developer agent that can implement robotics and embodied AI
projects based on research findings, with integrated GitHub and coding tool support.
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from roboco.core.logger import get_logger
from roboco.core.agent import Agent
from roboco.core.models import LLMConfig
from roboco.tools.browser_use import BrowserUseTool, BrowserUseResult

logger = get_logger(__name__)

class GitHubRepo(BaseModel):
    """A GitHub repository model."""
    name: str = Field(description="Name of the repository")
    owner: str = Field(description="Owner of the repository")
    url: str = Field(description="URL to the repository")
    description: Optional[str] = Field(None, description="Description of the repository")
    stars: Optional[int] = Field(None, description="Number of stars")
    forks: Optional[int] = Field(None, description="Number of forks")
    last_commit: Optional[str] = Field(None, description="Date of last commit")
    languages: Optional[List[str]] = Field(None, description="Programming languages used")
    
class CodeArtifact(BaseModel):
    """A code artifact produced by the developer."""
    name: str = Field(description="Name of the artifact (file, module, class, etc.)")
    path: str = Field(description="Path to the artifact")
    language: str = Field(description="Programming language used")
    description: str = Field(description="Description of the artifact")
    code: Optional[str] = Field(None, description="Source code snippet if applicable")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies required")
    
class DevelopmentTask(BaseModel):
    """A development task to be implemented."""
    id: str = Field(description="Unique identifier for the task")
    title: str = Field(description="Title of the task")
    description: str = Field(description="Detailed description of what to implement")
    priority: str = Field(description="Priority level (high, medium, low)")
    status: str = Field(description="Current status (todo, in_progress, review, done)")
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent tasks")
    assigned_to: Optional[str] = Field(None, description="Agent assigned to the task")
    artifacts: List[CodeArtifact] = Field(default_factory=list, description="Code artifacts produced")
    
class Project(BaseModel):
    """A software development project."""
    name: str = Field(description="Name of the project")
    description: str = Field(description="Description of the project")
    github_repo: Optional[GitHubRepo] = Field(None, description="Associated GitHub repository")
    tasks: List[DevelopmentTask] = Field(default_factory=list, description="Development tasks")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")
    
class SoftwareEngineer(Agent):
    """An agent that implements robotics and embodied AI projects."""
    
    def __init__(
        self,
        name: str = "Software Developer",
        llm_config: Optional[LLMConfig] = None,
        github_token: Optional[str] = None,
        **kwargs
    ):
        """Initialize the SoftwareDeveloperAgent.
        
        Args:
            name: The name of the agent.
            llm_config: Configuration for the language model.
            github_token: GitHub personal access token for API access.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(name=name, llm_config=llm_config, **kwargs)
        self.browser_tool = BrowserUseTool(llm_config=llm_config)
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.projects = {}
        
    async def initialize(self):
        """Initialize the agent and its tools."""
        logger.info(f"Initializing {self.name} agent")
    
    async def search_github_repos(self, query: str) -> BrowserUseResult:
        """Search for relevant GitHub repositories.
        
        Args:
            query: The search query.
            
        Returns:
            BrowserUseResult: The search results.
        """
        task = f"Search GitHub for repositories related to '{query}'. For each repository, extract the name, owner, URL, description, stars, and main programming languages used."
        return await self.browser_tool.browser_use(task)
    
    async def analyze_code_repository(self, repo_url: str) -> BrowserUseResult:
        """Analyze a code repository structure and quality.
        
        Args:
            repo_url: URL to the code repository.
            
        Returns:
            BrowserUseResult: The result of analyzing the repository.
        """
        task = f"Go to {repo_url} and analyze the codebase structure, quality, and architecture. Identify key components, dependencies, and potential areas for improvement."
        return await self.browser_tool.browser_use(task)
    
    async def research_coding_patterns(self, technology: str) -> BrowserUseResult:
        """Research coding patterns and best practices for a specific technology.
        
        Args:
            technology: The technology to research.
            
        Returns:
            BrowserUseResult: The research results.
        """
        task = f"Research best practices, design patterns, and code examples for {technology} in robotics and embodied AI applications. Find at least 3 high-quality examples."
        return await self.browser_tool.browser_use(task)
    
    async def create_project(self, name: str, description: str, research_report: Dict[str, Any] = None) -> Project:
        """Create a new software development project.
        
        Args:
            name: Name of the project.
            description: Description of the project.
            research_report: Optional research report to base the project on.
            
        Returns:
            Project: The created project.
        """
        # Create a new project
        project = Project(
            name=name,
            description=description,
            technologies=[]
        )
        
        # Extract technologies from research report if provided
        if research_report and "recommendations" in research_report:
            for recommendation in research_report["recommendations"]:
                if recommendation.get("type") == "library" or recommendation.get("type") == "framework":
                    project.technologies.append(recommendation.get("title"))
        
        # Store the project
        self.projects[name] = project
        
        logger.info(f"Created project: {name}")
        
        return project
    
    async def define_development_tasks(self, project_name: str, requirements: List[str]) -> List[DevelopmentTask]:
        """Define development tasks based on requirements.
        
        Args:
            project_name: Name of the project.
            requirements: List of project requirements.
            
        Returns:
            List[DevelopmentTask]: The defined development tasks.
        """
        if project_name not in self.projects:
            raise ValueError(f"Project {project_name} not found")
        
        project = self.projects[project_name]
        tasks = []
        
        # Create a task for each requirement
        for i, requirement in enumerate(requirements):
            task_id = f"task-{i+1}"
            
            task = DevelopmentTask(
                id=task_id,
                title=f"Implement {requirement.split()[0]}",
                description=requirement,
                priority="medium",
                status="todo",
                dependencies=[],
                assigned_to=self.name
            )
            
            tasks.append(task)
        
        # Update project tasks
        project.tasks.extend(tasks)
        
        logger.info(f"Defined {len(tasks)} development tasks for project {project_name}")
        
        return tasks
    
    async def implement_task(self, project_name: str, task_id: str) -> CodeArtifact:
        """Implement a development task.
        
        Args:
            project_name: Name of the project.
            task_id: ID of the task to implement.
            
        Returns:
            CodeArtifact: The code artifact produced.
        """
        if project_name not in self.projects:
            raise ValueError(f"Project {project_name} not found")
        
        project = self.projects[project_name]
        
        # Find the task
        task = next((t for t in project.tasks if t.id == task_id), None)
        if not task:
            raise ValueError(f"Task {task_id} not found in project {project_name}")
        
        # Update task status
        task.status = "in_progress"
        logger.info(f"Implementing task {task_id}: {task.title}")
        
        # Research coding patterns for technologies used in the project
        research_tasks = []
        for technology in project.technologies[:2]:  # Limit to first 2 technologies
            research_tasks.append(self.research_coding_patterns(technology))
        
        # Collect research results
        research_results = await asyncio.gather(*research_tasks)
        
        # Generate a code artifact
        artifact = CodeArtifact(
            name=f"{task.title.replace(' ', '_').lower()}.py",
            path=f"src/{project_name.lower().replace(' ', '_')}/{task.title.replace(' ', '_').lower()}.py",
            language="Python",
            description=f"Implementation of {task.title}",
            dependencies=project.technologies[:2]  # Use first 2 technologies as dependencies
        )
        
        # Update task status and artifacts
        task.status = "done"
        task.artifacts.append(artifact)
        
        logger.info(f"Completed task {task_id}")
        
        return artifact
    
    async def create_github_repository(self, project_name: str) -> GitHubRepo:
        """Create a GitHub repository for a project.
        
        Args:
            project_name: Name of the project.
            
        Returns:
            GitHubRepo: The created GitHub repository.
        """
        if project_name not in self.projects:
            raise ValueError(f"Project {project_name} not found")
        
        project = self.projects[project_name]
        
        if not self.github_token:
            logger.warning("GitHub token not provided. Can't create repository.")
            return None
        
        # In a real implementation, we would use the GitHub API to create a repository
        # For demonstration purposes, we'll just create a mock repo object
        repo = GitHubRepo(
            name=project_name.lower().replace(" ", "-"),
            owner="roboco",
            url=f"https://github.com/roboco/{project_name.lower().replace(' ', '-')}",
            description=project.description,
            stars=0,
            forks=0,
            last_commit="today",
            languages=["Python"]
        )
        
        # Update project with repo info
        project.github_repo = repo
        
        logger.info(f"Created GitHub repository: {repo.url}")
        
        return repo
    
    async def generate_project_from_research(self, research_report: Dict[str, Any]) -> Project:
        """Generate a complete project from research findings.
        
        Args:
            research_report: The research report to base the project on.
            
        Returns:
            Project: The generated project.
        """
        # Extract project information from research report
        project_name = f"{research_report['report'].focus_area.title()} Implementation"
        description = research_report['report'].overview
        
        # Create project
        project = await self.create_project(project_name, description, research_report)
        
        # Define requirements based on research recommendations
        requirements = []
        if "recommendations" in research_report:
            for i, recommendation in enumerate(research_report["recommendations"][:5]):  # Take top 5 recommendations
                requirements.append(f"Implement {recommendation.get('title')} with {', '.join(project.technologies[:2]) if project.technologies else 'Python'}")
        
        # If no recommendations found, create placeholder requirements
        if not requirements:
            requirements = [
                "Implement core system architecture",
                "Implement data processing module",
                "Implement hardware interface"
            ]
        
        # Define development tasks
        tasks = await self.define_development_tasks(project_name, requirements)
        
        # Create GitHub repository
        repo = await self.create_github_repository(project_name)
        
        # Implement first task as demonstration
        if tasks:
            artifact = await self.implement_task(project_name, tasks[0].id)
        
        return project
    
    async def build_development_pipeline(self, research_agents: List[Agent], topic: str) -> Dict[str, Any]:
        """Build a complete development pipeline using research from multiple agents.
        
        Args:
            research_agents: List of research agents to use.
            topic: Topic to research and implement.
            
        Returns:
            Dict[str, Any]: The complete development pipeline results.
        """
        results = {}
        
        # Collect research from each agent
        research_tasks = []
        for agent in research_agents:
            if hasattr(agent, 'run_research_pipeline'):
                research_tasks.append(agent.run_research_pipeline(topic))
        
        # If no valid research agents found, return empty results
        if not research_tasks:
            logger.warning("No valid research agents found")
            return results
            
        # Gather research results
        research_results = await asyncio.gather(*research_tasks)
        
        # Merge research findings
        merged_research = research_results[0]  # Start with first result
        
        # Generate project from research
        project = await self.generate_project_from_research(merged_research)
        
        results = {
            "research": merged_research,
            "project": project,
            "github_repo": project.github_repo.dict() if project.github_repo else None,
            "tasks": [task.dict() for task in project.tasks]
        }
        
        return results
    
    async def cleanup(self):
        """Clean up resources used by the agent."""
        await self.browser_tool.cleanup()
        logger.info(f"Cleaned up {self.name} agent resources") 