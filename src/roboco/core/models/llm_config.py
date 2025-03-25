"""
Language Model Configuration

This module defines configuration models for language models.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for language model settings."""
    
    model: str = Field(
        default="gpt-4",
        description="The model to use for language generation"
    )
    api_key: str = Field(
        default="",
        description="API key for the language model provider"
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the language model API"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for text generation"
    )
    max_tokens: int = Field(
        default=4000,
        gt=0,
        description="Maximum number of tokens to generate"
    )
    terminate_msg: str = Field(
        default="TERMINATE",
        description="Message used by agents to signal completion"
    )
    
    # Optional model-specific configurations
    vision: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for vision-capable models"
    )
    openai: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for OpenAI models"
    )
    deepseek: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for DeepSeek models"
    )
    ollama: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for local Ollama models"
    )
    
    class Config:
        extra = 'allow'  # Allow extra fields for model-specific configurations 