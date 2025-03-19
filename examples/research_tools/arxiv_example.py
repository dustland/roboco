"""
ArXiv Tool Example

This example demonstrates how to use the ArXiv tool to search for papers,
download them, and save research notes.
"""

import os
import asyncio
from pathlib import Path

from roboco.core import load_config, get_workspace
from roboco.tools.arxiv import ArxivTool
from loguru import logger

async def main():
    """Run the ArXiv tool example."""
    # Load configuration
    config = load_config()
    
    # Initialize ArXiv tool
    arxiv_tool = ArxivTool(config=config.tools.get("arxiv", {}))
    
    # Print workspace path
    workspace_path = get_workspace()
    print(f"Workspace path: {workspace_path}")
    
    # Search for papers on reinforcement learning
    print("\n== Searching for papers on reinforcement learning ==")
    search_results = await arxiv_tool.search(
        query="reinforcement learning robotics",
        max_results=5,
        categories=["cs.RO", "cs.AI"],
        sort_by="relevance"
    )
    
    if search_results["total_results"] > 0:
        print(f"Found {search_results['total_results']} papers:")
        for i, paper in enumerate(search_results["papers"]):
            print(f"{i+1}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'])}")
            print(f"   Categories: {', '.join(paper['categories'])}")
            print(f"   URL: {paper['arxiv_url']}")
            print()
        
        # Get first paper ID
        first_paper_id = search_results["papers"][0]["id"]
        
        # Get detailed metadata for the paper
        print(f"\n== Getting metadata for paper {first_paper_id} ==")
        metadata = await arxiv_tool.get_paper_metadata(first_paper_id)
        
        if metadata["success"]:
            print(f"Title: {metadata['title']}")
            print(f"Authors: {', '.join(metadata['authors'])}")
            print(f"Published: {metadata['published']}")
            print(f"Summary: {metadata['summary'][:200]}...")
            print(f"Categories: {', '.join(metadata['categories'])}")
            print(f"PDF URL: {metadata['pdf_url']}")
            
            # Download the paper
            print(f"\n== Downloading paper {first_paper_id} ==")
            download_result = await arxiv_tool.download_paper(first_paper_id)
            
            if download_result["success"]:
                print(f"Downloaded paper to: {download_result['path']}")
                print(f"Size: {download_result['size_bytes'] / 1024:.2f} KB")
                
                # Save research notes
                print(f"\n== Saving research notes for paper {first_paper_id} ==")
                notes = f"""
This paper discusses reinforcement learning techniques applied to robotics.
Key points:
- Overview of RL algorithms for robot control
- Comparison of model-based and model-free approaches
- Demonstrations in simulation and real-world environments

The methodology looks promising and could be applied to our current robotics project.
                """
                
                notes_result = await arxiv_tool.save_research_notes(
                    first_paper_id, 
                    notes, 
                    topic="reinforcement_learning"
                )
                
                if notes_result["success"]:
                    print(f"Saved research notes to: {notes_result['path']}")
                else:
                    print(f"Error saving notes: {notes_result.get('error')}")
            else:
                print(f"Error downloading paper: {download_result.get('error')}")
        else:
            print(f"Error getting metadata: {metadata.get('error')}")
    else:
        print(f"No papers found. Error: {search_results.get('error')}")

if __name__ == "__main__":
    asyncio.run(main()) 