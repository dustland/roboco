"""
Planning Team

This module provides a team of agents for project planning,
including requirements gathering, design, and implementation planning.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger

from roboco.core.team import Team
from roboco.core.team_loader import TeamLoader

class PlanningTeam(Team):
    """Team of agents that collaborate on planning a project."""
    
    def __init__(
        self,
        name: str = "PlanningTeam",
        agents: Dict[str, Any] = None,
        tools: List[Any] = None,
        roles_config_path: str = "config/roles.yaml",
        prompts_dir: str = "config/prompts",
        orchestrator_name: str = None
    ):
        """Initialize the planning team.
        
        Args:
            name: Name of the team
            agents: Dictionary of agents (optional)
            tools: List of tools available to the team (optional)
            roles_config_path: Path to the roles configuration file
            prompts_dir: Directory containing markdown files with detailed role prompts
            orchestrator_name: Name of the agent to use as orchestrator
        """
        super().__init__(name=name, agents=agents or {}, orchestrator_name=orchestrator_name)
        
        # Initialize attributes
        self.roles_config_path = roles_config_path
        self.prompts_dir = prompts_dir
        self.tools = tools or []
        
        # Build the team if no agents were provided
        if not agents:
            self._build_team()
            
        # Register handoffs between agents
        self._register_handoffs()
            
    def _build_team(self):
        """Build the team using the TeamBuilder."""
        # Create team builder with specialized agents
        builder = TeamBuilder(
            roles_config_path=self.roles_config_path,
            prompts_dir=self.prompts_dir,
            use_specialized_agents=True
        )
        
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
        from roboco.tools.file_system import FileSystemTool
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
            
    def plan(self, vision_statement: str) -> Dict[str, Any]:
        """Execute the planning process with the given vision statement.
        
        Args:
            vision_statement: The vision statement to plan around
            
        Returns:
            The planning outputs (plan documents)
        """
        # Get the starting agent (typically the product manager)
        if "Product Manager" in self.agents:
            starter = self.get_agent("Product Manager")
        else:
            starter = self.get_agent(list(self.agents.keys())[0])
            
        # Start the process with the vision statement
        request = f"""
        Create a complete planning document suite in the workspace/plan directory with the following:
        
        1. vision.md - Detailed vision document describing the project goals, scope, and success criteria
        2. technical_strategy.md - Technical approach, architecture, and technology choices
        3. implementation_plan.md - Implementation phases, tasks, and timeline
        4. risk_assessment.md - Potential risks, mitigation strategies, and contingency plans
        
        Start with this vision statement as your foundation:
        
        {vision_statement}
        
        Each document should be thorough and well-structured. Use markdown format.
        """
        
        # Run the planning process
        result = self.run_swarm(starter, request)
        
        return result

    async def create_planning_suite(self, vision: str) -> Dict[str, Any]:
        """Create a complete planning document suite based on a high-level vision.
        
        Args:
            vision: The high-level vision or goal for the project
            
        Returns:
            Dictionary with paths to the created planning documents
        """
        # Get task definition from config
        task_config = self.team_config.get("tasks", {}).get("create_planning_suite", {})
        
        # Get initial agent and max rounds from config or use defaults
        initial_agent_role = task_config.get("initial_agent", "product_manager")
        initial_agent_name = next((a.name for a in self.agents.values() 
                                 if a.system_message.lower().startswith(f"you are the {initial_agent_role}")),
                                self.agents.keys()[0])
        max_rounds = task_config.get("max_rounds", 12)
        
        # Get prompt template from config or use default
        prompt_template = task_config.get("prompt_template", """
        Based on this vision: "{vision}"

        Please create a complete planning document suite in the {output_dir} directory that includes:
        1. vision.md - A clear vision statement with objectives and success criteria
        2. technical_strategy.md - Technical approach and architecture
        3. implementation_plan.md - Detailed implementation plan with timelines
        4. risk_assessment.md - Assessment of risks and mitigation strategies

        Each document should be thorough, well-structured, and follow best practices for software project planning.
        """)
        
        # Format the query with the vision and output directory
        query = prompt_template.format(vision=vision, output_dir=self.output_dir)
        
        # Run the swarm with the configured initial agent
        logger.info(f"Starting planning process for vision: {vision[:50]}...")
        result = self.run_swarm(
            initial_agent_name=initial_agent_name,
            query=query,
            max_rounds=max_rounds
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
        # Get task definition from config
        task_config = self.team_config.get("tasks", {}).get("improve_document", {})
        
        # Get initial agent and max rounds from config or use defaults
        initial_agent_role = task_config.get("initial_agent", "report_writer")
        initial_agent_name = next((a.name for a in self.agents.values() 
                                 if a.system_message.lower().startswith(f"you are the {initial_agent_role}")),
                                list(self.agents.keys())[0])
        max_rounds = task_config.get("max_rounds", 6)
        
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
        
        # Get prompt template from config or use default
        prompt_template = task_config.get("prompt_template", """
        I need you to improve the {document_name} document based on this feedback:

        {feedback}

        The current document content is:

        {document_content}

        Please review the document, apply the feedback, and create an improved version that addresses all the points raised.
        Save the improved document back to {document_path}.
        """)
        
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
            max_rounds=max_rounds
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