from typing import List, Dict, Any
import autogen
from loguru import logger

from .roles import Executive, ProductManager, UserProxy

class Team(autogen.GroupChat):
    """A team of specialized agents working together on product development."""
    
    def __init__(self, llm_config: Dict[str, Any]):
        # Create agents
        self.user_proxy = UserProxy()
        self.executive = Executive(llm_config=llm_config)
        self.product_manager = ProductManager(llm_config=llm_config)
        
        # Initialize group chat
        super().__init__(
            agents=[self.user_proxy, self.executive, self.product_manager],
            messages=[],
            max_round=12
        )

class TeamManager(autogen.GroupChatManager):
    """Manages team interactions and workflow."""
    
    def __init__(self, config_list: List[Dict[str, Any]]):
        # Basic LLM config
        self.llm_config = {
            "config_list": config_list,
            "temperature": 0.7,
            "timeout": 600
        }
        
        # Create team
        self.group_chat = Team(llm_config=self.llm_config)
        
        # Initialize manager
        super().__init__(
            groupchat=self.group_chat,
            llm_config=self.llm_config
        )
    
    def process_vision(self, vision: str) -> Dict[str, Any]:
        """Process a product vision through the team."""
        try:
            # Reset the chat for a new conversation
            self.groupchat.messages.clear()
            
            # Start the chat with the vision
            self.groupchat.user_proxy.initiate_chat(
                self.groupchat.executive,
                message=f"""Process this product vision:

{vision}

1. First, structure the vision into clear components
2. Then, work with the product manager to create detailed specifications
3. Finally, summarize the complete product specification

Please ensure the final output is a structured JSON document containing the vision analysis and specifications."""
            )
            
            # Get the chat results
            return {
                "vision": vision,
                "messages": self.groupchat.messages,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Error in team chat: {str(e)}")
            return {
                "vision": vision,
                "error": str(e),
                "status": "failed"
            } 