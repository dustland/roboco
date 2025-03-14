"""
Roboco Agents Package

This package provides agent implementations for the Roboco system.
"""

from roboco.core.agent import Agent
from .executive import Executive
from .product_manager import ProductManager

__all__ = [
    "Agent",
    "Executive",
    "ProductManager"
]