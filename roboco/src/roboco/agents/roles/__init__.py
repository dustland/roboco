"""Role-specific agents for RoboCo."""

from .human import HumanAgent
from .executive import ExecutiveBoardAgent
from .product import ProductManagerAgent

__all__ = [
    "HumanAgent",
    "ExecutiveBoardAgent",
    "ProductManagerAgent",
]
