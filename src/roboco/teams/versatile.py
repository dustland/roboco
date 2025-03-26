"""
Versatile Team Module

This module defines the VersatileTeam class, which provides a flexible and adaptable team implementation
with specialized roles designed to handle any type of task phase effectively.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from roboco.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

from roboco.core.project_fs import ProjectFS
from roboco.core.team import Team
from roboco.core.models import Task
from roboco.agents.human_proxy import HumanProxy
from roboco.core.agent_factory import AgentFactory
from autogen import AfterWork, AfterWorkOption, OnCondition, register_hand_off
from roboco.utils import ensure_directory


class VersatileTeam(Team):
    """
    A flexible and adaptable team with specialized roles that can handle any type of task.
    This team is designed to work effectively on task phases that don't clearly
    fit into specific categories like research, development, or design.
    
    Uses the AG2 swarm pattern for agent orchestration, allowing agents to collaborate
    with automatic handoffs based on conditions.
    """
    
    def __init__(
        self,
        fs: ProjectFS,
        config_path: Optional[str] = None
    ):
        """Initialize the versatile team with specialized roles.
        
        Args:
            workspace_dir: Directory for workspace files
            config_path: Optional path to team configuration file
        """
        super().__init__(name="VersatileTeam", config_path=config_path)
        self.fs = fs
        
        # Initialize the agents with specialized roles
        self._initialize_agents()
        
        # Register tools with agents
        self._register_tools()
        
        # Enable swarm capabilities
        self.enable_swarm()
        
        # Register handoffs for the swarm
        self._register_handoffs()
        
        logger.info(f"Initialized VersatileTeam with specialized roles in workspace: {self.fs.base_dir}")
    
    def _initialize_agents(self):
        """Initialize agents with specialized roles for the team."""
        agent_factory = AgentFactory()
        
        # Initialize each agent using the role configurations from roles.yaml
        architect = agent_factory.create_agent(
            role_key="architect",
            human_input_mode="NEVER",
            terminate_msg="ARCHITECTURE_COMPLETE"
        )
        
        strategist = agent_factory.create_agent(
            role_key="strategist", 
            human_input_mode="NEVER",
            terminate_msg="STRATEGY_COMPLETE"
        )
        
        explorer = agent_factory.create_agent(
            role_key="explorer",
            human_input_mode="NEVER",
            terminate_msg="EXPLORATION_COMPLETE"
        )
        
        creator = agent_factory.create_agent(
            role_key="creator",
            human_input_mode="NEVER",
            terminate_msg="CREATION_COMPLETE"
        )
        
        evaluator = agent_factory.create_agent(
            role_key="evaluator",
            human_input_mode="NEVER",
            terminate_msg="EVALUATION_COMPLETE"
        )
        
        synthesizer = agent_factory.create_agent(
            role_key="synthesizer",
            human_input_mode="NEVER",
            terminate_msg="SYNTHESIS_COMPLETE"
        )
        
        # Human Proxy - Interface for human input when needed
        human_proxy = HumanProxy(
            name="human_proxy",
            human_input_mode="TERMINATE"
        )
        
        # Add all agents to the team
        self.add_agent("architect", architect)
        self.add_agent("strategist", strategist)
        self.add_agent("explorer", explorer)
        self.add_agent("creator", creator)
        self.add_agent("evaluator", evaluator)
        self.add_agent("synthesizer", synthesizer)
        self.add_agent("human_proxy", human_proxy)
    
    def _register_tools(self):
        """Register necessary tools with the agents."""
        try:
            # Register filesystem tool with all agents
            from roboco.tools.fs import FileSystemTool
            # Create the filesystem tool with project context if available
            fs_tool = FileSystemTool(
                fs=self.fs, 
            )
            
            for agent_name, agent in self.agents.items():
                fs_tool.register_with_agents(agent)
            
            logger.info("Registered FileSystemTool with all agents")
            
            # Register web search tool if available
            try:
                from roboco.tools.web_search import WebSearchTool
                web_search_tool = WebSearchTool(
                    name="web_search",
                    description="Search the web for information"
                )
                
                # Register with explorer primarily, but also with architect for high-level information
                web_search_tool.register_with_agents(
                    self.get_agent("explorer"),
                    self.get_agent("architect")
                )
                logger.info("Registered WebSearchTool with explorer and architect")
            except ImportError:
                logger.warning("WebSearchTool not available")
            except Exception as e:
                logger.warning(f"Could not initialize WebSearchTool: {str(e)}")
            
            # Register code tool with creator and evaluator
            try:
                from roboco.tools.code import CodeTool
                code_tool = CodeTool(
                    fs=self.fs,
                    name="code",
                    description="Generate, validate, and execute code in multiple languages"
                )
                
                # Register with creator for implementation and evaluator for testing
                code_tool.register_with_agents(
                    self.get_agent("creator"),
                    self.get_agent("evaluator"),
                    self.get_agent("synthesizer")  # Also register with synthesizer for final integration
                )
                
                # Log available languages
                available_langs = ', '.join(code_tool.available_languages)
                logger.info(f"Registered CodeTool with creator, evaluator, and synthesizer. Available languages: {available_langs}")
            except ImportError:
                logger.warning("CodeTool not available")
            except Exception as e:
                logger.warning(f"Could not initialize CodeTool: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error registering tools: {str(e)}")
    
    def _register_handoffs(self):
        """Register handoffs between agents for the swarm pattern."""
        architect = self.get_agent("architect")
        strategist = self.get_agent("strategist")
        explorer = self.get_agent("explorer")
        creator = self.get_agent("creator")
        evaluator = self.get_agent("evaluator")
        synthesizer = self.get_agent("synthesizer")
        human_proxy = self.get_agent("human_proxy")
        
        # Register explicit, sequential handoffs for each agent
        # with minimal conditional logic to ensure proper flow
        
        # Architect always hands off to Strategist
        register_hand_off(architect, [
            # No conditions needed - always go to Strategist after Architecture is complete
            AfterWork(agent=strategist)
        ])
        
        # Strategist always hands off to Explorer 
        register_hand_off(strategist, [
            # No conditions needed - always go to Explorer after Strategy is complete
            AfterWork(agent=explorer)
        ])
        
        # Explorer always hands off to Creator
        register_hand_off(explorer, [
            # No conditions needed - always go to Creator after Exploration is complete
            AfterWork(agent=creator)
        ])
        
        # Creator always hands off to Evaluator
        register_hand_off(creator, [
            # No conditions needed - always go to Evaluator after Creation is complete
            AfterWork(agent=evaluator)
        ])
        
        # Evaluator always hands off to Synthesizer
        register_hand_off(evaluator, [
            # No conditions needed - always go to Synthesizer after Evaluation is complete
            AfterWork(agent=synthesizer)
        ])
        
        # Synthesizer ends the swarm when finished
        register_hand_off(synthesizer, [
            # No conditions needed - end the swarm after Synthesis is complete
            AfterWork(AfterWorkOption.TERMINATE)
        ])
        
        # Human proxy should defer to architect if something goes wrong
        register_hand_off(human_proxy, [
            AfterWork(agent=architect)
        ])
        
        logger.info("Registered handoffs for swarm pattern with linear flow")
    
    async def run_chat(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a chat session with all team members working together.
        
        This method uses swarm orchestration to enable all agents to collaborate
        on a task with automatic handoffs between agents.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the session results
        """
        # Convert string to Task
        from roboco.core.models import Task
        task = Task(description=query)
        
        # Define relative paths
        src_dir = "src"
        docs_dir = "docs"
        
        # Prepare the initial query
        query = f"""
        # Collaborative Task
        
        {task.description}
        
        # Expected Outcome
        {task.expected_outcome if hasattr(task, 'expected_outcome') else 'Complete the task successfully'}
        
        # Resources
        Workspace directory: {self.fs.base_dir} (this is already set up for you)
        Source code directory: {src_dir} (use this relative path, not absolute paths)
        Documentation directory: {docs_dir} (use this relative path, not absolute paths)
        
        # Process
        This is a collaborative effort where team members will work together:
        1. The Architect will design the overall solution framework
        2. The Strategist will develop the execution plan
        3. The Explorer will gather necessary information and research
        4. The Creator will implement the solution
           - For coding tasks, the Creator can use CodeTool to generate, validate, and execute code
           - All source code should be created in the source code directory
        5. The Evaluator will review and identify improvements
        6. The Synthesizer will integrate everything into a final deliverable
        
        # Important Instructions for All Agents
        - When you complete your phase, ALWAYS end your message with your assigned terminate message.
        - For example, Architect ends with "ARCHITECTURE_COMPLETE", Strategist with "STRATEGY_COMPLETE", etc.
        - Do not use these terminate messages in the middle of your contribution, only at the very end.
        - After your terminate message, the next appropriate agent will automatically be selected to continue.
        - All source code files should be created in the source code directory.
        - All documentation and planning files should be created in the documentation directory.
        - IMPORTANT: When using filesystem commands, always use relative paths like "src/file.py" or "docs/plan.md", NOT absolute paths.
        
        Let's work together to complete this task successfully.
        """
        
        # Run the swarm with the architect as the initial agent
        swarm_result = self.run_swarm(
            initial_agent_name="architect",
            query=query,
            context_variables={
                "task": task.dict() if hasattr(task, 'dict') else {"description": task.description},
                "src_dir": src_dir,
                "docs_dir": docs_dir
            },
            max_rounds=25
        )
        
        # Save the results
        # Create a file name based on the first few words of the description
        task_file_name = "_".join(task.description.split()[:5]).lower()
        task_file_name = "".join(c if c.isalnum() or c == "_" else "_" for c in task_file_name)
        results_path = os.path.join(self.fs.base_dir, docs_dir, f"{task_file_name}_collaborative_results.md")
        
        if "error" not in swarm_result:
            chat_result = swarm_result.get("chat_result", "")
            with open(results_path, "w") as f:
                f.write(f"# Collaborative Task Results\n\n")
                f.write(f"## Task Description\n{task.description}\n\n")
                f.write(f"## Solution\n{chat_result}\n\n")
            
            logger.info(f"Collaborative session completed and results saved to {results_path}")
            
            # Format the response to match PlanningTeam's run_chat format
            return {
                "response": chat_result,
                "chat_history": swarm_result.get("messages", []),
                "results_path": results_path,
                "status": "completed"
            }
        else:
            logger.error(f"Error in collaborative session: {swarm_result.get('error')}")
            return {
                "error": swarm_result.get('error', "Unknown error in collaborative session"),
                "status": "failed"
            }