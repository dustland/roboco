"""
Versatile Team Module

This module defines the VersatileTeam class, which provides a flexible and adaptable team implementation
with specialized roles designed to handle any type of task phase effectively.
"""

import os
from typing import Dict, Any, List, Optional, Union
from roboco.core.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

from roboco.core.team import Team
from roboco.core.agent import Agent
from roboco.core.schema import Task
from roboco.agents.human_proxy import HumanProxy


class VersatileTeam(Team):
    """
    A flexible and adaptable team with specialized roles that can handle any type of task.
    This team is designed to work effectively on task phases that don't clearly
    fit into specific categories like research, development, or design.
    """
    
    def __init__(
        self,
        workspace_dir: str = "workspace",
        config_path: Optional[str] = None
    ):
        """Initialize the versatile team with specialized roles.
        
        Args:
            workspace_dir: Directory for workspace files
            config_path: Optional path to team configuration file
        """
        super().__init__(name="VersatileTeam", config_path=config_path)
        self.workspace_dir = workspace_dir
        
        # Initialize the agents with specialized roles
        self._initialize_agents()
        
        # Register tools with agents
        self._register_tools()
        
        logger.info(f"Initialized VersatileTeam with specialized roles in workspace: {workspace_dir}")
    
    def _initialize_agents(self):
        """Initialize agents with specialized roles for the team."""
        
        # Architect - Designs solutions and oversees the big picture
        architect = Agent(
            name="architect",
            system_message="""You are the Architect of the team, responsible for designing solutions and overseeing the big picture.
            Your primary responsibilities include:
            1. Understanding the task requirements in depth
            2. Creating high-level designs and architectural frameworks
            3. Making key decisions about approach and methodology
            4. Ensuring all components work together cohesively
            5. Balancing technical constraints with business needs
            
            You excel at systems thinking, creating elegant solutions, and communicating complex concepts clearly.
            Your aim is to design solutions that are robust, scalable, and maintainable.
            """,
            human_input_mode="NEVER",
            terminate_msg="ARCHITECTURE_COMPLETE"
        )
        
        # Strategist - Plans execution and identifies resources
        strategist = Agent(
            name="strategist",
            system_message="""You are the Strategist of the team, responsible for planning execution and identifying resources.
            Your primary responsibilities include:
            1. Breaking down complex tasks into actionable steps
            2. Creating detailed execution plans with clear milestones
            3. Identifying required resources and potential constraints
            4. Prioritizing tasks and establishing dependencies
            5. Developing contingency plans for potential obstacles
            
            You excel at analytical thinking, resource optimization, and structured planning.
            Your aim is to create practical, efficient plans that maximize chances of success.
            """,
            human_input_mode="NEVER",
            terminate_msg="STRATEGY_COMPLETE"
        )
        
        # Explorer - Researches and discovers relevant information
        explorer = Agent(
            name="explorer",
            system_message="""You are the Explorer of the team, responsible for researching and discovering relevant information.
            Your primary responsibilities include:
            1. Conducting comprehensive research on the task domain
            2. Gathering relevant data, evidence, and context
            3. Identifying existing solutions and best practices
            4. Exploring innovative approaches and alternatives
            5. Validating information sources and assessing credibility
            
            You excel at information gathering, pattern recognition, and knowledge synthesis.
            Your aim is to provide well-researched, accurate insights that expand the team's understanding.
            """,
            human_input_mode="NEVER",
            terminate_msg="EXPLORATION_COMPLETE"
        )
        
        # Creator - Implements solutions and produces deliverables
        creator = Agent(
            name="creator",
            system_message="""You are the Creator of the team, responsible for implementing solutions and producing deliverables.
            Your primary responsibilities include:
            1. Transforming designs and plans into concrete outputs
            2. Creating high-quality deliverables that meet specifications
            3. Developing prototypes and functional implementations
            4. Bringing concepts to life with attention to detail
            5. Adapting to feedback and iterating on solutions
            
            You excel at execution, craftsmanship, and technical problem-solving.
            For programming tasks, you can write code in multiple languages and ensure it works correctly.
            Use available code tools to generate, validate, and execute code as needed.
            
            Your aim is to produce well-crafted, functional outputs that fulfill requirements.
            """,
            human_input_mode="NEVER",
            terminate_msg="CREATION_COMPLETE"
        )
        
        # Evaluator - Reviews, tests, and refines solutions
        evaluator = Agent(
            name="evaluator",
            system_message="""You are the Evaluator of the team, responsible for reviewing, testing, and refining solutions.
            Your primary responsibilities include:
            1. Critically assessing deliverables against requirements
            2. Identifying potential issues, risks, and improvements
            3. Testing functionality and validating assumptions
            4. Providing constructive feedback with specific recommendations
            5. Ensuring quality standards are met or exceeded
            
            For code evaluation, you can use available tools to validate code and identify issues.
            Focus on ensuring code is functional, efficient, and meets requirements.
            
            You excel at critical thinking, quality assessment, and solution refinement.
            Your aim is to ensure deliverables are robust, effective, and meet all requirements.
            """,
            human_input_mode="NEVER",
            terminate_msg="EVALUATION_COMPLETE"
        )
        
        # Synthesizer - Integrates components and creates final deliverables
        synthesizer = Agent(
            name="synthesizer",
            system_message="""You are the Synthesizer of the team, responsible for integrating components and creating final deliverables.
            Your primary responsibilities include:
            1. Combining individual contributions into cohesive deliverables
            2. Ensuring consistency across all components
            3. Resolving conflicts and addressing feedback
            4. Creating polished, professional final outputs
            5. Communicating results effectively to stakeholders
            
            You excel at integration, refinement, and clear communication.
            Your aim is to produce comprehensive, unified deliverables that exceed expectations.
            """,
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
            fs_tool = FileSystemTool(workspace_dir=self.workspace_dir)
            
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
                    workspace_dir=os.path.join(self.workspace_dir, "code"),
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
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task using the team's specialized roles.
        
        Args:
            task: The task to execute
            
        Returns:
            Dict containing the task execution results
        """
        logger.info(f"Starting execution of task: {task.title}")
        
        architect = self.get_agent("architect")
        strategist = self.get_agent("strategist")
        explorer = self.get_agent("explorer")
        creator = self.get_agent("creator")
        evaluator = self.get_agent("evaluator")
        synthesizer = self.get_agent("synthesizer")
        
        task_prompt = f"""
        # Task Description
        {task.description}
        
        # Expected Outcome
        {task.expected_outcome if hasattr(task, 'expected_outcome') else 'Complete the task successfully'}
        
        # Resources
        Workspace directory: {self.workspace_dir}
        """
        
        try:
            # Phase 1: Architecture
            logger.info(f"Starting architecture phase for task: {task.title}")
            architecture_message = f"""
            We need to design a solution for the following task:
            
            {task_prompt}
            
            Please analyze the requirements, identify the core components needed, 
            and create a high-level architecture or framework to guide our approach.
            """
            
            architecture_result = architect.initiate_chat(
                recipient=architect,
                message=architecture_message,
                max_turns=5
            )
            
            # Phase 2: Strategy
            logger.info(f"Starting strategy phase for task: {task.title}")
            strategy_message = f"""
            Based on our architectural design:
            
            {architecture_result.summary}
            
            Please create a detailed execution plan for this task. Break it down into 
            clear steps, identify resources needed, and establish milestones.
            """
            
            strategy_result = architect.initiate_chat(
                recipient=strategist,
                message=strategy_message,
                max_turns=5
            )
            
            # Phase 3: Exploration
            logger.info(f"Starting exploration phase for task: {task.title}")
            exploration_message = f"""
            Based on our architecture and strategy:
            
            Architecture: {architecture_result.summary}
            
            Strategy: {strategy_result.summary}
            
            Please conduct research to gather all necessary information for this task.
            Identify relevant context, best practices, and potential approaches.
            """
            
            exploration_result = strategist.initiate_chat(
                recipient=explorer,
                message=exploration_message,
                max_turns=8
            )
            
            # Phase 4: Creation
            logger.info(f"Starting creation phase for task: {task.title}")
            creation_message = f"""
            Based on our architecture, strategy, and exploration:
            
            Architecture: {architecture_result.summary}
            
            Strategy: {strategy_result.summary}
            
            Exploration: {exploration_result.summary}
            
            Please implement the solution for this task. Focus on creating high-quality deliverables
            that meet the requirements and align with our design.
            
            If this task involves coding, you have access to the CodeTool which allows you to:
            1. Generate code files in various languages
            2. Validate that code compiles correctly
            3. Fix code that has compilation errors
            4. Run code and see the output
            5. Get summaries of code files
            
            Use these capabilities to ensure any code you create works properly.
            """
            
            creation_result = explorer.initiate_chat(
                recipient=creator,
                message=creation_message,
                max_turns=10
            )
            
            # Phase 5: Evaluation
            logger.info(f"Starting evaluation phase for task: {task.title}")
            evaluation_message = f"""
            Please evaluate the implementation for this task:
            
            {creation_result.summary}
            
            Compare it against the original requirements:
            
            {task_prompt}
            
            And our architecture and strategy:
            
            Architecture: {architecture_result.summary}
            Strategy: {strategy_result.summary}
            
            Identify any issues, suggest improvements, and assess overall quality.
            
            If the implementation includes code, use the CodeTool to validate and test the code,
            ensuring it works as expected.
            """
            
            evaluation_result = creator.initiate_chat(
                recipient=evaluator,
                message=evaluation_message,
                max_turns=5
            )
            
            # Phase 6: Synthesis
            logger.info(f"Starting synthesis phase for task: {task.title}")
            synthesis_message = f"""
            Based on the implementation and evaluation:
            
            Implementation: {creation_result.summary}
            
            Evaluation: {evaluation_result.summary}
            
            Please synthesize the final solution, addressing any issues identified in the evaluation.
            Create a polished, comprehensive deliverable that fulfills all requirements.
            
            If there are code components, ensure all code is working correctly and is well-integrated
            into the final solution. Use the CodeTool as needed for final validation.
            """
            
            synthesis_result = evaluator.initiate_chat(
                recipient=synthesizer,
                message=synthesis_message,
                max_turns=5
            )
            
            # Save the results
            results_path = os.path.join(self.workspace_dir, f"{task.title}_results.md")
            with open(results_path, "w") as f:
                f.write(f"# Task Results: {task.title}\n\n")
                f.write(f"## Task Description\n{task.description}\n\n")
                f.write(f"## Architecture\n{architecture_result.summary}\n\n")
                f.write(f"## Strategy\n{strategy_result.summary}\n\n")
                f.write(f"## Exploration\n{exploration_result.summary}\n\n")
                f.write(f"## Creation\n{creation_result.summary}\n\n")
                f.write(f"## Evaluation\n{evaluation_result.summary}\n\n")
                f.write(f"## Final Solution\n{synthesis_result.summary}\n\n")
            
            logger.info(f"Task completed and results saved to {results_path}")
            
            # Return the results
            return {
                "status": "completed",
                "task_name": task.title,
                "results_path": results_path,
                "summary": synthesis_result.summary,
                "phases": {
                    "architecture": architecture_result.summary,
                    "strategy": strategy_result.summary,
                    "exploration": exploration_result.summary,
                    "creation": creation_result.summary,
                    "evaluation": evaluation_result.summary,
                    "synthesis": synthesis_result.summary
                },
                "chat_history": {
                    "architecture": architecture_result.chat_history,
                    "strategy": strategy_result.chat_history,
                    "exploration": exploration_result.chat_history,
                    "creation": creation_result.chat_history,
                    "evaluation": evaluation_result.chat_history,
                    "synthesis": synthesis_result.chat_history
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing task {task.title}: {str(e)}")
            return {
                "status": "failed",
                "task_name": task.title,
                "error": str(e)
            }
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Execute multiple tasks sequentially.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Dict containing results for all tasks
        """
        results = []
        for task in tasks:
            task_result = await self.execute_task(task)
            results.append(task_result)
        
        return {
            "task_results": results,
            "completed": len([r for r in results if r.get("status") == "completed"]),
            "failed": len([r for r in results if r.get("status") == "failed"])
        }
    
    async def run_collaborative_session(self, task: Union[Task, str]) -> Dict[str, Any]:
        """
        Run a collaborative session with all team members working together.
        
        This method uses swarm orchestration to enable all agents to collaborate
        on a task with automatic handoffs between agents.
        
        Args:
            task: Task object or task description string
            
        Returns:
            Dict containing the session results
        """
        # Convert string to Task if needed
        if isinstance(task, str):
            from roboco.core.schema import Task
            task = Task(title="collaborative_task", description=task)
        
        # Enable swarm for collaboration
        self.enable_swarm()
        self.register_handoffs()
        
        # Prepare the initial query
        query = f"""
        # Collaborative Task
        
        {task.description}
        
        # Expected Outcome
        {task.expected_outcome if hasattr(task, 'expected_outcome') else 'Complete the task successfully'}
        
        # Process
        This is a collaborative effort where team members will work together:
        1. The Architect will design the overall solution framework
        2. The Strategist will develop the execution plan
        3. The Explorer will gather necessary information and research
        4. The Creator will implement the solution
           - For coding tasks, the Creator can use CodeTool to generate, validate, and execute code
        5. The Evaluator will review and identify improvements
        6. The Synthesizer will integrate everything into a final deliverable
        
        Let's work together to complete this task successfully.
        """
        
        # Run the swarm with the architect as the initial agent
        swarm_result = self.run_swarm(
            initial_agent_name="architect",
            query=query,
            context_variables={"task": task.dict() if hasattr(task, 'dict') else {"title": task.title, "description": task.description}},
            max_rounds=25
        )
        
        # Save the results
        results_path = os.path.join(self.workspace_dir, f"{task.title}_collaborative_results.md")
        
        if "error" not in swarm_result:
            chat_result = swarm_result.get("chat_result", "")
            with open(results_path, "w") as f:
                f.write(f"# Collaborative Task Results: {task.title}\n\n")
                f.write(f"## Task Description\n{task.description}\n\n")
                f.write(f"## Solution\n{chat_result}\n\n")
            
            logger.info(f"Collaborative session completed and results saved to {results_path}")
            
            swarm_result["results_path"] = results_path
            swarm_result["status"] = "completed"
        else:
            logger.error(f"Error in collaborative session: {swarm_result.get('error')}")
            swarm_result["status"] = "failed"
        
        return swarm_result 