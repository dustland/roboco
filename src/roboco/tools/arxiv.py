"""
ArXiv Research Tool

This module provides tools for interacting with arXiv to search and retrieve
academic papers for research purposes.
"""

import os
import json
import time
import asyncio
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import logging

import arxiv
from pydantic import BaseModel, Field
from roboco.core.tool import Tool
from roboco.core.config import get_workspace
from loguru import logger
from roboco.core.models import ToolConfig
from autogen.agentchat.contrib.retrieve_assistant_agent import RetrieveAssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent

# Initialize logger
logger = logger.bind(module=__name__)


class ArxivConfig(ToolConfig):
    """Configuration for ArxivTool."""
    max_results: int = Field(
        default=10,
        description="Maximum number of search results to return"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    rate_limit_delay: int = Field(
        default=3,
        description="Delay between API requests in seconds"
    )
    cache_dir: Optional[str] = Field(
        default="./cache/arxiv",
        description="Directory for caching search results"
    )
    temp_dir: Optional[str] = Field(
        default="./tmp/arxiv_papers",
        description="Directory for temporary paper downloads"
    )


class ArxivTool(Tool):
    """Tool for interacting with the arXiv API to search and retrieve academic papers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ArXiv tool.
        
        Args:
            config: Optional configuration for the tool
        """
        self.config = config or {}
        self.max_results = self.config.get("max_results", 10)
        self.search_timeout = self.config.get("timeout", 30)
        self.rate_limit_delay = self.config.get("rate_limit_delay", 3)  # Seconds between requests
        
        # Cache for search results
        self.cache = {}
        self.cache_dir = self.config.get("cache_dir", None)
        
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            
        # Define the search function
        def search_arxiv(query: str, max_results: Optional[int] = None, 
                        categories: Optional[List[str]] = None,
                        sort_by: str = "relevance") -> Dict[str, Any]:
            """
            Search arXiv for papers matching the query.
            
            Args:
                query: The search query
                max_results: Maximum number of results to return
                categories: Limit search to specific arXiv categories like cs.AI, cs.RO
                sort_by: Sort by "relevance", "lastUpdatedDate", or "submittedDate"
                
            Returns:
                Dictionary containing search results
            """
            return asyncio.run(self.search(query, max_results, categories, sort_by))
        
        # Initialize the Tool parent class with the search function
        super().__init__(
            name="search_arxiv",
            description="Search arXiv for academic papers by keyword, optionally filtering by category",
            func_or_tool=search_arxiv
        )
        
        logger.info("Initialized ArxivTool")
    
    async def search(self, query: str, max_results: Optional[int] = None, 
                    categories: Optional[List[str]] = None,
                    sort_by: str = "relevance", sort_order: str = "descending") -> Dict[str, Any]:
        """Search arXiv for papers matching the query.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            categories: Limit search to specific arXiv categories
            sort_by: Sort by "relevance", "lastUpdatedDate", or "submittedDate"
            sort_order: Sort order "ascending" or "descending"
            
        Returns:
            Dictionary containing search results
        """
        cache_key = f"{query}_{max_results}_{categories}_{sort_by}_{sort_order}"
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"Using cached results for query: {query}")
            return self.cache[cache_key]
        
        # Convert sort_by to arxiv.SortCriterion
        sort_options = {
            "relevance": arxiv.SortCriterion.Relevance,
            "lastUpdatedDate": arxiv.SortCriterion.LastUpdatedDate,
            "submittedDate": arxiv.SortCriterion.SubmittedDate,
        }
        sort_criterion = sort_options.get(sort_by, arxiv.SortCriterion.Relevance)
        
        # Convert sort_order to arxiv.SortOrder
        sort_order_options = {
            "ascending": arxiv.SortOrder.Ascending,
            "descending": arxiv.SortOrder.Descending,
        }
        sort_order_criterion = sort_order_options.get(sort_order, arxiv.SortOrder.Descending)
        
        logger.info(f"Searching arXiv for: {query}")
        
        try:
            # Create the arxiv search client
            client = arxiv.Client(
                page_size=max_results or self.max_results,
                delay_seconds=self.rate_limit_delay,
                num_retries=3
            )
            
            # Create search query
            search_query = arxiv.Search(
                query=query,
                max_results=max_results or self.max_results,
                sort_by=sort_criterion,
                sort_order=sort_order_criterion,
                categories=categories,
            )
            
            # Execute search
            results = list(client.results(search_query))
            
            # Convert to dictionaries
            papers = []
            for result in results:
                paper = {
                    "id": result.entry_id.split("/")[-1],  # Extract paper ID
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "published": result.published.isoformat(),
                    "updated": result.updated.isoformat(),
                    "pdf_url": result.pdf_url,
                    "arxiv_url": result.entry_id,
                    "categories": result.categories,
                    "doi": result.doi
                }
                papers.append(paper)
            
            result = {
                "query": query,
                "success": True,
                "total_results": len(papers),
                "papers": papers
            }
            
            # Cache the results
            self.cache[cache_key] = result
            
            # Save to cache directory if enabled
            if self.cache_dir:
                cache_file = Path(self.cache_dir) / f"arxiv_{urllib.parse.quote_plus(query)}.json"
                with open(cache_file, "w") as f:
                    json.dump(result, f, indent=2)
            
            logger.info(f"Found {len(papers)} papers for query: {query}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return {
                "query": query,
                "success": False,
                "total_results": 0,
                "papers": [],
                "error": str(e)
            }
    
    async def download_paper(self, paper_id: str, save_to_workspace: bool = True) -> Dict[str, Any]:
        """Download a paper PDF from arXiv by ID.
        
        Args:
            paper_id: The arXiv paper ID
            save_to_workspace: Whether to save to the workspace
            
        Returns:
            Dictionary with download information
        """
        try:
            # Create workspace research directory
            if save_to_workspace:
                # Import ProjectManager here to avoid circular imports
                from roboco.core.project_manager import ProjectManager
                workspace = ProjectManager(self.config.get("workspace_dir", "workspace"))
                save_path = workspace.get_research_path("papers") / f"{paper_id}.pdf"
                save_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                temp_dir = Path(self.config.get("temp_dir", "/tmp/arxiv_papers"))
                temp_dir.mkdir(parents=True, exist_ok=True)
                save_path = temp_dir / f"{paper_id}.pdf"
            
            # Download using the arxiv package
            logger.info(f"Downloading paper {paper_id} from arXiv")
            client = arxiv.Client()
            paper = next(client.results(arxiv.Search(id_list=[paper_id])))
            
            # Download PDF
            paper.download_pdf(filename=str(save_path))
            
            logger.info(f"Downloaded paper to {save_path}")
            
            return {
                "paper_id": paper_id,
                "success": True,
                "path": str(save_path),
                "size_bytes": os.path.getsize(save_path)
            }
            
        except Exception as e:
            logger.error(f"Error downloading paper {paper_id}: {e}")
            return {
                "paper_id": paper_id,
                "success": False,
                "error": str(e)
            }
    
    async def get_paper_metadata(self, paper_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a paper from arXiv.
        
        Args:
            paper_id: The arXiv paper ID
            
        Returns:
            Dictionary with paper metadata
        """
        try:
            # Use arxiv package to get paper metadata
            client = arxiv.Client()
            search = arxiv.Search(id_list=[paper_id])
            paper = next(client.results(search))
            
            metadata = {
                "paper_id": paper_id,
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "published": paper.published.isoformat(),
                "updated": paper.updated.isoformat(),
                "categories": paper.categories,
                "pdf_url": paper.pdf_url,
                "arxiv_url": paper.entry_id,
                "journal_ref": getattr(paper, "journal_ref", ""),
                "doi": paper.doi if hasattr(paper, "doi") else "",
                "success": True
            }
            
            return metadata
            
        except StopIteration:
            logger.error(f"Paper {paper_id} not found")
            return {
                "paper_id": paper_id,
                "success": False,
                "error": "Paper not found"
            }
        except Exception as e:
            logger.error(f"Error getting metadata for paper {paper_id}: {e}")
            return {
                "paper_id": paper_id,
                "success": False,
                "error": str(e)
            }
    
    async def save_research_notes(self, paper_id: str, notes: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """Save research notes for a paper to the workspace.
        
        Args:
            paper_id: The arXiv paper ID
            notes: Notes about the paper
            topic: Optional research topic for organizing notes
            
        Returns:
            Dictionary with save result
        """
        try:
            # Get paper metadata
            metadata = await self.get_paper_metadata(paper_id)
            
            if not metadata.get("success", False):
                return {
                    "paper_id": paper_id,
                    "success": False,
                    "error": f"Could not retrieve paper metadata: {metadata.get('error')}"
                }
            
            # Format notes document
            title = metadata.get("title", f"Paper {paper_id}")
            authors = ", ".join(metadata.get("authors", []))
            
            formatted_notes = f"""# Notes on: {title}

## Paper Information
- **Paper ID**: {paper_id}
- **Authors**: {authors}
- **Published**: {metadata.get('published', 'Unknown')}
- **Categories**: {', '.join(metadata.get('categories', []))}
- **URL**: {metadata.get('arxiv_url', f'https://arxiv.org/abs/{paper_id}')}

## Research Notes
{notes}

## Added on
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            # Create workspace research notes directory
            workspace = ProjectManager(self.config.get("workspace_dir", "workspace"))
            workspace_path = workspace.get_research_path("notes")
            if topic:
                topic_safe = topic.lower().replace(" ", "_").replace("-", "_")
                workspace_path = workspace_path / topic_safe
            
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            # Save notes file
            timestamp = datetime.now().strftime("%Y%m%d")
            notes_file = workspace_path / f"{timestamp}_{paper_id}_notes.md"
            
            with open(notes_file, "w") as f:
                f.write(formatted_notes)
            
            logger.info(f"Saved research notes to {notes_file}")
            
            return {
                "paper_id": paper_id,
                "title": title,
                "success": True,
                "path": str(notes_file)
            }
            
        except Exception as e:
            logger.error(f"Error saving research notes for paper {paper_id}: {e}")
            return {
                "paper_id": paper_id,
                "success": False,
                "error": str(e)
            }

    # Helper method to register additional functions
    def register_function(self, func):
        """Register an additional function with this tool."""
        self._function = func 
        
    @classmethod
    def create_with_config(cls, config: Dict[str, Any]) -> 'ArxivTool':
        """Create an instance with the specified configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configured ArxivTool instance
        """
        return cls(config=config.get("arxiv", {})) 