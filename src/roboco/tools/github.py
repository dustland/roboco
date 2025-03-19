"""
GitHub Tool

This module provides tools for interacting with GitHub repositories, issues, and code.
"""

import os
import json
import base64
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from github import Github, Repository, ContentFile
from github.GithubException import GithubException

from roboco.core import Tool, get_workspace
from roboco.core.logger import get_logger

logger = get_logger(__name__)

class GitHubTool(Tool):
    """Tool for interacting with GitHub repositories."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the GitHub tool.
        
        Args:
            config: Optional configuration for the tool
        """
        self.config = config or {}
        self.token = self.config.get("token", os.environ.get("GITHUB_TOKEN", ""))
        self.max_results = self.config.get("max_results", 10)
        self.timeout = self.config.get("timeout", 30)
        self.rate_limit_delay = self.config.get("rate_limit_delay", 1)  # Seconds between requests
        
        # Initialize PyGithub client
        try:
            self.github = Github(self.token, timeout=self.timeout)
            logger.info("GitHub client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing GitHub client: {e}")
            self.github = None
        
        # Cache for search results
        self.cache = {}
        self.cache_dir = self.config.get("cache_dir", None)
        
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            
        # Define the search repositories function
        def search_github_repos(query: str, language: Optional[str] = None, 
                              sort: str = "stars", max_results: Optional[int] = None) -> Dict[str, Any]:
            """
            Search GitHub for repositories matching the query.
            
            Args:
                query: The search query
                language: Filter by programming language (e.g. "python", "javascript")
                sort: Sort by "stars", "forks", "updated", "help-wanted-issues"
                max_results: Maximum number of results to return
                
            Returns:
                Dictionary containing search results
            """
            return asyncio.run(self.search_repositories(query, language, sort, "desc", max_results))
        
        # Initialize the Tool parent class with the search_repositories function
        super().__init__(
            name="search_github_repos",
            description="Search GitHub for repositories matching a query, optionally filtering by language",
            func_or_tool=search_github_repos
        )
        
        logger.info("Initialized GitHubTool")
    
    async def search_repositories(self, query: str, language: Optional[str] = None, 
                                 sort: str = "stars", order: str = "desc", 
                                 max_results: Optional[int] = None) -> Dict[str, Any]:
        """Search GitHub for repositories matching the query.
        
        Args:
            query: The search query
            language: Filter by programming language
            sort: Sort by "stars", "forks", "updated", "help-wanted-issues"
            order: Sort order "desc" or "asc"
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
        """
        cache_key = f"repo_{query}_{language}_{sort}_{order}_{max_results}"
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"Using cached results for repo query: {query}")
            return self.cache[cache_key]
        
        # Prepare search parameters
        search_query = query
        if language:
            search_query = f"{search_query} language:{language}"
        
        results_limit = max_results or self.max_results
        
        logger.info(f"Searching GitHub repositories for: {search_query}")
        
        try:
            if not self.github:
                raise ValueError("GitHub client not initialized")
                
            # Execute search with PyGithub
            repo_results = self.github.search_repositories(
                query=search_query, 
                sort=sort, 
                order=order
            )
            
            # Extract repository information
            repos = []
            for i, repo in enumerate(repo_results):
                if i >= results_limit:
                    break
                    
                repo_dict = {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "html_url": repo.html_url,
                    "api_url": repo.url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "issues": repo.open_issues_count,
                    "language": repo.language,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "owner": {
                        "login": repo.owner.login,
                        "url": repo.owner.html_url
                    }
                }
                repos.append(repo_dict)
                
                # Add small delay to avoid rate limiting
                time.sleep(self.rate_limit_delay)
            
            result = {
                "query": search_query,
                "success": True,
                "total_count": repo_results.totalCount,
                "repositories": repos
            }
            
            # Cache the results
            self.cache[cache_key] = result
            
            # Save to cache directory if enabled
            if self.cache_dir:
                cache_file = Path(self.cache_dir) / f"github_repo_{query.replace(' ', '_')}.json"
                with open(cache_file, "w") as f:
                    json.dump(result, f, indent=2)
            
            logger.info(f"Found {len(repos)} repositories for query: {search_query}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error searching GitHub repositories: {e}")
            return {
                "query": search_query,
                "success": False,
                "total_count": 0,
                "repositories": [],
                "error": str(e)
            }
    
    async def get_repository(self, repo_name: str) -> Dict[str, Any]:
        """Get details about a specific GitHub repository.
        
        Args:
            repo_name: The repository name in the format "owner/repo"
            
        Returns:
            Dictionary with repository details
        """
        try:
            if not self.github:
                raise ValueError("GitHub client not initialized")
                
            # Get repository using PyGithub
            repo = self.github.get_repo(repo_name)
            
            return {
                "success": True,
                "repository": {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "html_url": repo.html_url,
                    "api_url": repo.url,
                    "clone_url": repo.clone_url,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "issues": repo.open_issues_count,
                    "language": repo.language,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "homepage": repo.homepage,
                    "license": repo.license.name if repo.license else None,
                    "topics": repo.topics,
                    "has_wiki": repo.has_wiki,
                    "has_pages": repo.has_pages,
                    "default_branch": repo.default_branch,
                    "owner": {
                        "login": repo.owner.login,
                        "url": repo.owner.html_url
                    }
                }
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error for repository {repo_name}: {e}")
            return {
                "success": False,
                "error": f"GitHub API error: {e.status} - {e.data.get('message', str(e))}"
            }
        except Exception as e:
            logger.error(f"Error getting repository details for {repo_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_repository_contents(self, repo_name: str, path: str = "") -> Dict[str, Any]:
        """Get the contents of a repository directory or file.
        
        Args:
            repo_name: The repository name in the format "owner/repo"
            path: Path to the file or directory within the repository
            
        Returns:
            Dictionary with repository contents
        """
        try:
            if not self.github:
                raise ValueError("GitHub client not initialized")
                
            # Get repository and contents
            repo = self.github.get_repo(repo_name)
            contents = repo.get_contents(path)
            
            # Handle both file and directory contents
            if isinstance(contents, list):
                # Directory contents
                items = []
                for item in contents:
                    items.append({
                        "name": item.name,
                        "path": item.path,
                        "type": "file" if item.type == "file" else "directory",
                        "size": item.size if item.type == "file" else None,
                        "url": item.html_url
                    })
                
                return {
                    "success": True,
                    "repository": repo_name,
                    "path": path,
                    "type": "directory",
                    "contents": items
                }
            else:
                # Single file contents
                content = None
                if contents.encoding == "base64" and contents.content:
                    content = base64.b64decode(contents.content).decode("utf-8", errors="replace")
                
                return {
                    "success": True,
                    "repository": repo_name,
                    "path": path,
                    "type": "file",
                    "name": contents.name,
                    "size": contents.size,
                    "url": contents.html_url,
                    "content": content
                }
            
        except GithubException as e:
            logger.error(f"GitHub API error for {repo_name}/{path}: {e}")
            return {
                "success": False,
                "repository": repo_name,
                "path": path,
                "error": f"GitHub API error: {e.status} - {e.data.get('message', str(e))}"
            }
        except Exception as e:
            logger.error(f"Error getting repository contents for {repo_name}/{path}: {e}")
            return {
                "success": False,
                "repository": repo_name,
                "path": path,
                "error": str(e)
            }
    
    async def get_file_content(self, repo_name: str, file_path: str, save_to_workspace: bool = False, 
                              workspace_path: Optional[str] = None) -> Dict[str, Any]:
        """Get the content of a specific file from a repository.
        
        Args:
            repo_name: The repository name in the format "owner/repo"
            file_path: Path to the file within the repository
            save_to_workspace: Whether to save the file to the workspace
            workspace_path: Optional custom path within workspace to save the file
            
        Returns:
            Dictionary with file content
        """
        try:
            # Get the file content
            file_result = await self.get_repository_contents(repo_name, file_path)
            
            if not file_result.get("success", False) or file_result.get("type") != "file":
                return file_result
            
            content = file_result.get("content")
            
            # Save to workspace if requested
            if save_to_workspace and content:
                # Extract repository owner and name
                owner, repo = repo_name.split("/")
                
                if workspace_path:
                    # Use custom workspace path
                    save_dir = get_workspace() / workspace_path
                else:
                    # Use default structure: code/github/{owner}/{repo}/...
                    save_dir = get_workspace() / "code" / "github" / owner / repo
                
                # Create directory structure
                os.makedirs(save_dir, exist_ok=True)
                
                # Get file name from path
                file_name = os.path.basename(file_path)
                target_path = save_dir / file_name
                
                # Save the file
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                file_result["workspace_path"] = str(target_path)
                logger.info(f"Saved file to workspace: {target_path}")
            
            return file_result
            
        except Exception as e:
            logger.error(f"Error getting file content for {repo_name}/{file_path}: {e}")
            return {
                "success": False,
                "repository": repo_name,
                "path": file_path,
                "error": str(e)
            }
    
    async def search_code(self, query: str, language: Optional[str] = None, 
                         repo: Optional[str] = None, path: Optional[str] = None,
                         max_results: Optional[int] = None) -> Dict[str, Any]:
        """Search for code on GitHub matching the query.
        
        Args:
            query: The search query
            language: Filter by programming language
            repo: Filter by repository in the format "owner/repo"
            path: Filter by file path
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
        """
        cache_key = f"code_{query}_{language}_{repo}_{path}_{max_results}"
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"Using cached results for code query: {query}")
            return self.cache[cache_key]
        
        # Prepare search parameters
        search_query = query
        if language:
            search_query = f"{search_query} language:{language}"
        if repo:
            search_query = f"{search_query} repo:{repo}"
        if path:
            search_query = f"{search_query} path:{path}"
        
        results_limit = max_results or self.max_results
        
        logger.info(f"Searching GitHub code for: {search_query}")
        
        try:
            if not self.github:
                raise ValueError("GitHub client not initialized")
                
            # Execute search with PyGithub
            code_results = self.github.search_code(query=search_query)
            
            # Extract code information
            items = []
            for i, code_item in enumerate(code_results):
                if i >= results_limit:
                    break
                    
                item_dict = {
                    "name": code_item.name,
                    "path": code_item.path,
                    "repository": {
                        "name": code_item.repository.name,
                        "full_name": code_item.repository.full_name,
                        "url": code_item.repository.html_url
                    },
                    "html_url": code_item.html_url,
                    "url": code_item.url
                }
                items.append(item_dict)
                
                # Add small delay to avoid rate limiting
                time.sleep(self.rate_limit_delay)
            
            result = {
                "query": search_query,
                "success": True,
                "total_count": code_results.totalCount,
                "items": items
            }
            
            # Cache the results
            self.cache[cache_key] = result
            
            # Save to cache directory if enabled
            if self.cache_dir:
                cache_file = Path(self.cache_dir) / f"github_code_{query.replace(' ', '_')}.json"
                with open(cache_file, "w") as f:
                    json.dump(result, f, indent=2)
            
            logger.info(f"Found {len(items)} code items for query: {search_query}")
            
            return result
            
        except GithubException as e:
            logger.error(f"GitHub API error for code search '{search_query}': {e}")
            return {
                "query": search_query,
                "success": False,
                "total_count": 0,
                "items": [],
                "error": f"GitHub API error: {e.status} - {e.data.get('message', str(e))}"
            }
        except Exception as e:
            logger.error(f"Error searching GitHub code: {e}")
            return {
                "query": search_query,
                "success": False,
                "total_count": 0,
                "items": [],
                "error": str(e)
            }
    
    async def clone_repository(self, repo_name: str, workspace_subdir: Optional[str] = None) -> Dict[str, Any]:
        """Clone a GitHub repository to the workspace.
        
        Args:
            repo_name: The repository name in the format "owner/repo"
            workspace_subdir: Optional subdirectory within workspace/code
            
        Returns:
            Dictionary with clone result
        """
        try:
            # Get repository details
            repo_details = await self.get_repository(repo_name)
            
            if not repo_details.get("success", False):
                return repo_details
            
            # Extract clone URL
            clone_url = repo_details.get("repository", {}).get("clone_url")
            
            if not clone_url:
                return {
                    "success": False,
                    "repository": repo_name,
                    "error": "Could not find clone URL for repository"
                }
            
            # Extract repository owner and name
            owner, repo = repo_name.split("/")
            
            # Determine target directory
            if workspace_subdir:
                target_dir = get_workspace() / "code" / workspace_subdir / repo
            else:
                target_dir = get_workspace() / "code" / "github" / owner / repo
            
            # Check if directory already exists
            if os.path.exists(target_dir):
                return {
                    "success": True,
                    "repository": repo_name,
                    "workspace_path": str(target_dir),
                    "message": "Repository already exists in workspace"
                }
            
            # Create parent directory
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # Execute git clone command
            import subprocess
            
            logger.info(f"Cloning repository {repo_name} to {target_dir}")
            
            result = subprocess.run(
                ["git", "clone", clone_url, str(target_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            return {
                "success": True,
                "repository": repo_name,
                "workspace_path": str(target_dir),
                "output": result.stdout
            }
            
        except Exception as e:
            logger.error(f"Error cloning repository {repo_name}: {e}")
            return {
                "success": False,
                "repository": repo_name,
                "error": str(e)
            }
    
    # Helper method to register additional functions
    def register_function(self, func):
        """Register an additional function with this tool."""
        self._function = func
        
    @classmethod
    def create_with_config(cls, config: Dict[str, Any]) -> 'GitHubTool':
        """Create an instance with the specified configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configured GitHubTool instance
        """
        return cls(config=config.get("github", {})) 