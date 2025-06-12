#!/usr/bin/env python3
"""
SuperWriter Configuration Validation Script

This script validates the SuperWriter configuration step by step to identify
and fix issues before running the full demo.
"""

import os
import sys
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any

def validate_environment():
    """Validate required environment variables."""
    print("🔍 Step 1: Validating Environment Variables")
    
    required_vars = ["OPENAI_API_KEY", "SERPAPI_KEY"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"   ❌ {var}: Not set")
        else:
            # Show first 8 characters for security
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"   ✅ {var}: {masked_value}")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All environment variables are set\n")
    return True

def validate_config_files():
    """Validate configuration files exist and are valid."""
    print("🔍 Step 2: Validating Configuration Files")
    
    config_path = Path("config/default.yaml")
    if not config_path.exists():
        print(f"   ❌ Configuration file not found: {config_path}")
        return False, None
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"   ✅ Configuration file loaded: {config_path}")
    except yaml.YAMLError as e:
        print(f"   ❌ Invalid YAML in {config_path}: {e}")
        return False, None
    
    # Validate required sections
    required_sections = ["agents", "tools", "memory", "team", "events"]
    for section in required_sections:
        if section not in config:
            print(f"   ❌ Missing required section: {section}")
            return False, None
        print(f"   ✅ Section found: {section}")
    
    print("✅ Configuration file is valid\n")
    return True, config

def validate_prompt_files(config: Dict[str, Any]):
    """Validate all prompt files exist."""
    print("🔍 Step 3: Validating Prompt Files")
    
    agents = config.get("agents", [])
    missing_prompts = []
    
    for agent in agents:
        agent_name = agent.get("name", "unknown")
        prompt_file = agent.get("prompt_file")
        
        if not prompt_file:
            print(f"   ❌ Agent {agent_name}: No prompt_file specified")
            missing_prompts.append(agent_name)
            continue
        
        prompt_path = Path(f"config/prompts/{prompt_file}")
        if not prompt_path.exists():
            print(f"   ❌ Agent {agent_name}: Prompt file not found: {prompt_path}")
            missing_prompts.append(agent_name)
        else:
            print(f"   ✅ Agent {agent_name}: Prompt file found: {prompt_path}")
    
    if missing_prompts:
        print(f"\n❌ Missing prompt files for agents: {', '.join(missing_prompts)}")
        return False
    
    print("✅ All prompt files exist\n")
    return True

def validate_tool_configuration(config: Dict[str, Any]):
    """Validate tool configuration."""
    print("🔍 Step 4: Validating Tool Configuration")
    
    tools = config.get("tools", [])
    agents = config.get("agents", [])
    
    # Check if all tools are properly defined
    tool_names = {tool["name"] for tool in tools}
    print(f"   ✅ Defined tools: {', '.join(tool_names)}")
    
    # Check agent tool references
    for agent in agents:
        agent_name = agent.get("name", "unknown")
        agent_tools = agent.get("tools", [])
        
        for tool_name in agent_tools:
            if tool_name not in tool_names:
                print(f"   ❌ Agent {agent_name}: References undefined tool '{tool_name}'")
                return False
        
        if agent_tools:
            print(f"   ✅ Agent {agent_name}: Tools {agent_tools}")
        else:
            print(f"   ✅ Agent {agent_name}: No tools (memory-only)")
    
    print("✅ Tool configuration is valid\n")
    return True

def validate_memory_configuration(config: Dict[str, Any]):
    """Validate memory configuration."""
    print("🔍 Step 5: Validating Memory Configuration")
    
    memory_config = config.get("memory", {})
    
    required_memory_sections = ["vector_store", "llm", "embedder"]
    for section in required_memory_sections:
        if section not in memory_config:
            print(f"   ❌ Missing memory section: {section}")
            return False
        print(f"   ✅ Memory section found: {section}")
    
    # Check memory database path
    vector_store = memory_config.get("vector_store", {})
    db_path = vector_store.get("config", {}).get("path", "./workspace/memory_db")
    
    # Create directory if it doesn't exist
    Path(db_path).mkdir(parents=True, exist_ok=True)
    print(f"   ✅ Memory database path: {db_path}")
    
    print("✅ Memory configuration is valid\n")
    return True

def validate_event_configuration(config: Dict[str, Any]):
    """Validate event configuration."""
    print("🔍 Step 6: Validating Event Configuration")
    
    events_config = config.get("events", {})
    
    # Check auto_emit_patterns
    patterns = events_config.get("auto_emit_patterns", [])
    if not patterns:
        print("   ❌ No auto_emit_patterns defined")
        return False
    
    print(f"   ✅ Found {len(patterns)} auto-emit patterns:")
    for pattern in patterns:
        event_name = pattern.get("event_name", "unknown")
        metadata_filter = pattern.get("metadata_filter", {})
        print(f"      • {event_name}: {metadata_filter}")
    
    print("✅ Event configuration is valid\n")
    return True

async def validate_imports():
    """Validate that all required imports work."""
    print("🔍 Step 7: Validating Python Imports")
    
    try:
        from roboco import run_team, InMemoryEventBus, EventMonitor
        print("   ✅ Core roboco imports successful")
    except ImportError as e:
        print(f"   ❌ Failed to import roboco components: {e}")
        return False
    
    try:
        from roboco.core.team_manager import TeamManager
        print("   ✅ TeamManager import successful")
    except ImportError as e:
        print(f"   ❌ Failed to import TeamManager: {e}")
        return False
    
    try:
        from roboco.builtin_tools.search_tools import WebSearchTool
        print("   ✅ WebSearchTool import successful")
    except ImportError as e:
        print(f"   ❌ Failed to import WebSearchTool: {e}")
        return False
    
    print("✅ All imports successful\n")
    return True

async def validate_team_creation():
    """Validate that the team can be created from configuration."""
    print("🔍 Step 8: Validating Team Creation")
    
    try:
        from roboco.core.team_manager import TeamManager
        
        team = TeamManager(config_path="config/default.yaml")
        print("   ✅ TeamManager created successfully")
        
        # Check agents
        agent_names = team.list_agents()
        print(f"   ✅ Agents loaded: {', '.join(agent_names)}")
        
        # Check tools
        tool_names = team.list_tools()
        print(f"   ✅ Tools loaded: {', '.join(tool_names)}")
        
        print("✅ Team creation successful\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create team: {e}")
        return False

async def validate_memory_system():
    """Validate memory system initialization."""
    print("🔍 Step 9: Validating Memory System")
    
    try:
        from roboco.memory.manager import MemoryManager
        
        # Load config to get memory settings
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        memory_config = config.get("memory", {})
        memory_manager = MemoryManager(memory_config)
        print("   ✅ MemoryManager created successfully")
        
        # Test basic memory operations
        test_content = "This is a test memory entry for validation"
        test_metadata = {"test": True, "validation": "step_9"}
        
        # Add memory (synchronous, not async) - provide required agent_id
        result = memory_manager.add_memory(
            content=test_content,
            agent_id="validator",
            run_id="validation_test",
            metadata=test_metadata
        )
        
        if result.get("success", True):
            print(f"   ✅ Memory added successfully")
        else:
            print(f"   ⚠️  Memory add returned: {result}")
        
        # Search memory (synchronous, not async) - provide required agent_id
        results = memory_manager.search_memory(
            "test memory", 
            agent_id="validator",
            run_id="validation_test",
            limit=1
        )
        if results:
            print(f"   ✅ Memory search successful: found {len(results)} results")
        else:
            print("   ⚠️  Memory search returned no results (may be normal)")
        
        print("✅ Memory system validation successful\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Memory system validation failed: {e}")
        return False

async def main():
    """Run all validation steps."""
    print("🚀 SuperWriter Configuration Validation")
    print("=" * 50)
    
    validation_steps = [
        ("Environment Variables", validate_environment),
        ("Configuration Files", validate_config_files),
        ("Python Imports", validate_imports),
    ]
    
    config = None
    
    # Run basic validations
    for step_name, step_func in validation_steps:
        if step_name == "Configuration Files":
            success, config = step_func()
        else:
            success = await step_func() if asyncio.iscoroutinefunction(step_func) else step_func()
        
        if not success:
            print(f"❌ Validation failed at step: {step_name}")
            return False
    
    # Run config-dependent validations
    if config:
        config_steps = [
            ("Prompt Files", lambda: validate_prompt_files(config)),
            ("Tool Configuration", lambda: validate_tool_configuration(config)),
            ("Memory Configuration", lambda: validate_memory_configuration(config)),
            ("Event Configuration", lambda: validate_event_configuration(config)),
        ]
        
        for step_name, step_func in config_steps:
            success = step_func()
            if not success:
                print(f"❌ Validation failed at step: {step_name}")
                return False
    
    # Run advanced validations
    advanced_steps = [
        ("Team Creation", validate_team_creation),
        ("Memory System", validate_memory_system),
    ]
    
    for step_name, step_func in advanced_steps:
        success = await step_func()
        if not success:
            print(f"❌ Validation failed at step: {step_name}")
            return False
    
    print("🎉 All validation steps passed!")
    print("✅ SuperWriter configuration is ready for use")
    print("\nYou can now run: python demo.py")
    return True

if __name__ == "__main__":
    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 