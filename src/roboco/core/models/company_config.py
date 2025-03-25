"""
Company Configuration

This module defines company-specific configuration settings.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class CompanyConfig(BaseModel):
    """
    Company-specific configuration settings.
    
    This includes organization details, branding, and default templates
    that are specific to the company using the application.
    """
    
    # Company details
    name: str = Field(
        default="My Company",
        description="Name of the company"
    )
    
    domain: str = Field(
        default="example.com",
        description="Company domain name"
    )
    
    description: str = Field(
        default="",
        description="Company description"
    )
    
    # Contact information
    contact: Dict[str, Any] = Field(
        default_factory=lambda: {
            "email": "info@example.com",
            "phone": "",
            "address": ""
        },
        description="Company contact information"
    )
    
    # Branding settings
    branding: Dict[str, Any] = Field(
        default_factory=lambda: {
            "logo_url": "",
            "primary_color": "#4A90E2",
            "secondary_color": "#50E3C2",
            "accent_color": "#F5A623"
        },
        description="Company branding settings"
    )
    
    # Default templates
    templates: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default templates for various content types"
    )
    
    # Department structure
    departments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Company department structure"
    )
    
    # Team structure
    teams: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Company team structure"
    )
    
    # Project defaults
    project_defaults: Dict[str, Any] = Field(
        default_factory=lambda: {
            "repository_prefix": "",
            "default_license": "MIT",
            "default_readme_template": "",
            "default_project_structure": []
        },
        description="Default settings for new projects"
    )
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra fields 