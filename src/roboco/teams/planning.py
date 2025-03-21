"""
Planning Team

This module provides a team of agents for project planning,
including requirements gathering, design, and implementation planning.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger

from roboco.core import Team, TeamBuilder
from roboco.core.models import TeamConfig

class PlanningTeam(Team):
    """Team of agents that collaborate on planning a project."""
    
    def __init__(
        self,
        name: str = "PlanningTeam",
        agents: Dict[str, Any] = None,
        tools: List[Any] = None,
        roles_config_path: str = "config/roles.yaml",
        prompts_dir: str = "config/prompts",
        orchestrator_name: str = None,
        output_dir: str = "workspace/plan",
        team_config: Optional[TeamConfig] = None
    ):
        """Initialize the planning team.
        
        Args:
            name: Name of the team
            agents: Dictionary of agents (optional)
            tools: List of tools available to the team (optional)
            roles_config_path: Path to the roles configuration file
            prompts_dir: Directory containing markdown files with detailed role prompts
            orchestrator_name: Name of the agent to use as orchestrator
            output_dir: Directory to store created planning documents
            team_config: Optional TeamConfig instance for team configuration
        """
        super().__init__(name=name, agents=agents or {})
        
        # Store orchestrator name for later use
        self.orchestrator_name = orchestrator_name
        
        # Initialize attributes
        self.roles_config_path = roles_config_path
        self.prompts_dir = prompts_dir
        self.tools = tools or []
        self.output_dir = output_dir
        
        # Initialize team configuration
        if team_config:
            self.team_config = team_config
            # Override output_dir if specified in constructor
            if output_dir != "workspace/plan":
                self.output_dir = output_dir
            else:
                self.output_dir = team_config.output_dir
        else:
            self.team_config = TeamConfig(
                name=name,
                description="Team of agents that collaborate on planning a project",
                roles=["executive", "product_manager", "software_engineer", "report_writer"],
                tool_executor="human_proxy",
                output_dir=output_dir,
                orchestrator_name=orchestrator_name
            )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Build the team if no agents were provided
        if not agents:
            self._build_team()
            
        # Register handoffs between agents
        self._register_handoffs()
            
    def _build_team(self):
        """Build the team using the TeamBuilder."""
        # Get TeamBuilder singleton instance
        builder = TeamBuilder.get_instance()
        
        # Define the roles in the team
        builder.with_roles(
            "executive",
            "product_manager",
            "software_engineer",
            "report_writer"
        )
        
        # Set up the tool executor (human proxy)
        builder.with_tool_executor("human_proxy")
        
        # Add file system tools to the human proxy
        from roboco.tools.fs import FileSystemTool
        builder.with_tools("human_proxy", [FileSystemTool()])
        
        # Define the workflow as a circular sequence
        builder.with_circular_workflow(
            "product_manager",
            "software_engineer",
            "report_writer",
            "executive"
        )
        
        # Build the team
        team = builder.build()
        
        # Add all agents to this team
        for name, agent in team.agents.items():
            self.add_agent(name, agent)
        
        # Enable swarm orchestration
        self.enable_swarm()
        
    def _register_handoffs(self):
        """Register handoffs between agents if using direct initialization.
        
        This method is used when the team is created directly rather than
        through the TeamBuilder. It defines the handoffs between agents.
        """
        # Import required modules
        from autogen import register_hand_off, AfterWork
        
        # Get list of agent names (excluding the human proxy)
        agent_names = [name for name in self.agents if "human" not in name.lower()]
        
        # Create a circular workflow
        for i, name in enumerate(agent_names):
            next_name = agent_names[(i + 1) % len(agent_names)]
            from_agent = self.get_agent(name)
            to_agent = self.get_agent(next_name)
            
            # Register the handoff
            register_hand_off(
                agent=from_agent,
                hand_to=AfterWork(agent=to_agent)
            )
            
        logger.info(f"Registered basic handoff workflow with {len(agent_names)} agents")

    async def create_planning_suite(self, vision: str) -> Dict[str, Any]:
        """Create a complete planning document suite based on a high-level vision.
        
        Args:
            vision: The high-level vision or goal for the project
            
        Returns:
            Dictionary with paths to the created planning documents
        """
        # Find the initial agent (product manager)
        initial_agent_name = None
        for agent in self.agents.values():
            if agent.system_message.lower().startswith("you are the product_manager"):
                initial_agent_name = agent.name
                break
                
        if not initial_agent_name and self.agents:
            initial_agent_name = list(self.agents.keys())[0]
        
        # Create a prompt for the planning task
        prompt_template = f"""
        Based on this vision: "{{vision}}"

        Please create a complete planning document suite in the {self.output_dir} directory that includes:
        1. vision.md - A clear vision statement with objectives and success criteria
        2. technical_strategy.md - Technical approach and architecture
        3. implementation_plan.md - Detailed implementation plan with timelines
        4. risk_assessment.md - Assessment of risks and mitigation strategies
        
        Each document should be thorough, well-structured, and follow best practices for software project planning.
        """
        
        # Format the query with the vision
        query = prompt_template.format(vision=vision)
        
        # Run the swarm with the configured initial agent
        logger.info(f"Starting planning process for vision: {vision[:50]}...")
        result = self.run_swarm(
            initial_agent_name=initial_agent_name,
            query=query,
            max_rounds=12  # Default max rounds
        )
        
        # Collect information about the created files
        created_files = []
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.md'):
                    created_files.append(filename)
        
        # Return summary of results
        return {
            "success": len(created_files) > 0,
            "output_dir": self.output_dir,
            "created_files": created_files,
            "conversation_history": result.get("history", []),
            "swarm_rounds": result.get("rounds", 0)
        }
    
    async def improve_planning_document(self, document_name: str, feedback: str) -> Dict[str, Any]:
        """Improve an existing planning document based on feedback.
        
        Args:
            document_name: Name of the document to improve (e.g., "vision.md")
            feedback: Detailed feedback for improvements
            
        Returns:
            Dictionary with information about the improved document
        """
        # Find the initial agent (report writer is good for improvements)
        initial_agent_name = None
        for agent in self.agents.values():
            if agent.system_message.lower().startswith("you are the report_writer"):
                initial_agent_name = agent.name
                break
                
        if not initial_agent_name and self.agents:
            initial_agent_name = list(self.agents.keys())[0]
        
        # Construct full path to the document
        document_path = os.path.join(self.output_dir, document_name)
        
        # Check if document exists
        if not os.path.exists(document_path):
            return {
                "success": False,
                "error": f"Document {document_name} not found in {self.output_dir}"
            }
        
        # Read the current document
        document_content = ""
        try:
            with open(document_path, 'r', encoding='utf-8') as file:
                document_content = file.read()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read document: {str(e)}"
            }
        
        # Update shared context
        self.shared_context.update({
            "current_plan": document_content,
            "feedback": feedback,
            "document_name": document_name,
            "document_path": document_path
        })
        
        # Create a prompt for the improvement task
        prompt_template = """
        I need you to improve the {document_name} document based on this feedback:

        {feedback}

        The current document content is:

        {document_content}

        Please review the document, apply the feedback, and create an improved version that addresses all the points raised.
        Save the improved document back to {document_path}.
        """
        
        # Format the query with the document details and feedback
        query = prompt_template.format(
            document_name=document_name,
            feedback=feedback,
            document_content=document_content,
            document_path=document_path
        )
        
        # Start with the configured initial agent
        logger.info(f"Starting improvement process for {document_name}")
        result = self.run_swarm(
            initial_agent_name=initial_agent_name,
            query=query,
            max_rounds=6  # Fewer rounds for improvement
        )
        
        # Check if file was modified
        try:
            with open(document_path, 'r', encoding='utf-8') as file:
                updated_content = file.read()
                
            was_modified = updated_content != document_content
            
            return {
                "success": was_modified,
                "document_name": document_name,
                "document_path": document_path,
                "was_modified": was_modified,
                "conversation_history": result.get("history", []),
                "swarm_rounds": result.get("rounds", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to verify document update: {str(e)}"
            }

if __name__ == "__main__":
    # Example usage
    async def run_example():
        planning_team = PlanningTeam()
        result = await planning_team.create_planning_suite(
            vision="Create a robot control system that can adapt to different environments and learn from experience"
        )
        print(f"Planning documents created: {result['created_files']}")
    
    # Run the example
    asyncio.run(run_example()) 