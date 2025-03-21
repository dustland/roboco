"""
Test for the TeamBuilder initialization
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.core.team_builder import TeamBuilder

async def main():
    """Test that TeamBuilder can be initialized with various configurations."""
    
    print("Testing TeamBuilder initialization...")
    
    # Test 1: Default initialization
    builder1 = TeamBuilder()
    print("✓ Default initialization successful")
    
    # Test 2: With custom roles configuration path
    builder2 = TeamBuilder(roles_config_path="config/roles.yaml")
    print("✓ Initialization with custom roles_config_path successful")
    
    # Test 3: With custom prompts directory
    builder3 = TeamBuilder(prompts_dir="config/prompts")
    print("✓ Initialization with custom prompts_dir successful")
    
    # Test 4: With both custom paths
    builder4 = TeamBuilder(
        roles_config_path="config/roles.yaml",
        prompts_dir="config/prompts"
    )
    print("✓ Initialization with both custom paths successful")
    
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 