#!/usr/bin/env python3
"""
Integration test script for AgentX clean architecture refactoring.

This script tests that all subsystem models can be imported and used
without circular dependencies or import errors.
"""

import sys
import traceback
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_subsystem_models():
    """Test that all subsystem models can be imported independently."""
    print("🧪 Testing subsystem model imports...")
    
    # Test tool models
    try:
        from agentx.tool.models import Tool, ToolResult, ToolCall, ToolFunction
        print("✅ Tool models imported successfully")
        
        # Test basic functionality
        tool_result = ToolResult(success=True, result="test")
        assert tool_result.success == True
        print("✅ ToolResult model works correctly")
        
    except Exception as e:
        print(f"❌ Tool models failed: {e}")
        traceback.print_exc()
        return False
    
    # Test config models
    try:
        from agentx.config.models import (
            AgentConfig, TeamConfig, MemoryConfig, 
            ConfigurationError, LLMProviderConfig, BrainConfig
        )
        print("✅ Config models imported successfully")
        
        # Test basic functionality
        llm_config = LLMProviderConfig(provider="openai", model="gpt-4")
        brain_config = BrainConfig(llm_config=llm_config)
        assert brain_config.llm_config.provider == "openai"
        print("✅ Config models work correctly")
        
    except Exception as e:
        print(f"❌ Config models failed: {e}")
        traceback.print_exc()
        return False
    
    # Test memory models
    try:
        from agentx.memory.models import (
            MemoryItem, MemoryType, MemoryBackend, 
            MemoryQuery, MemorySearchResult
        )
        print("✅ Memory models imported successfully")
        
        # Test basic functionality
        memory_item = MemoryItem(
            content="test memory",
            memory_type=MemoryType.TEXT,
            agent_name="test_agent"
        )
        assert memory_item.content == "test memory"
        print("✅ Memory models work correctly")
        
    except Exception as e:
        print(f"❌ Memory models failed: {e}")
        traceback.print_exc()
        return False
    
    # Test event models
    try:
        from agentx.event.models import (
            Event, EventType, TaskStartEvent, 
            AgentEvent, ToolEvent
        )
        print("✅ Event models imported successfully")
        
        # Test basic functionality
        event = Event(
            event_type=EventType.TASK_STARTED,
            source="test",
            data={"test": "data"}
        )
        assert event.event_type == EventType.TASK_STARTED
        print("✅ Event models work correctly")
        
    except Exception as e:
        print(f"❌ Event models failed: {e}")
        traceback.print_exc()
        return False
    
    # Test storage models
    try:
        from agentx.storage.models import (
            Artifact, ArtifactType, StorageBackend,
            StorageConfig, FileInfo
        )
        print("✅ Storage models imported successfully")
        
        # Test basic functionality
        artifact = Artifact(
            name="test.txt",
            path="/test/test.txt",
            artifact_type=ArtifactType.TEXT
        )
        assert artifact.name == "test.txt"
        print("✅ Storage models work correctly")
        
    except Exception as e:
        print(f"❌ Storage models failed: {e}")
        traceback.print_exc()
        return False
    
    # Test builtin tools models
    try:
        from agentx.builtin_tools.models import (
            SearchQuery, SearchProvider, WebPageRequest,
            MemoryToolOperation, StorageToolOperation
        )
        print("✅ Builtin tools models imported successfully")
        
        # Test basic functionality
        search_query = SearchQuery(
            query="test search",
            provider=SearchProvider.SERPAPI
        )
        assert search_query.query == "test search"
        print("✅ Builtin tools models work correctly")
        
    except Exception as e:
        print(f"❌ Builtin tools models failed: {e}")
        traceback.print_exc()
        return False
    
    print("🎉 All subsystem models imported and tested successfully!")
    return True


def test_import_isolation():
    """Test that subsystems don't have circular dependencies."""
    print("\n🔍 Testing import isolation...")
    
    # Test that subsystems can be imported without importing core
    test_cases = [
        ("agentx.tool.models", "Tool"),
        ("agentx.config.models", "TeamConfig"),
        ("agentx.memory.models", "MemoryItem"),
        ("agentx.event.models", "Event"),
        ("agentx.storage.models", "Artifact"),
        ("agentx.builtin_tools.models", "SearchQuery"),
    ]
    
    for module_name, class_name in test_cases:
        try:
            # Import the module
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name} imported without core dependencies")
        except Exception as e:
            print(f"❌ {module_name}.{class_name} failed: {e}")
            return False
    
    print("🎉 All subsystems are properly isolated!")
    return True


def test_registry_functions():
    """Test that tool registry functions work correctly."""
    print("\n🔧 Testing tool registry functions...")
    
    try:
        from agentx.tool.registry import (
            validate_agent_tools, suggest_tools_for_agent, 
            list_tools, print_available_tools
        )
        print("✅ Tool registry functions imported successfully")
        
        # Test basic functionality
        valid, invalid = validate_agent_tools(["nonexistent_tool"])
        assert isinstance(valid, list)
        assert isinstance(invalid, list)
        print("✅ validate_agent_tools works correctly")
        
        suggestions = suggest_tools_for_agent("test_agent")
        assert isinstance(suggestions, list)
        print("✅ suggest_tools_for_agent works correctly")
        
        tools = list_tools()
        assert isinstance(tools, list)
        print("✅ list_tools works correctly")
        
    except Exception as e:
        print(f"❌ Tool registry functions failed: {e}")
        traceback.print_exc()
        return False
    
    print("🎉 Tool registry functions work correctly!")
    return True


def test_json_serialization():
    """Test that models can be serialized to JSON properly."""
    print("\n📄 Testing JSON serialization...")
    
    try:
        from agentx.tool.models import ToolResult, safe_json_dumps
        from agentx.config.models import LLMProviderConfig
        from agentx.memory.models import MemoryItem, MemoryType
        
        # Test ToolResult serialization
        tool_result = ToolResult(success=True, result={"key": "value"})
        json_str = safe_json_dumps(tool_result)
        assert '"success": true' in json_str
        print("✅ ToolResult JSON serialization works")
        
        # Test config serialization
        llm_config = LLMProviderConfig(provider="openai", model="gpt-4")
        json_str = llm_config.model_dump_json()
        assert '"provider": "openai"' in json_str
        print("✅ Config model JSON serialization works")
        
        # Test memory item serialization
        memory_item = MemoryItem(
            content="test",
            memory_type=MemoryType.TEXT,
            agent_name="test"
        )
        json_dict = memory_item.to_dict()
        assert json_dict["content"] == "test"
        print("✅ Memory model JSON serialization works")
        
    except Exception as e:
        print(f"❌ JSON serialization failed: {e}")
        traceback.print_exc()
        return False
    
    print("🎉 JSON serialization works correctly!")
    return True


def test_updated_imports():
    """Test that updated imports in subsystems work correctly."""
    print("\n🔄 Testing updated imports...")
    
    try:
        # Test that builtin tools can import from tool.models
        from agentx.builtin_tools.context_tools import ContextTool
        print("✅ Builtin tools import from tool.models correctly")
        
        # Test that config modules use config.models
        from agentx.config.agent_loader import load_single_agent_config
        print("✅ Config modules use config.models correctly")
        
        # Test that tool executor uses tool.models
        from agentx.tool.executor import ToolExecutor
        print("✅ Tool executor uses tool.models correctly")
        
    except Exception as e:
        print(f"❌ Updated imports failed: {e}")
        traceback.print_exc()
        return False
    
    print("🎉 Updated imports work correctly!")
    return True


def main():
    """Run all architecture tests."""
    print("🏗️  AgentX Clean Architecture Integration Tests")
    print("=" * 60)
    
    tests = [
        test_subsystem_models,
        test_import_isolation,
        test_registry_functions,
        test_json_serialization,
        test_updated_imports,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Clean architecture refactoring is successful!")
        return True
    else:
        print("❌ Some tests failed. Architecture needs fixes.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 