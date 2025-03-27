"""
ID Generator Utility

This module provides utility functions for generating short, URL-friendly IDs.
"""

import string
import uuid

def generate_short_id(length=8):
    """
    Generate a base62-encoded short ID from UUID.
    """
    uid = uuid.uuid4().int
    chars = string.ascii_letters + string.digits
    base = len(chars)
    encoded = ""
    
    while uid > 0:
        uid, rem = divmod(uid, base)
        encoded = chars[rem] + encoded

    return encoded[:length]