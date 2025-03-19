"""
Roboco Agents Package

This package provides agent implementations for the Roboco system.
"""

from roboco.core.agent import Agent
from .executive import Executive
from .product_manager import ProductManager
from .software_engineer import SoftwareEngineer
from .robotics_scientist import RoboticsScientist
from .report_writer import ReportWriter
from .human import HumanProxy

__all__ = [
    "Agent",
    "Executive",
    "ProductManager",
    "SoftwareEngineer",
    "RoboticsScientist",
    "ReportWriter",
    "HumanProxy"
]