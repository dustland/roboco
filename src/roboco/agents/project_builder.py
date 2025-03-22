"""
Project Agent Module

This module defines the ProjectBuilder class, which specializes in project creation,
structuring, and orchestrating team collaborations. It serves as the interface between 
users and the project management system.
"""

from typing import Dict, Any, List, Optional, Union, Callable
from loguru import logger
import os
from pathlib import Path
import asyncio

from autogen import ConversableAgent

from roboco.core.agent import Agent
from roboco.core.project_manager import ProjectManager
from roboco.core.team import Team
from roboco.agents.human_proxy import HumanProxy

class ProjectBuilder(Agent):
    """Agent specialized in project creation.
    
    This agent extends the base Agent class to provide specialized capabilities
    for creating and managing projects based on natural language queries.
    It interfaces with the ProjectManager to handle project operations and
    orchestrates team collaborations in a sequential workflow.
    
    The ProjectBuilder can:
    1. Analyze queries to determine appropriate project structures
    2. Create new projects with relevant teams and initial tasks
    3. Make recommendations on project organization
    4. Suggest appropriate tasks and sprints for different project types
    5. Orchestrate team collaborations in a sequential workflow
    6. Manage multiple sprints based on the results of previous sprints
    """
    
    def __init__(
        self, 
        name: str = "project_builder",
        project_manager: Optional[ProjectManager] = None,
        workspace_dir: str = "workspace",
        **kwargs
    ):
        """Initialize the ProjectBuilder.
        
        Args:
            name: Name of the agent
            project_manager: ProjectManager instance to use (creates new one if None)
            workspace_dir: Directory for workspace files
            **kwargs: Additional arguments to pass to the base Agent constructor
        """
        # Enhance the system message with project-specific instructions
        system_message = kwargs.pop("system_message", "")
        project_system_message = """
        You are a Project Builder specialized in creating and orchestrating projects.
        
        Your responsibilities include:
        - Analyzing user queries to determine appropriate project structures
        - Creating new projects with the right teams and initial tasks
        - Making recommendations on project organization
        - Suggesting appropriate tasks and sprints for different project types
        - Orchestrating team collaborations in a sequential workflow
        - Managing multiple sprints based on the results of previous sprints
        
        When a user asks you to create a project:
        1. First understand their needs and project type (research, development, design)
        2. Determine appropriate teams to assign based on the project nature
        3. Create a well-structured project with meaningful initial tasks
        4. Explain the structure you've created and why it suits their needs
        5. Plan the team collaboration workflow, where each team builds on the results of the previous team
        6. Organize the work into sprints, where each sprint builds on the results of the previous sprint
        
        Always aim to create project structures that are:
        - Well-organized and easy to navigate
        - Appropriately staffed with the right teams
        - Initialized with meaningful tasks and sprints
        - Aligned with the user's stated goals
        - Structured for efficient team collaboration
        """
        
        # Combine system messages
        if system_message:
            combined_system_message = f"{system_message}\n\n{project_system_message}"
        else:
            combined_system_message = project_system_message
            
        # Pass the enhanced system message to the parent constructor
        super().__init__(
            name=name,
            system_message=combined_system_message,
            **kwargs
        )
        
        # Initialize or store ProjectManager
        self.project_manager = project_manager or ProjectManager()
        self.workspace_dir = workspace_dir
        
        # Dictionary to store team instances
        self.teams: Dict[str, Team] = {}
        
        # Dictionary to store human proxy instances
        self.human_proxies: Dict[str, HumanProxy] = {}
        
        # Register core project management capabilities
        self._register_functions()
        
        logger.info(f"Initialized ProjectBuilder with name '{name}'")
    
    def _register_functions(self) -> None:
        """Register project management functions with the agent."""
        # Register core functions that will be available in conversations
        self.register_function(
            self.create_project_from_query,
            name="create_project",
            description="Create a new project from a natural language query",
        )
        
        self.register_function(
            self.list_available_projects,
            name="list_projects",
            description="List all available projects",
        )
        
        self.register_function(
            self.get_project_details,
            name="project_details",
            description="Get detailed information about a specific project",
        )
        
        self.register_function(
            self.create_team_for_project,
            name="create_team",
            description="Create a team for a specific project",
        )
        
        self.register_function(
            self.run_team_collaboration,
            name="run_team",
            description="Run a team collaboration for a specific project",
        )
        
        self.register_function(
            self.create_sprint,
            name="create_sprint",
            description="Create a new sprint for a project",
        )
        
        self.register_function(
            self.run_sprint,
            name="run_sprint",
            description="Run a sprint for a project, executing all team collaborations in sequence",
        )
    
    async def create_project_from_query(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a project from a natural language query.
        
        Args:
            query: The user's query describing the project
            teams: Optional list of teams to assign to the project
            
        Returns:
            Dict containing project details
        """
        try:
            # Use the project manager to create a project
            project_id = await self.project_manager.create_project_from_query(query, teams)
            
            # Retrieve the created project
            project = self.project_manager.get_project(project_id)
            if not project:
                return {"error": "Failed to retrieve created project"}
            
            # Create project workspace directory
            project_workspace = os.path.join(self.workspace_dir, project.directory)
            os.makedirs(project_workspace, exist_ok=True)
            
            # Return project details
            return {
                "id": project_id,
                "name": project.name,
                "description": project.description,
                "teams": project.teams,
                "directory": project.directory,
                "workspace": project_workspace,
                "current_sprint": project.current_sprint,
                "tags": project.tags,
                "sprints_count": len(project.sprints),
                "todos_count": len(project.todos) + sum(len(sprint.todos) for sprint in project.sprints)
            }
        except Exception as e:
            logger.error(f"Error creating project from query: {str(e)}")
            return {"error": str(e)}
    
    def list_available_projects(self) -> List[Dict[str, Any]]:
        """List all available projects.
        
        Returns:
            List of project summary dictionaries
        """
        return self.project_manager.list_projects()
    
    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific project.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            Dict containing project details
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Get detailed sprint information
        sprints = []
        for sprint in project.sprints:
            sprint_info = sprint.model_dump()
            sprint_info["todos_count"] = len(sprint.todos)
            # Remove the full todos list to keep response size manageable
            sprint_info.pop("todos", None)
            sprints.append(sprint_info)
        
        # Return project details 
        return {
            "id": project_id,
            "name": project.name,
            "description": project.description,
            "directory": project.directory,
            "teams": project.teams,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "current_sprint": project.current_sprint,
            "tags": project.tags,
            "sprints": sprints,
            "todos_count": len(project.todos),
            "jobs_count": len(project.jobs)
        }
    
    def create_team_for_project(
        self, 
        project_id: str, 
        team_name: str, 
        team_type: str, 
        description: str = "",
        roles: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a team for a specific project.
        
        Args:
            project_id: ID of the project
            team_name: Name of the team
            team_type: Type of team to create (e.g., "research", "development")
            description: Description of the team's purpose
            roles: Optional list of roles for the team
            config: Optional additional configuration for the team
            
        Returns:
            Dict containing team details
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Create team instance based on team_type
        try:
            # Define team key for storage
            team_key = f"{project_id}_{team_name}"
            
            # Create team instance (implementation will vary based on team_type)
            # This is a simplified version - in a real implementation, you would
            # dynamically import and instantiate the appropriate team class
            team = Team(name=team_name)
            
            # Store the team instance
            self.teams[team_key] = team
            
            # Add the team to the project
            if team_name not in project.teams:
                project.teams.append(team_name)
                self.project_manager._save_project(project_id)
            
            return {
                "team_key": team_key,
                "name": team_name,
                "type": team_type,
                "description": description,
                "project_id": project_id,
                "project_name": project.name
            }
        except Exception as e:
            logger.error(f"Error creating team: {str(e)}")
            return {"error": str(e)}
    
    async def run_team_collaboration(
        self, 
        project_id: str, 
        team_name: str, 
        query: str,
        context: Optional[Dict[str, Any]] = None,
        max_rounds: int = 10
    ) -> Dict[str, Any]:
        """Run a team collaboration for a specific project.
        
        Args:
            project_id: ID of the project
            team_name: Name of the team to run
            query: The query or task for the team
            context: Optional context variables for the team
            max_rounds: Maximum number of conversation rounds
            
        Returns:
            Dict containing the results of the team collaboration
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Get the team instance
        team_key = f"{project_id}_{team_name}"
        team = self.teams.get(team_key)
        if not team:
            return {"error": f"Team {team_name} not found for project {project_id}"}
        
        try:
            # Set up context with project information
            full_context = context or {}
            full_context.update({
                "project_id": project_id,
                "project_name": project.name,
                "project_description": project.description,
                "project_directory": project.directory,
                "workspace_dir": os.path.join(self.workspace_dir, project.directory)
            })
            
            # Run the team collaboration
            # Determine the initial agent based on team configuration
            initial_agent = next(iter(team.agents.keys())) if team.agents else None
            if not initial_agent:
                return {"error": f"No agents found in team {team_name}"}
            
            # Run the swarm
            result = team.run_swarm(
                initial_agent_name=initial_agent,
                query=query,
                context_variables=full_context,
                max_rounds=max_rounds
            )
            
            # Save the result to the project
            result_summary = {
                "team_name": team_name,
                "query": query,
                "context": full_context,
                "result": result
            }
            
            return result_summary
        except Exception as e:
            logger.error(f"Error running team collaboration: {str(e)}")
            return {"error": str(e)}
    
    def create_sprint(
        self, 
        project_id: str, 
        sprint_name: str, 
        description: str,
        team_sequence: List[str]
    ) -> Dict[str, Any]:
        """Create a new sprint for a project.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            description: Description of the sprint goals
            team_sequence: Ordered list of team names to run in sequence
            
        Returns:
            Dict containing sprint details
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Validate that all teams exist
        for team_name in team_sequence:
            team_key = f"{project_id}_{team_name}"
            if team_key not in self.teams:
                return {"error": f"Team {team_name} not found for project {project_id}"}
        
        try:
            # Create the sprint using the project manager
            sprint = self.project_manager.create_sprint(
                project_id=project_id,
                name=sprint_name,
                description=description
            )
            
            if not sprint:
                return {"error": f"Failed to create sprint {sprint_name}"}
            
            # Store the team sequence as a tag on the sprint
            # This is a workaround since the Sprint model doesn't have a field for team sequence
            team_sequence_tag = f"team_sequence:{','.join(team_sequence)}"
            if team_sequence_tag not in sprint.tags:
                sprint.tags.append(team_sequence_tag)
            
            # Set as current sprint if no current sprint is set
            if not project.current_sprint:
                self.project_manager.update_project(project_id, current_sprint=sprint_name)
            
            # Save the project
            self.project_manager._save_project(project_id)
            
            return {
                "sprint_name": sprint_name,
                "description": description,
                "team_sequence": team_sequence,
                "project_id": project_id,
                "project_name": project.name,
                "start_date": sprint.start_date,
                "end_date": sprint.end_date
            }
        except Exception as e:
            logger.error(f"Error creating sprint: {str(e)}")
            return {"error": str(e)}
    
    async def run_sprint(
        self, 
        project_id: str, 
        sprint_name: str, 
        initial_query: str,
        context: Optional[Dict[str, Any]] = None,
        max_rounds_per_team: int = 10
    ) -> Dict[str, Any]:
        """Run a sprint for a project, executing all team collaborations in sequence.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint to run
            initial_query: The initial query or task for the sprint
            context: Optional initial context variables
            max_rounds_per_team: Maximum number of conversation rounds per team
            
        Returns:
            Dict containing the results of the sprint
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": f"Project with ID {project_id} not found"}
        
        # Find the sprint
        sprint = None
        for s in project.sprints:
            if s.name == sprint_name:
                sprint = s
                break
        
        if not sprint:
            return {"error": f"Sprint {sprint_name} not found for project {project_id}"}
        
        # Extract team sequence from tags
        team_sequence = []
        for tag in sprint.tags:
            if tag.startswith("team_sequence:"):
                team_sequence = tag.split(":", 1)[1].split(",")
                break
        
        if not team_sequence:
            return {"error": f"No team sequence found for sprint {sprint_name}"}
        
        try:
            # Initialize context
            current_context = context or {}
            current_context.update({
                "project_id": project_id,
                "project_name": project.name,
                "project_description": project.description,
                "sprint_name": sprint_name,
                "sprint_description": sprint.description,
                "workspace_dir": os.path.join(self.workspace_dir, project.directory)
            })
            
            # Initialize query
            current_query = initial_query
            
            # Store results for each team
            team_results = {}
            
            # Run each team in sequence
            for team_name in team_sequence:
                logger.info(f"Running team {team_name} for sprint {sprint_name}")
                
                # Run the team collaboration
                team_result = await self.run_team_collaboration(
                    project_id=project_id,
                    team_name=team_name,
                    query=current_query,
                    context=current_context,
                    max_rounds=max_rounds_per_team
                )
                
                # Store the result
                team_results[team_name] = team_result
                
                # Update context with team result for the next team
                if "result" in team_result and "context" in team_result["result"]:
                    current_context.update(team_result["result"]["context"])
                
                # Update query for the next team based on the result
                # This is a simplified approach - in a real implementation,
                # you would have a more sophisticated way to generate the next query
                if "result" in team_result and "chat_result" in team_result["result"]:
                    # Extract the last message from the chat result
                    chat_result = team_result["result"]["chat_result"]
                    if isinstance(chat_result, list) and chat_result:
                        last_message = chat_result[-1].get("content", "")
                        current_query = f"Based on the previous team's work: {last_message[:500]}..., continue with: {initial_query}"
            
            # Mark the sprint as completed
            self.project_manager.update_sprint(
                project_id=project_id,
                sprint_name=sprint_name,
                status="completed"
            )
            
            # Return the results of all team collaborations
            return {
                "project_id": project_id,
                "project_name": project.name,
                "sprint_name": sprint_name,
                "team_sequence": team_sequence,
                "team_results": team_results,
                "final_context": current_context
            }
        except Exception as e:
            logger.error(f"Error running sprint: {str(e)}")
            return {"error": str(e)}
    
    async def create_and_run_project(
        self,
        query: str,
        teams: Optional[List[str]] = None,
        sprint_name: str = "Sprint 1",
        sprint_description: str = "Initial project sprint"
    ) -> Dict[str, Any]:
        """Create a project and run the initial sprint in one operation.
        
        This is a convenience method that combines project creation, team setup,
        sprint creation, and sprint execution into a single operation.
        
        Args:
            query: The user's query describing the project
            teams: Optional list of teams to assign to the project
            sprint_name: Name for the initial sprint
            sprint_description: Description for the initial sprint
            
        Returns:
            Dict containing the results of the project creation and sprint execution
        """
        try:
            # Create the project
            project_result = await self.create_project_from_query(query, teams)
            if "error" in project_result:
                return project_result
            
            project_id = project_result["id"]
            
            # Create teams for the project
            # This is a simplified approach - in a real implementation,
            # you would dynamically determine the appropriate teams based on the project
            team_results = []
            team_sequence = []
            
            for team_type in teams or ["research", "development"]:
                team_name = f"{team_type}_team"
                team_result = self.create_team_for_project(
                    project_id=project_id,
                    team_name=team_name,
                    team_type=team_type,
                    description=f"{team_type.capitalize()} team for {project_result['name']}"
                )
                team_results.append(team_result)
                team_sequence.append(team_name)
            
            # Create the sprint
            sprint_result = self.create_sprint(
                project_id=project_id,
                sprint_name=sprint_name,
                description=sprint_description,
                team_sequence=team_sequence
            )
            
            if "error" in sprint_result:
                return {
                    "project": project_result,
                    "teams": team_results,
                    "sprint_error": sprint_result["error"]
                }
            
            # Run the sprint
            sprint_execution = await self.run_sprint(
                project_id=project_id,
                sprint_name=sprint_name,
                initial_query=query
            )
            
            # Return the combined results
            return {
                "project": project_result,
                "teams": team_results,
                "sprint": sprint_result,
                "sprint_execution": sprint_execution
            }
        except Exception as e:
            logger.error(f"Error creating and running project: {str(e)}")
            return {"error": str(e)}