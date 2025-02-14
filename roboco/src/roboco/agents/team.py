from typing import List, Dict, Any, Optional, Union
import autogen
from loguru import logger
from autogen import initiate_swarm_chat, AFTER_WORK, ON_CONDITION, AfterWorkOption

from .roles import Executive, ProductManager, UserProxy

class Team:
    """A team of specialized agents working together on product development."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        # Create agents with llm_config
        self.user_proxy = UserProxy(llm_config=llm_config)
        self.executive = Executive(llm_config=llm_config)
        self.product_manager = ProductManager(llm_config=llm_config)
        
        # Initialize shared context
        self.context_variables = {
            "vision": None,
            "current_timestamp": None,
            "product_spec": {},
            "analyses": [],
            "spec_history": [],
            "current_analysis": None,
            "reviews_left": 2  # Allow for 2 rounds of review/revision
        }
        
        # Register hand-offs for each agent
        self.user_proxy.handoff(hand_to=[
            ON_CONDITION(
                target=self.executive,
                condition="After recording the vision, it must be analyzed.",
                available="reviews_left"
            ),
            AFTER_WORK(AfterWorkOption.TERMINATE)  # End if no more work needed
        ])
        
        self.executive.handoff(hand_to=[
            ON_CONDITION(
                target=self.product_manager,
                condition="After analysis is recorded, create detailed specifications.",
                available="reviews_left"
            ),
            AFTER_WORK(self.product_manager)  # Default to product manager if no condition met
        ])
        
        self.product_manager.handoff(hand_to=[
            ON_CONDITION(
                target=self.executive,
                condition="After specifications are updated, they need review.",
                available="reviews_left"
            ),
            ON_CONDITION(
                target=self.user_proxy,
                condition="When specifications are complete and no more reviews needed, get final result.",
                available=lambda context: not bool(context.get("reviews_left", 0))
            ),
            AFTER_WORK(self.executive)  # Default back to executive for review
        ])
    
    def process_vision(self, vision: str) -> Dict[str, Any]:
        """Process a vision through the team workflow."""
        try:
            # Run the swarm with proper configuration
            chat_result, context_variables, last_agent = initiate_swarm_chat(
                initial_agent=self.user_proxy,
                agents=[self.user_proxy, self.executive, self.product_manager],
                messages=vision,
                context_variables=self.context_variables,
                after_work=AFTER_WORK(AfterWorkOption.TERMINATE),  # Global fallback
                max_turns=12  # Prevent infinite loops
            )
            
            # Get final result
            return self.user_proxy.get_final_result(context_variables)
            
        except Exception as e:
            logger.error(f"Error in team workflow: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }

class TeamManager:
    """Manages team interactions and workflow."""
    
    def __init__(self, config_list: List[Dict[str, Any]]):
        # Basic LLM config
        self.llm_config = {
            "config_list": config_list,
            "temperature": 0.7,
            "timeout": 600
        }
        
        # Create team
        self.team = Team(llm_config=self.llm_config)
    
    def process_vision(self, vision: str) -> Dict[str, Any]:
        """Process a product vision through the team."""
        try:
            # Process the vision through the team workflow
            result = self.team.process_vision(vision)
            
            return {
                "vision": vision,
                "result": result,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error processing vision: {str(e)}")
            return {
                "vision": vision,
                "error": str(e),
                "status": "failed"
            } 