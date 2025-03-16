"""Asynchronous and threading utilities for Roboco."""

import logging
import concurrent.futures
from typing import Any, Callable, Optional, Dict, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

def run_with_timeout(
    func: Callable[..., T], 
    args: tuple = (), 
    kwargs: Optional[Dict] = None, 
    timeout_seconds: int = 120
) -> Optional[T]:
    """
    Run a function with a timeout using concurrent.futures.
    
    This utility allows running any function with a specified timeout,
    preventing operations from hanging indefinitely.
    
    Args:
        func: The function to run
        args: Positional arguments to pass to the function
        kwargs: Keyword arguments to pass to the function
        timeout_seconds: Maximum time to allow the function to run
        
    Returns:
        The result of the function if it completes within the timeout,
        or None if it times out
        
    Raises:
        Any exception raised by the function
    """
    if kwargs is None:
        kwargs = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            logger.warning(f"Operation timed out after {timeout_seconds} seconds")
            return None 