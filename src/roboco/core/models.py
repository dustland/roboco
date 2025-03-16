"""
Configuration Models

This module defines Pydantic models for configuration validation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class LLMConfig(BaseModel):
    """Configuration for language model settings."""
    
    model: str = Field(
        default="gpt-4",
        description="The model to use for language generation"
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
    config_list: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of model configurations for autogen"
    )
    
    @field_validator("config_list", mode="before")
    def ensure_config_list(cls, v: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """Ensure config_list is populated with at least one configuration."""
        if not v:
            return [{"model": "gpt-4", "api_key": ""}]
        return v


class ToolConfig(BaseModel):
    """Base configuration for tools."""
    timeout: int = Field(default=30, description="Operation timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    use_cache: bool = Field(default=True, description="Whether to use caching")


class BrowserToolConfig(ToolConfig):
    """Configuration for BrowserTool."""
    search: Dict[str, Any] = Field(
        default_factory=lambda: {"max_results": 5, "timeout": 30},
        description="Search-specific settings"
    )
    browse: Dict[str, Any] = Field(
        default_factory=lambda: {"timeout": 30, "max_retries": 3},
        description="Browse-specific settings"
    )


class ToolsConfig(BaseModel):
    """Configuration for all tools."""
    BrowserTool: BrowserToolConfig = Field(
        default_factory=BrowserToolConfig,
        description="BrowserTool configuration"
    )


class RobocoConfig(BaseModel):
    """Root configuration model for roboco.
    
    This model defines the configuration structure for the roboco framework,
    including LLM settings, tool configurations, and agent behavior settings.
    
    The configuration can be loaded from a TOML file using the load_config function.
    Default locations searched for config files include:
    - ./config.toml
    - config/config.toml
    - ~/.config/roboco/config.toml
    - /etc/roboco/config.toml
    """
    
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="Language model configuration"
    )
    tools: ToolsConfig = Field(
        default_factory=ToolsConfig,
        description="Tool configurations"
    )
    terminate_msg: str = Field(
        default="TERMINATE",
        description="Default termination message for agents to signal completion of their response. This message is used by agents to indicate they have finished their task, following AG2's conversation termination pattern."
    )
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "config_list": [
                        {"model": "gpt-4", "api_key": "YOUR_API_KEY"}
                    ]
                },
                "tools": {
                    "BrowserTool": {
                        "timeout": 30,
                        "max_retries": 3,
                        "use_cache": True,
                        "search": {
                            "max_results": 5,
                            "timeout": 30
                        },
                        "browse": {
                            "timeout": 30,
                            "max_retries": 3
                        }
                    }
                }
            }
        } 