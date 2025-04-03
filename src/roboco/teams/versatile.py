"""
Versatile Team Module

This module defines the VersatileTeam class, which provides a flexible and adaptable team implementation
with specialized roles designed to handle any type of task phase effectively.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

# Initialize logger
logger = logger.bind(module=__name__)

from roboco.core.project_fs import ProjectFS
from roboco.core.team import Team
from roboco.core.models import Task
from roboco.agents.human_proxy import HumanProxy
from roboco.core.agent_factory import AgentFactory
from roboco.core.config import get_llm_config
from roboco.tools.bash import BashTool
from autogen import AfterWork, AfterWorkOption, OnCondition, register_hand_off


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
        
        # Enable swarm capabilities with shared context
        self.enable_swarm({
            "project_phase": "initial",
            "allow_research": True,
            "allow_development": True,
            "allow_writing": True,
            "allow_evaluation": False,
            "allow_leadership": False
        })
        
        # Register handoffs for the swarm
        self._register_handoffs()
        
        logger.info(f"Initialized VersatileTeam with specialized roles in workspace: {self.fs.base_dir}")
    
    def _initialize_agents(self):
        """Initialize agents with specialized roles for the team."""
        agent_factory = AgentFactory.get_instance()
        
        # Create the lead agent with the system message from the roles config
        self.lead = agent_factory.create_agent(
            role_key="lead",
        )

        # Create the researcher agent
        self.researcher = agent_factory.create_agent(
            role_key="researcher",
        )

        # Create the developer agent
        self.developer = agent_factory.create_agent(
            role_key="developer",
        )

        # Create the writer agent
        self.writer = agent_factory.create_agent(
            role_key="writer",
        )

        # Create the evaluator agent
        self.evaluator = agent_factory.create_agent(
            role_key="evaluator",
        )
        
        # Create the executor agent - use agent_factory for consistency
        self.executor = agent_factory.create_agent(
            role_key="executor",
            code_execution_config={"work_dir": "workspace", "use_docker": False}
        )
        
        # Add all agents to the team
        self.agents = {
            "lead": self.lead,
            "researcher": self.researcher, 
            "developer": self.developer,
            "writer": self.writer,
            "evaluator": self.evaluator,
            "executor": self.executor
        }
    
    def _register_tools(self):
        """Register necessary tools with the agents."""
        agents_to_register = [agent for agent_name, agent in self.agents.items() if agent_name != "executor"]
        try:
            # Create file system tool
            from roboco.tools.fs import FileSystemTool
            
            fs_tool = FileSystemTool(
                fs=self.fs
            )
            # Register fs_tool with all agents at once
            if agents_to_register:
                fs_tool.register_with_agents(*agents_to_register, executor_agent=self.executor)
        except ImportError:
            logger.warning("FileSystemTool not available")
        except Exception as e:
            logger.warning(f"Could not initialize FileSystemTool: {str(e)}")
            
        try:
            # Register bash tool with executor for code execution
            bash_tool = BashTool(fs=self.fs)  # Pass the filesystem to ensure commands run at project root
            # Register bash tool with all agents at once
            if agents_to_register:
                bash_tool.register_with_agents(*agents_to_register, executor_agent=self.executor)
        except Exception as e:
            logger.warning(f"Could not initialize BashTool: {str(e)}")
        
        # Register web search tool if available
        try:
            from roboco.tools.web_search import WebSearchTool
            web_search_tool = WebSearchTool(
                name="web_search",
                description="Search the web for information"
            )
            
            # Register with researcher for research capabilities
            web_search_tool.register_with_agents(
                self.researcher,
                executor_agent=self.executor
            )
        except ImportError:
            logger.warning("WebSearchTool not available")
        except Exception as e:
            logger.warning(f"Could not initialize WebSearchTool: {str(e)}")
        
        # Register browser tool with researcher
        try:
            from roboco.tools.browser_use import BrowserUseTool, BrowserUseConfig
            
            # Create config object first
            browser_config = BrowserUseConfig(
                headless=True,
                output_dir="./output/browser_sessions",
                debug=False
            )
            
            # Create tool with config object
            browser_tool = BrowserUseTool(
                name="browser",
                description="Use the web browser to search the web or navigate to a specific URL",
                config=browser_config
            )
            
            # Register with appropriate agents
            browser_tool.register_with_agents(
                self.researcher,
                executor_agent=self.executor
            )
            
        except ImportError:
            logger.warning("BrowserUseTool not available")
        except Exception as e:
            logger.warning(f"Could not initialize BrowserUseTool: {str(e)}")
            
    def _register_handoffs(self):
        """Register handoffs for a hybrid Star/Feedback Loop pattern.
        
        This pattern:
        1. Maintains Lead as the central coordinator (hub in Star pattern)
        2. Allows direct feedback loops between specialists for iterative refinement
        3. Ensures Lead has oversight while enabling efficient specialist collaboration
        4. Uses semantic understanding rather than explicit keywords for transitions
        5. Prevents endless back-and-forth loops with loop counting and circuit breakers
        6. Requires explicit handoff reasoning to improve transparency and debuggability
        """
        
        # Clear any existing handoffs first
        for agent in self.agents.values():
            if hasattr(agent, "_hand_to"):
                agent._hand_to = []
        
        # Set up a shared context for tracking feedback loops and handoff reasons
        self.shared_context.update({
            "feedback_loops": {
                "researcher_developer": 0,
                "developer_researcher": 0,
                "max_loops": 3  # Maximum number of loops before forcing a return to Lead
            },
            "current_task_phase": "initial"  # Track the current task phase
        })
        
        # STAR PATTERN: Lead as central coordinator (Hub)
        register_hand_off(self.lead, [
            # Lead to Researcher for research tasks
            OnCondition(
                condition="Indicates a need for data collection, research, information gathering, understanding concepts, or exploring solutions.",
                target=self.researcher
            ),
            # Lead to Developer for implementation tasks
            OnCondition(
                condition="Indicates a need for code implementation, development, programming, website creation, or building a solution.",
                target=self.developer
            ),
            # Lead to Writer for documentation tasks
            OnCondition(
                condition="Indicates a need for documentation, content creation, explanation, or written material.",
                target=self.writer
            ),
            # Lead to Evaluator for testing tasks
            OnCondition(
                condition="Indicates a need for testing, evaluation, review, validation, or quality assessment.",
                target=self.evaluator
            )
        ])
        
        # FEEDBACK LOOP: Researcher-Developer for iterative research and implementation
        register_hand_off(self.researcher, [
            # Only go to Developer if research work is complete and implementation is needed
            OnCondition(
                condition="Includes substantive research findings, collected data, or analysis AND indicates the research is complete or sufficient for implementation.",
                target=self.developer
            ),
            # Default: Return to Lead
            AfterWork(
                agent=self.lead
            )
        ])
        
        # FEEDBACK LOOP: Developer-Researcher for implementation questions
        register_hand_off(self.developer, [
            # Developer to Evaluator when implementation is ready for testing
            OnCondition(
                condition="Includes substantive development work AND (indicates code or website implementation is complete AND ready for testing OR mentions data retrieval/API functionality that needs validation).",
                target=self.evaluator
            ),
            # Developer to Researcher only if there are unresolved research questions
            OnCondition(
                condition="Includes substantive development work AND mentions needing additional research, information, or clarification.",
                target=self.researcher
            ),
            # If no specific conditions match, go back to Lead
            AfterWork(
                agent=self.lead
            )
        ])
        
        # FEEDBACK LOOP: Evaluator-Developer for iterative improvement
        register_hand_off(self.evaluator, [
            # Evaluator to Developer when implementation needs improvement
            OnCondition(
                condition="Includes substantive evaluation results AND (indicates issues with data retrieval, API functionality, or data processing OR mentions bugs/improvements needed in the code).",
                target=self.developer
            ),
            # Default: Evaluator back to Lead when evaluation is complete and all tests pass
            OnCondition(
                condition="Indicates all tests have passed, including data retrieval validation AND no critical issues were found.",
                target=self.lead
            ),
            # Fallback to Lead if no conditions match
            AfterWork(
                agent=self.lead
            )
        ])
        
        # Writer always returns to Lead (following Star pattern)
        register_hand_off(self.writer, [
            AfterWork(
                agent=self.lead
            )
        ])
        
        # Add logging for handoffs and track context
        for agent_name, agent in self.agents.items():
            if hasattr(agent, "_hand_to") and agent._hand_to:
                # Add a message handler to log handoffs
                original_receive = agent.receive
                
                async def receive_with_logging(self, message, sender, config=None):
                    content = message.get("content", "")
                    
                    # Check for short messages
                    short_message_response = self._check_message_length(content, sender)
                    if short_message_response:
                        return short_message_response
                    
                    # Log handoff and check for feedback loops
                    loop_response = self._check_feedback_loops(sender)
                    if loop_response:
                        return loop_response
                    
                    return await original_receive(message, sender, config)
                
                def _check_message_length(self, content, sender):
                    """Check if message is too short and return rejection if needed"""
                    if len(content.strip()) < 100 and sender is not None and sender.name != "executor" and self.name != "lead":
                        logger.warning(f"Agent {sender.name} sent a very short message to {self.name} ({len(content.strip())} chars)")
                        if len(content.strip()) < 30:
                            return {"content": f"Message rejected: Your message was too short. Please provide substantive work or explanation."}
                    return None
                
                def _check_feedback_loops(self, sender):
                    """Check and update feedback loop counters, break loops if needed"""
                    if not hasattr(self, "shared_context") or sender is None:
                        return None
                        
                    # Log the handoff
                    logger.info(f"Handoff from {sender.name if hasattr(sender, 'name') else 'unknown'} to {self.name}")
                    
                    # Check researcher→developer loop
                    if self.name == "developer" and sender.name == "researcher":
                        return self._update_loop_counter("researcher_developer")
                    
                    # Check developer→researcher loop    
                    elif self.name == "researcher" and sender.name == "developer":
                        return self._update_loop_counter("developer_researcher")
                    
                    return None
                
                def _update_loop_counter(self, loop_name):
                    """Update a specific loop counter and break if threshold exceeded"""
                    loops = self.shared_context.get("feedback_loops", {})
                    loops[loop_name] = loops.get(loop_name, 0) + 1
                    self.shared_context["feedback_loops"] = loops
                    
                    max_loops = loops.get("max_loops", 3)
                    if loops[loop_name] >= max_loops:
                        loop_agents = loop_name.split("_")
                        logger.warning(f"Breaking {loop_agents[0]}→{loop_agents[1]} loop after {loops[loop_name]} iterations")
                        return {"content": f"Loop detected: This task has been passed between {loop_agents[0]} and {loop_agents[1]} {loops[loop_name]} times without sufficient progress. Redirecting to lead for coordination."}
                    
                    return None
                
                # Add helper methods to the agent
                agent._check_message_length = _check_message_length.__get__(agent)
                agent._check_feedback_loops = _check_feedback_loops.__get__(agent)
                agent._update_loop_counter = _update_loop_counter.__get__(agent)
                
                # Replace the receive method with our logging version
                agent.receive = receive_with_logging.__get__(agent)
        
        logger.info("Registered improved handoff pattern with explicit reasoning requirements and loop prevention")
    
    def _chat_result_to_dict(self, chat_result):
        """
        Convert a ChatResult object to a dictionary for JSON serialization.
        
        Args:
            chat_result: A ChatResult object or any other object
            
        Returns:
            A JSON-serializable dictionary
        """
        # If it's already a dict or basic type, return it
        if isinstance(chat_result, (dict, str, int, float, bool, type(None))):
            return chat_result
            
        # If it's a list, convert each item
        if isinstance(chat_result, list):
            return [self._chat_result_to_dict(item) for item in chat_result]
            
        # If it's a ChatResult object
        if hasattr(chat_result, '__class__') and chat_result.__class__.__name__ == 'ChatResult':
            result = {}
            # Add all attributes that don't start with underscore
            for attr in dir(chat_result):
                if not attr.startswith('_'):
                    try:
                        value = getattr(chat_result, attr)
                        # Skip methods
                        if not callable(value):
                            result[attr] = self._chat_result_to_dict(value)
                    except Exception as e:
                        logger.warning(f"Error getting attribute {attr} from ChatResult: {e}")
            return result
            
        # Try to convert object to dict if it has a to_dict method
        if hasattr(chat_result, 'to_dict') and callable(chat_result.to_dict):
            return self._chat_result_to_dict(chat_result.to_dict())
            
        # If it has a dict or model_dump method (pydantic models)
        if hasattr(chat_result, 'dict') and callable(getattr(chat_result, 'dict')):
            return self._chat_result_to_dict(chat_result.dict())
        if hasattr(chat_result, 'model_dump') and callable(getattr(chat_result, 'model_dump')):
            return self._chat_result_to_dict(chat_result.model_dump())
            
        # Last resort: try to convert to string
        try:
            return str(chat_result)
        except:
            return f"<Non-serializable object of type {type(chat_result).__name__}>"
            
    async def run_chat(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a chat session with all team members working together.
        
        This method uses a hybrid Star/Feedback Loop pattern where:
        - Lead serves as the central coordinator (hub in Star pattern)
        - Specialists can directly interact in feedback loops for iterative refinement
        - Lead maintains oversight of the overall process
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the session results
        """
        # Convert string to Task
        from roboco.core.models import Task
        task = Task(description=query)
        
        # Create context variables with task information and tracking vars
        context = {
            "task": task.model_dump() if hasattr(task, 'model_dump') else (
                task.dict() if hasattr(task, 'dict') else {"description": task.description}
            ),
            # Shared tracking variables for hybrid pattern
            "query_analyzed": False,
            "query_completed": False,
            
            # Track task assignments
            "research_needed": False,
            "research_completed": False,
            "development_needed": False,
            "development_completed": False,
            "writing_needed": False,
            "writing_completed": False,
            "evaluation_needed": False,
            "evaluation_completed": False,
            
            # Track feedback loops
            "feedback_loops": {
                "researcher_developer": 0,  # Count of researcher→developer handoffs
                "developer_researcher": 0,  # Count of developer→researcher handoffs
                "developer_evaluator": 0,   # Count of developer→evaluator handoffs
                "evaluator_developer": 0,   # Count of evaluator→developer handoffs
            },
            
            # Content storage
            "research_findings": "",
            "implementation_status": "",
            "evaluation_results": "",
            "final_response": ""
        }
        
        # Log the start of collaborative session
        logger.info(f"Starting hybrid Star/Feedback Loop session for task: {task.description[:50]}...")
        
        # Run the swarm with the lead as the central coordinator
        try:
            swarm_result = self.run_swarm(
                initial_agent_name="lead",
                query=query,
                context_variables=context,
                max_rounds=240
            )
        except Exception as e:
            import traceback
            error_tb = traceback.format_exc()
            logger.error(f"Exception in hybrid pattern execution: {str(e)}")
            logger.error(f"Traceback: {error_tb}")
            return {
                "error": str(e),
                "traceback": error_tb,
                "status": "failed"
            }
        
        # Save the results
        # Create a file name based on the first few words of the description
        task_file_name = "_".join(task.description.split()[:5]).lower()
        task_file_name = "".join(c if c.isalnum() or c == "_" else "_" for c in task_file_name)
        
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        if not self.fs.exists_sync(logs_dir):
            try:
                # Use the filesystem to create the logs directory
                self.fs.mkdir_sync(logs_dir)
                logger.info(f"Created logs directory at {logs_dir}")
            except Exception as e:
                logger.warning(f"Failed to create logs directory: {str(e)}")
        
        # Save results in the logs directory
        results_file = f"{task_file_name}_results.md"
        results_path_relative = os.path.join(logs_dir, results_file)
        results_path = os.path.join(self.fs.base_dir, results_path_relative)
        
        if "error" not in swarm_result:
            chat_result = swarm_result.get("chat_result", "")
            
            # Extract and format the collaboration analysis
            messages = swarm_result.get("messages", [])
            agent_sequence = []
            agent_contributions = {}
            feedback_loops_detected = {
                "researcher_developer": 0,
                "developer_researcher": 0,
                "developer_evaluator": 0,
                "evaluator_developer": 0
            }
            
            # Analyze the message flow to identify handoffs and feedback loops
            previous_agent = None
            for msg in messages:
                agent_name = msg.get("name", "unknown")
                if agent_name not in ["user", "unknown"]:
                    agent_sequence.append(agent_name)
                    content = msg.get("content", "")
                    
                    # Track agent contributions
                    if agent_name not in agent_contributions:
                        agent_contributions[agent_name] = []
                    agent_contributions[agent_name].append(len(content))
                    
                    # Track feedback loops
                    if previous_agent and previous_agent != agent_name:
                        if previous_agent == "researcher" and agent_name == "developer":
                            feedback_loops_detected["researcher_developer"] += 1
                        elif previous_agent == "developer" and agent_name == "researcher":
                            feedback_loops_detected["developer_researcher"] += 1
                        elif previous_agent == "developer" and agent_name == "evaluator":
                            feedback_loops_detected["developer_evaluator"] += 1
                        elif previous_agent == "evaluator" and agent_name == "developer":
                            feedback_loops_detected["evaluator_developer"] += 1
                    
                    previous_agent = agent_name
            
            # Write enhanced results file
            with open(results_path, "w") as f:
                f.write(f"# Hybrid Star/Feedback Loop Task Results\n\n")
                f.write(f"## Task Description\n{task.description}\n\n")
                f.write(f"## Solution\n{json.dumps(self._chat_result_to_dict(chat_result), indent=2)}\n\n")
                
                # Add collaboration analysis
                f.write(f"## Collaboration Analysis\n\n")
                f.write(f"### Agent Sequence\n{' → '.join(agent_sequence)}\n\n")
                
                f.write(f"### Contribution Summary\n")
                for agent, sizes in agent_contributions.items():
                    f.write(f"- **{agent}**: {len(sizes)} contributions, {sum(sizes)} total characters\n")
                
                # Add feedback loop analysis
                f.write(f"\n### Feedback Loops Detected\n")
                f.write(f"- Researcher → Developer: {feedback_loops_detected['researcher_developer']} handoffs\n")
                f.write(f"- Developer → Researcher: {feedback_loops_detected['developer_researcher']} handoffs\n")
                f.write(f"- Developer → Evaluator: {feedback_loops_detected['developer_evaluator']} handoffs\n")
                f.write(f"- Evaluator → Developer: {feedback_loops_detected['evaluator_developer']} handoffs\n")
                
                # Calculate efficiency metrics
                total_handoffs = len(agent_sequence) - 1
                direct_feedback_loops = sum(feedback_loops_detected.values())
                star_pattern_handoffs = total_handoffs - direct_feedback_loops
                
                f.write(f"\n### Pattern Efficiency\n")
                f.write(f"- Total handoffs: {total_handoffs}\n")
                f.write(f"- Direct feedback loops: {direct_feedback_loops} ({direct_feedback_loops/total_handoffs*100:.1f}%)\n")
                f.write(f"- Star pattern handoffs: {star_pattern_handoffs} ({star_pattern_handoffs/total_handoffs*100:.1f}%)\n")
            
            logger.info(f"Hybrid pattern session completed with {len(agent_sequence)} agent handoffs")
            logger.info(f"Detected {direct_feedback_loops} direct feedback loops")
            logger.info(f"Results saved to {results_path_relative}")
            
            return {
                "response": self._chat_result_to_dict(chat_result),
                "chat_history": messages,
                "results_path": results_path_relative,
                "collaboration_stats": {
                    "agent_sequence": agent_sequence,
                    "agent_contributions": agent_contributions,
                    "feedback_loops": feedback_loops_detected
                },
                "status": "completed"
            }
        else:
            logger.error(f"Error in hybrid pattern session: {swarm_result.get('error')}")
            return {
                "error": swarm_result.get('error', "Unknown error in hybrid pattern session"),
                "status": "failed"
            }
