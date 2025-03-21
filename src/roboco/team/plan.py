"""
Planning Team Module

This module provides a team of agents that collaborate to create, review, and improve
project planning documents for software development and robotics projects.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from loguru import logger

from roboco.core.team import Team
from roboco.core.agent import Agent
from roboco.agents import Executive, ProductManager, SoftwareEngineer, ReportWriter
from roboco.tools.fs import FileSystemTool

class PlanningTeam(Team):
    """A team of agents that collaborate to create and improve project planning documents.
    
    This team consists of:
    - Executive: Provides strategic vision and final approval
    - Product Manager: Creates detailed plans based on vision
    - Software Engineer: Reviews plans for technical feasibility
    - Report Writer: Improves document clarity and structure
    
    The team works iteratively to generate, review, and refine planning documents
    that are stored in the workspace/plan directory.
    """
    
    def __init__(
        self,
        name: str = "PlanningTeam",
        config_path: Optional[str] = None,
        output_dir: str = "workspace/plan",
        **kwargs
    ):
        """Initialize the planning team.
        
        Args:
            name: Name of the team (default: PlanningTeam)
            config_path: Optional path to team configuration file
            output_dir: Directory where planning documents are stored
            **kwargs: Additional arguments passed to Team
        """
        super().__init__(name=name, agents={}, config_path=config_path, **kwargs)
        
        # Set up plan output directory
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Enable swarm orchestration with shared context
        self.enable_swarm(shared_context={
            "output_dir": self.output_dir,
            "current_plan": None,
            "revision_history": [],
            "feedback": []
        })
        
        # Initialize team members
        self._initialize_team_members()
        
        # Set up file system tool
        self.fs_tool = FileSystemTool()
        
        # Register the tool with all agents
        for agent in self.agents.values():
            self.fs_tool.register_with_agent(agent)
        
        # Register handoffs between agents for automatic swarm orchestration
        self._register_handoffs()
        
        logger.info(f"Initialized Planning Team with output directory: {self.output_dir}")
    
    def _create_executive(self, name, system_message, **kwargs):
        """Create an Executive agent, working around the tools parameter issue."""
        # Filter out any tools parameter to avoid the error
        if 'tools' in kwargs:
            del kwargs['tools']
        
        # Create and return the Executive agent
        executive = Executive(
            name=name,
            system_message=system_message,
            **kwargs
        )
        
        # Add to the team
        self.add_agent(name, executive)
        return executive
    
    def _initialize_team_members(self):
        """Initialize all team members with appropriate system messages."""
        
        # Executive agent for high-level vision and approval
        executive = self._create_executive(
            name="Executive",
            system_message="""You are the Executive agent responsible for setting the strategic vision and providing final approval on plans.
            Your role is to ensure plans align with the overall business goals and to provide high-level feedback.
            Contribute by setting clear objectives, priorities, and success criteria.
            When the planning document fully meets your requirements, provide your approval for implementation."""
        )
        
        # Product Manager for creating and managing plans
        product_manager = self.create_agent(
            agent_class=ProductManager,
            name="ProductManager",
            system_message="""You are the Product Manager agent responsible for creating detailed planning documents.
            Your role is to transform high-level vision into actionable plans with timelines, deliverables, and resource requirements.
            Create structured documents including vision statements, technical strategies, implementation plans, and risk assessments.
            When you have a complete draft, hand off to the SoftwareEngineer for technical review."""
        )
        
        # Software Engineer for technical review
        software_engineer = self.create_agent(
            agent_class=SoftwareEngineer,
            name="SoftwareEngineer",
            system_message="""You are the Software Engineer agent responsible for reviewing plans for technical feasibility.
            Your role is to assess technical aspects of plans, identify potential implementation challenges, and suggest solutions.
            Provide detailed feedback on architecture, technology choices, and implementation approaches.
            When your technical review is complete, hand off to the ReportWriter for clarity and structure improvements."""
        )
        
        # Report Writer for document quality and clarity
        report_writer = self.create_agent(
            agent_class=ReportWriter,
            name="ReportWriter",
            system_message="""You are the Report Writer agent responsible for improving document clarity and structure.
            Your role is to refine planning documents for readability, consistency, and professional presentation.
            Focus on clear headings, proper formatting, consistent terminology, and cohesive narrative flow.
            When you have improved the document, hand off to the Executive for final review and approval."""
        )
    
    def _register_handoffs(self):
        """Register handoffs between agents for automatic swarm transitions."""
        from autogen import register_hand_off, AfterWork
        
        # Define the work flow: ProductManager -> SoftwareEngineer -> ReportWriter -> Executive -> ProductManager
        handoff_chain = [
            self.get_agent("ProductManager"),
            self.get_agent("SoftwareEngineer"),
            self.get_agent("ReportWriter"),
            self.get_agent("Executive"),
        ]
        
        # Create circular handoffs
        for i, agent in enumerate(handoff_chain):
            next_agent = handoff_chain[(i + 1) % len(handoff_chain)]
            register_hand_off(
                agent=agent,
                hand_to=[AfterWork(agent=next_agent)]
            )
        
        logger.info(f"Registered handoffs between {len(handoff_chain)} agents")
    
    async def create_planning_suite(self, vision: str) -> Dict[str, Any]:
        """Create a complete planning document suite based on a high-level vision.
        
        Args:
            vision: The high-level vision or goal for the project
            
        Returns:
            Dictionary with paths to the created planning documents
        """
        # Prepare the initial query for the product manager
        query = f"""Based on this vision: "{vision}"

Please create a complete planning document suite in the workspace/plan directory that includes:
1. vision.md - A clear vision statement with objectives and success criteria
2. technical_strategy.md - Technical approach and architecture
3. implementation_plan.md - Detailed implementation plan with timelines
4. risk_assessment.md - Assessment of risks and mitigation strategies

Each document should be thorough, well-structured, and follow best practices for software project planning.
"""
        
        # Run the swarm with the product manager as the starting agent
        logger.info(f"Starting planning process for vision: {vision[:50]}...")
        result = self.run_swarm(
            initial_agent_name="ProductManager",
            query=query,
            max_rounds=12  # Allow multiple review cycles
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
        
        # Prepare query for improvement
        query = f"""I need you to improve the {document_name} document based on this feedback:

{feedback}

The current document content is:

{document_content}

Please review the document, apply the feedback, and create an improved version that addresses all the points raised.
Save the improved document back to {document_path}.
"""
        
        # Start with the ReportWriter for document improvements
        logger.info(f"Starting improvement process for {document_name}")
        result = self.run_swarm(
            initial_agent_name="ReportWriter",
            query=query,
            max_rounds=6
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
