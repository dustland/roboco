"""
Roboco Agents Package

This package provides agent implementations for the Roboco system.
"""

from roboco.core.agent import Agent
from .executive import Executive
from .product_manager import ProductManager
from .researcher import Researcher
from .report_writer import ReportWriter
from .human_proxy import HumanProxy

__all__ = [
    "Agent",
    "Executive",
    "ProductManager",
    "Researcher",
    "ReportWriter",
    "HumanProxy"
]