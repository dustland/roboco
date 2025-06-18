"""
Unit tests for tool schema generation.

These tests verify that tool schemas are generated correctly with proper
parameter descriptions, which are critical for LLM function calling.
"""

import pytest
from agentx.tool.registry import ToolRegistry
from agentx.tool.base import Tool


class WeatherTool(Tool):
    """Test weather tool for schema validation."""
    
    def get_weather(self, location: str) -> str:
        """
        Get weather forecast for a location.
        
        Args:
            location: The city and state/country for weather lookup
            
        Returns:
            Weather forecast information
        """
        return f"Weather for {location}: Sunny, 25°C"
    
    def get_weather_no_docs(self, city: str) -> str:
        """Get weather without Args section."""
        return f"Weather for {city}"


class TestToolSchemaGeneration:
    """Test tool schema generation with parameter descriptions."""
    
    def test_schema_includes_parameter_descriptions(self):
        """Test that generated schemas include parameter descriptions from docstrings."""
        registry = ToolRegistry()
        weather_tool = WeatherTool()
        registry.register_tool(weather_tool)
        
        # Get schema for the weather tool
        schemas = registry.get_tool_schemas(['get_weather'])
        assert len(schemas) == 1
        
        schema = schemas[0]
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'get_weather'
        assert 'parameters' in schema['function']
        
        parameters = schema['function']['parameters']
        assert parameters['type'] == 'object'
        assert 'properties' in parameters
        assert 'location' in parameters['properties']
        
        # This is the critical test - parameter should have description
        location_param = parameters['properties']['location']
        assert 'description' in location_param
        assert location_param['description'] == "The city and state/country for weather lookup"
        assert location_param['type'] == 'string'
        
        # Required parameters should be listed
        assert 'required' in parameters
        assert 'location' in parameters['required']
    
    def test_schema_without_args_section(self):
        """Test schema generation for functions without Args: section in docstring."""
        registry = ToolRegistry()
        weather_tool = WeatherTool()
        registry.register_tool(weather_tool)
        
        schemas = registry.get_tool_schemas(['get_weather_no_docs'])
        assert len(schemas) == 1
        
        schema = schemas[0]
        parameters = schema['function']['parameters']
        
        # Should still generate schema but without parameter description
        assert 'city' in parameters['properties']
        city_param = parameters['properties']['city']
        
        # Without Args: section, should either have no description or a generic one
        # The exact behavior depends on implementation
        if 'description' in city_param:
            # If description exists, it should not be empty
            assert len(city_param['description']) > 0
    
    def test_complete_schema_structure(self):
        """Test that the complete schema structure matches OpenAI function calling format."""
        registry = ToolRegistry()
        weather_tool = WeatherTool()
        registry.register_tool(weather_tool)
        
        schemas = registry.get_tool_schemas(['get_weather'])
        schema = schemas[0]
        
        # Verify complete OpenAI function calling schema structure
        assert 'type' in schema
        assert schema['type'] == 'function'
        
        assert 'function' in schema
        function = schema['function']
        
        assert 'name' in function
        assert isinstance(function['name'], str)
        
        assert 'description' in function
        assert isinstance(function['description'], str)
        
        assert 'parameters' in function
        parameters = function['parameters']
        
        assert 'type' in parameters
        assert parameters['type'] == 'object'
        
        assert 'properties' in parameters
        assert isinstance(parameters['properties'], dict)
        
        assert 'required' in parameters
        assert isinstance(parameters['required'], list)
    
    def test_multiple_tools_schema(self):
        """Test schema generation for multiple tools."""
        registry = ToolRegistry()
        weather_tool = WeatherTool()
        registry.register_tool(weather_tool)
        
        schemas = registry.get_tool_schemas(['get_weather', 'get_weather_no_docs'])
        assert len(schemas) == 2
        
        # Verify both schemas are present
        schema_names = [s['function']['name'] for s in schemas]
        assert 'get_weather' in schema_names
        assert 'get_weather_no_docs' in schema_names
    
    def test_nonexistent_tool_schema(self):
        """Test requesting schema for non-existent tool."""
        registry = ToolRegistry()
        
        schemas = registry.get_tool_schemas(['nonexistent_tool'])
        # Should return empty list or handle gracefully
        assert isinstance(schemas, list)
        # The exact behavior may vary - some implementations might return empty list,
        # others might log warnings. Both are acceptable.


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__]) 