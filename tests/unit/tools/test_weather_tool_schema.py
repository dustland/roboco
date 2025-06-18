"""
Test for the specific weather tool schema that's failing in the examples.

This test reproduces the exact scenario from the tool_chat example
to verify that the weather tool schema is generated correctly.
"""

import pytest
from weather_tool import WeatherTool
from agentx.tool.registry import ToolRegistry


class TestWeatherToolSchema:
    """Test the actual weather tool from the examples."""
    
    def test_weather_tool_schema_generation(self):
        """Test that the weather tool generates correct schema with parameter descriptions."""
        registry = ToolRegistry()
        weather_tool = WeatherTool()
        registry.register_tool(weather_tool)
        
        # Get schema for the weather tool
        schemas = registry.get_tool_schemas(['get_weather'])
        assert len(schemas) == 1
        
        schema = schemas[0]
        print(f"Generated schema: {schema}")
        
        # Verify basic structure
        assert schema['type'] == 'function'
        assert schema['function']['name'] == 'get_weather'
        assert 'parameters' in schema['function']
        
        parameters = schema['function']['parameters']
        assert parameters['type'] == 'object'
        assert 'properties' in parameters
        assert 'location' in parameters['properties']
        
        # This is the critical test - parameter should have description
        location_param = parameters['properties']['location']
        print(f"Location parameter: {location_param}")
        
        assert 'description' in location_param, "Parameter description is missing!"
        assert len(location_param['description']) > 0, "Parameter description is empty!"
        assert location_param['type'] == 'string'
        
        # Required parameters should be listed
        assert 'required' in parameters
        assert 'location' in parameters['required']
    
    def test_weather_tool_all_schemas(self):
        """Test all schemas from the weather tool."""
        registry = ToolRegistry()
        weather_tool = WeatherTool()
        registry.register_tool(weather_tool)
        
        # Get all tool names
        tool_names = registry.list_tools()
        print(f"Registered tools: {tool_names}")
        
        # Get all schemas
        schemas = registry.get_tool_schemas(tool_names)
        print(f"Generated {len(schemas)} schemas")
        
        for schema in schemas:
            print(f"Schema for {schema['function']['name']}: {schema}")
            
            # Each schema should have the required structure
            assert 'function' in schema
            assert 'name' in schema['function']
            assert 'description' in schema['function']
            assert 'parameters' in schema['function']
            
            # Parameters should have properties
            params = schema['function']['parameters']
            if 'properties' in params and params['properties']:
                for param_name, param_info in params['properties'].items():
                    print(f"  Parameter {param_name}: {param_info}")
                    # Each parameter should ideally have a description
                    if 'description' not in param_info:
                        print(f"  WARNING: Parameter {param_name} missing description!")


if __name__ == "__main__":
    # Allow running the test directly
    pytest.main([__file__, "-v", "-s"]) 