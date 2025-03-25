"""
Core Configuration

This module defines the core configuration settings for the application.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field


class CoreConfig(BaseModel):
    """
    Core configuration settings for the application.
    
    This includes settings for databases, caching, storage, and other
    infrastructure components.
    """
    
    # Database settings
    database: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "sqlite",
            "path": "data/roboco.db",
            "pool_size": 5,
            "pool_recycle": 3600,
            "echo": False
        },
        description="Database configuration settings"
    )
    
    # Cache settings
    cache: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "memory",
            "ttl": 3600,  # Time to live in seconds
            "max_size": 1000  # Maximum number of items in cache
        },
        description="Cache configuration settings"
    )
    
    # Storage settings
    storage: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "local",
            "root_dir": "data/storage",
            "max_size_mb": 1024
        },
        description="Storage configuration settings"
    )
    
    # Security settings
    security: Dict[str, Any] = Field(
        default_factory=lambda: {
            "secret_key": "",
            "token_expire_minutes": 1440,  # 24 hours
            "algorithm": "HS256"
        },
        description="Security configuration settings"
    )
    
    # Concurrency settings
    concurrency: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_workers": 4,
            "timeout": 300  # seconds
        },
        description="Concurrency and threading settings"
    )
    
    # Feature flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "enable_web_search": True,
            "enable_code_execution": True,
            "enable_file_access": True,
            "enable_swarm": True
        },
        description="Feature flags for enabling/disabling functionality"
    )
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra fields 