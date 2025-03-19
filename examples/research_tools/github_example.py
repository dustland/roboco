"""
GitHub Tool Example

This example demonstrates how to use the GitHub tool to search repositories,
get file contents, and clone repositories to the workspace.
"""

import os
import asyncio
from pathlib import Path

from roboco.core import load_config, get_workspace
from roboco.tools.github import GitHubTool
from loguru import logger

async def main():
    """Run the GitHub tool example."""
    # Load configuration
    config = load_config()
    
    # Initialize GitHub tool
    github_tool = GitHubTool(config=config.tools.get("github", {}))
    
    # Print workspace path
    workspace_path = get_workspace()
    print(f"Workspace path: {workspace_path}")
    
    # Search for repositories related to robotics
    print("\n== Searching for robotics repositories ==")
    repo_results = await github_tool.search_repositories(
        query="robotics framework",
        language="python",
        max_results=5
    )
    
    if repo_results["total_count"] > 0:
        print(f"Found {repo_results['total_count']} repositories:")
        for i, repo in enumerate(repo_results["repositories"]):
            print(f"{i+1}. {repo['full_name']}")
            print(f"   Description: {repo['description']}")
            print(f"   Stars: {repo['stars']}")
            print(f"   Language: {repo['language']}")
            print(f"   URL: {repo['html_url']}")
            print()
        
        # Select a repository
        repo_name = repo_results["repositories"][0]["full_name"]
        
        # Get repository details
        print(f"\n== Getting details for repository {repo_name} ==")
        repo_details = await github_tool.get_repository(repo_name)
        
        if repo_details["success"]:
            repo = repo_details["repository"]
            print(f"Name: {repo['name']}")
            print(f"Full Name: {repo['full_name']}")
            print(f"Description: {repo['description']}")
            print(f"Stars: {repo['stars']}")
            print(f"Forks: {repo['forks']}")
            print(f"Language: {repo['language']}")
            print(f"Topics: {', '.join(repo['topics'])}")
            print(f"Default Branch: {repo['default_branch']}")
            print(f"Clone URL: {repo['clone_url']}")
            
            # Get repository contents
            print(f"\n== Getting repository contents for {repo_name} ==")
            contents = await github_tool.get_repository_contents(repo_name)
            
            if contents["success"]:
                print(f"Contents of {repo_name}:")
                for item in contents["contents"]:
                    print(f"  - {item['name']} ({item['type']})")
                
                # Look for README.md file
                readme_path = None
                for item in contents["contents"]:
                    if item["name"].lower() in ["readme.md", "readme.rst", "readme"]:
                        readme_path = item["path"]
                        break
                
                if readme_path:
                    # Get README file content
                    print(f"\n== Getting content of {readme_path} ==")
                    file_content = await github_tool.get_file_content(
                        repo_name, 
                        readme_path,
                        save_to_workspace=True
                    )
                    
                    if file_content["success"]:
                        print(f"File saved to workspace: {file_content.get('workspace_path')}")
                        
                        # Print first 10 lines of README
                        content_lines = file_content["content"].split("\n")
                        print("\nFirst 10 lines of README:")
                        for i, line in enumerate(content_lines[:10]):
                            print(f"{i+1}: {line}")
                    else:
                        print(f"Error getting file content: {file_content.get('error')}")
                
                # Search for code examples in the repository
                print(f"\n== Searching for 'example' in {repo_name} ==")
                code_results = await github_tool.search_code(
                    query="example",
                    repo=repo_name,
                    max_results=5
                )
                
                if code_results["total_count"] > 0:
                    print(f"Found {code_results['total_count']} code matches:")
                    for i, item in enumerate(code_results["items"]):
                        print(f"{i+1}. {item['path']}")
                        print(f"   Repository: {item['repository']['full_name']}")
                        print(f"   URL: {item['html_url']}")
                else:
                    print(f"No code matches found. Error: {code_results.get('error')}")
                
                # Clone the repository (commented out to avoid actual cloning in example)
                # print(f"\n== Cloning repository {repo_name} ==")
                # clone_result = await github_tool.clone_repository(repo_name)
                # 
                # if clone_result["success"]:
                #     print(f"Repository cloned to: {clone_result['workspace_path']}")
                # else:
                #     print(f"Error cloning repository: {clone_result.get('error')}")
            else:
                print(f"Error getting repository contents: {contents.get('error')}")
        else:
            print(f"Error getting repository details: {repo_details.get('error')}")
    else:
        print(f"No repositories found. Error: {repo_results.get('error')}")

if __name__ == "__main__":
    asyncio.run(main()) 