"""
Brain Component - LLM Gateway

Handles all LLM interactions for agents, including provider abstraction,
prompt formatting, and response parsing.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from ..utils.logger import get_logger
from .config import LLMConfig

logger = get_logger(__name__)


class LLMMessage(BaseModel):
    """Standard message format for LLM interactions."""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: Optional[datetime] = None


class LLMResponse(BaseModel):
    """Response from LLM call."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    timestamp: datetime


class Brain:
    """
    Brain component that handles all LLM interactions for an agent.
    
    Provides a unified interface for different LLM providers and handles
    prompt formatting, response parsing, and error handling.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize Brain with LLM configuration.
        
        Args:
            config: LLM configuration including provider, model, etc.
        """
        self.config = config
        self._client = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure LLM client is initialized."""
        if self._initialized:
            return
            
        try:
            # Use litellm for provider abstraction
            import litellm
            
            # Set API key from config or environment
            api_key = self.config.api_key
            if not api_key:
                # Try to get from environment based on provider
                env_key_map = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY", 
                    "deepseek": "DEEPSEEK_API_KEY",
                    "ollama": "OLLAMA_API_KEY"
                }
                env_key = env_key_map.get(self.config.provider.lower())
                if env_key:
                    api_key = os.getenv(env_key)
            
            if not api_key and self.config.provider.lower() != "ollama":
                logger.warning(f"No API key found for provider {self.config.provider}")
            
            # Configure litellm
            if api_key:
                os.environ[f"{self.config.provider.upper()}_API_KEY"] = api_key
                
            if self.config.base_url:
                # Set base URL for custom endpoints
                if self.config.provider.lower() == "deepseek":
                    os.environ["DEEPSEEK_API_BASE"] = self.config.base_url
                elif self.config.provider.lower() == "openai":
                    os.environ["OPENAI_API_BASE"] = self.config.base_url
                    
            self._initialized = True
            logger.info(f"Brain initialized with {self.config.provider}/{self.config.model}")
            
        except ImportError:
            logger.error("litellm package not available. Install with: pip install litellm")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Brain: {e}")
            raise
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt to prepend
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            
        Returns:
            LLM response with content and metadata
        """
        await self._ensure_initialized()
        
        try:
            import litellm
            
            # Format messages for LLM
            formatted_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                # Always append current date/time to system prompt
                current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
                enhanced_system_prompt = f"{system_prompt}\n\nCurrent date and time: {current_datetime}"
                
                formatted_messages.append({
                    "role": "system",
                    "content": enhanced_system_prompt
                })
            
            # Add conversation messages
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare call parameters
            call_params = {
                "model": f"{self.config.provider}/{self.config.model}",
                "messages": formatted_messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "timeout": self.config.timeout
            }
            
            # Add base URL if configured
            if self.config.base_url:
                call_params["api_base"] = self.config.base_url
            
            logger.debug(f"Making LLM call with model: {call_params['model']}")
            
            # Make the LLM call
            response = await litellm.acompletion(**call_params)
            
            # Extract response content
            content = response.choices[0].message.content
            usage = response.usage.dict() if response.usage else None
            finish_reason = response.choices[0].finish_reason
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return a fallback response for demo purposes
            return LLMResponse(
                content=f"I apologize, but I'm having trouble connecting to the {self.config.provider} API. "
                       f"This could be due to missing API keys or network issues. "
                       f"Error: {str(e)}",
                model=self.config.model,
                usage=None,
                finish_reason="error",
                timestamp=datetime.now()
            )
    
    async def generate_streaming_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Generate a streaming response from the LLM.
        
        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt to prepend
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            
        Yields:
            Streaming chunks of the response
        """
        await self._ensure_initialized()
        
        try:
            import litellm
            
            # Format messages for LLM
            formatted_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                # Always append current date/time to system prompt
                current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
                enhanced_system_prompt = f"{system_prompt}\n\nCurrent date and time: {current_datetime}"
                
                formatted_messages.append({
                    "role": "system", 
                    "content": enhanced_system_prompt
                })
            
            # Add conversation messages
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare call parameters
            call_params = {
                "model": f"{self.config.provider}/{self.config.model}",
                "messages": formatted_messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "timeout": self.config.timeout,
                "stream": True
            }
            
            # Add base URL if configured
            if self.config.base_url:
                call_params["api_base"] = self.config.base_url
            
            logger.debug(f"Making streaming LLM call with model: {call_params['model']}")
            
            # Make the streaming LLM call
            response = await litellm.acompletion(**call_params)
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming LLM call failed: {e}")
            # Yield a fallback response
            yield f"I apologize, but I'm having trouble connecting to the {self.config.provider} API. Error: {str(e)}" 