"""
Search manager that coordinates different search backends.
"""

from typing import Dict, Optional, Any
from .interfaces import SearchBackend, SearchResponse
from .serpapi_backend import SerpAPIBackend


class SearchManager:
    """
    Manages multiple search backends and provides unified search interface.
    """
    
    def __init__(self, default_backend: str = "serpapi", **backend_configs):
        """
        Initialize search manager.
        
        Args:
            default_backend: Default backend to use for searches
            **backend_configs: Configuration for different backends
        """
        self.default_backend = default_backend
        self.backends: Dict[str, SearchBackend] = {}
        
        # Initialize available backends
        self._initialize_backends(backend_configs)
    
    def _initialize_backends(self, configs: Dict[str, Any]) -> None:
        """Initialize search backends."""
        # SerpAPI backend
        serpapi_config = configs.get("serpapi", {})
        try:
            self.backends["serpapi"] = SerpAPIBackend(
                api_key=serpapi_config.get("api_key")
            )
        except (ValueError, ImportError) as e:
            print(f"Warning: Could not initialize SerpAPI backend: {e}")
    
    def add_backend(self, name: str, backend: SearchBackend) -> None:
        """Add a new search backend."""
        self.backends[name] = backend
    
    def get_backend(self, name: Optional[str] = None) -> SearchBackend:
        """Get a search backend by name."""
        backend_name = name or self.default_backend
        
        if backend_name not in self.backends:
            raise ValueError(f"Backend '{backend_name}' not available")
        
        backend = self.backends[backend_name]
        if not backend.is_available():
            raise RuntimeError(f"Backend '{backend_name}' is not available")
        
        return backend
    
    def list_backends(self) -> Dict[str, bool]:
        """List all backends and their availability status."""
        return {
            name: backend.is_available() 
            for name, backend in self.backends.items()
        }
    
    async def search(self, query: str, backend: Optional[str] = None, **kwargs) -> SearchResponse:
        """
        Execute a search using the specified or default backend.
        
        Args:
            query: Search query
            backend: Backend to use (defaults to default_backend)
            **kwargs: Additional search parameters
            
        Returns:
            SearchResponse with results
        """
        search_backend = self.get_backend(backend)
        return await search_backend.search(query, **kwargs) 