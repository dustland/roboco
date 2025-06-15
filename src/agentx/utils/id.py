"""
ID generation utilities for AgentX.
"""

import secrets
import string

def generate_short_id(length: int = 8) -> str:
    """
    Generate a short, URL-friendly, cryptographically secure random ID.

    Args:
        length (int): The desired length of the ID. Defaults to 8.

    Returns:
        str: A new short ID.
    """
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_'
    return ''.join(secrets.choice(alphabet) for _ in range(length)) 