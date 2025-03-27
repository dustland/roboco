"""
ID Generator Utility

This module provides utility functions for generating short, URL-friendly IDs.
"""

import random
import string
import time

def generate_short_id(length=8):
    """
    Generate a short, URL-friendly ID.
    
    Args:
        length: Length of the ID to generate (default: 8)
        
    Returns:
        A short alphanumeric ID
    """
    # Use a timestamp component to ensure uniqueness
    timestamp = int(time.time() * 1000)
    timestamp_str = format(timestamp, 'x')[-6:]  # Last 6 chars of hex timestamp
    
    # Random alphanumeric characters
    chars = string.ascii_letters + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(length - len(timestamp_str)))
    
    # Combine timestamp and random parts
    short_id = random_part + timestamp_str
    
    # Shuffle the combined ID to make it less predictable
    short_id_list = list(short_id)
    random.shuffle(short_id_list)
    
    return ''.join(short_id_list[:length]) 