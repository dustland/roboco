"""
Memory Backend Factory

Factory functions for creating memory backend instances based on configuration.
"""

from ..utils.logger import get_logger
from typing import Optional
from .backend import MemoryBackend
from .mem0_backend import Mem0Backend
# MemoryConfig imported locally to avoid circular imports

logger = get_logger(__name__)


def create_memory_backend(config = None) -> MemoryBackend:
    """
    Create a memory backend instance based on configuration.
    
    Args:
        config: Memory configuration. If None, uses default Mem0 config.
        
    Returns:
        Memory backend instance
        
    Raises:
        ValueError: If backend type is not supported
        ImportError: If required dependencies are not installed
    """
    if config is None:
        # Create default Mem0 configuration
        from .models import MemoryConfig
        config = MemoryConfig()
    
    # For now, we only support Mem0 backend
    # In the future, we could support multiple backends based on config
    try:
        backend = Mem0Backend(config)
        logger.info("Created Mem0 memory backend")
        return backend
        
    except ImportError as e:
        logger.error(f"Failed to create Mem0 backend: {e}")
        logger.error("Install mem0ai with: pip install mem0ai")
        raise
    except Exception as e:
        logger.error(f"Failed to create memory backend: {e}")
        raise


def create_default_memory_backend() -> MemoryBackend:
    """
    Create a memory backend with default configuration.
    
    Returns:
        Memory backend instance with default settings
    """
    return create_memory_backend() 