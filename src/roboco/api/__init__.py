"""
API package for Roboco.

This package provides API models and utilities for the API layer.
"""

from .server import app as server_app

__all__ = ["server_app"]
