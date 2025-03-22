"""
RoboCo API

This package provides the API server implementation for RoboCo.
"""

from .server import app as server_app

__all__ = ["server_app"]
