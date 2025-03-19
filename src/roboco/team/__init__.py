"""
Roboco Robotics Corporation

This module provides the core corporate structure for Roboco,
a comprehensive robotics company framework.
"""

from roboco.team.robotics import RoboticsCompany
from roboco.agents import (
    Executive,
    ProductManager,
    SoftwareEngineer,
    RoboticsScientist,
    ReportWriter,
    HumanProxy
)

__all__ = [
    "RoboticsCompany",
    "Executive",
    "ProductManager",
    "SoftwareEngineer",
    "RoboticsScientist",
    "ReportWriter",
    "HumanProxy",
] 