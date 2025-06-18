"""
Unit tests for agent configuration loading and validation.
Tests agent YAML loading, tool validation, and template generation.
"""

import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from agentx.config.agent_loader import (
    AgentConfigFile, 
    load_agents_config, 
    load_single_agent_config,
    create_team_config_template,
    create_single_agent_template,
    validate_config_file
)
from agentx.core.exceptions import ConfigurationError


class TestAgentConfigFile:
    """Test AgentConfigFile dataclass."""
    
    def test_agent_config_file_defaults(self):
        """Test AgentConfigFile with default values."""
        config = AgentConfigFile(name="test_agent")
        
        assert config.name == "test_agent"
        assert config.role == "assistant"
        assert config.system_message is None
        assert config.prompt_file is None
        assert config.tools == []
        assert config.enable_memory == True
        assert config.auto_reply == True
    
    def test_agent_config_file_custom_values(self):
        """Test AgentConfigFile with custom values."""
        config = AgentConfigFile(
            name="custom_agent",
            role="system",
            system_message="Custom message",
            prompt_file="prompts/custom.md",
            tools=["search", "memory"],
            enable_code_execution=True,
            enable_memory=False
        )
        
        assert config.name == "custom_agent"
        assert config.role == "system"
        assert config.system_message == "Custom message"
        assert config.prompt_file == "prompts/custom.md"
        assert config.tools == ["search", "memory"]
        assert config.enable_code_execution == True
        assert config.enable_memory == False
    
    def test_agent_config_file_post_init(self):
        """Test AgentConfigFile post-init processing."""
        # Test with None tools
        config = AgentConfigFile(name="test", tools=None)
        assert config.tools == []
        
        # Test with explicit tools
        config = AgentConfigFile(name="test", tools=["search"])
        assert config.tools == ["search"]


class TestLoadAgentsConfig:
    """Test loading agent configurations from YAML files."""
    
    @patch('agentx.config.agent_loader.validate_agent_tools')
    def test_load_single_agent_config_format(self, mock_validate, temp_dir):
        """Test loading single agent configuration format."""
        mock_validate.return_value = (["search"], [])
        
        agent_yaml = {
            "name": "researcher",
            "role": "assistant",
            "system_message": "You are a researcher.",
            "tools": ["search"]
        }
        
        config_file = temp_dir / "agent.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_yaml, f)
        
        agents = load_agents_config(str(config_file), validate_tools=True)
        
        assert len(agents) == 1
        agent_config, tools = agents[0]
        assert agent_config.name == "researcher"
        assert agent_config.description == "AI assistant named researcher"
        assert agent_config.prompt_template == "You are a researcher."
        assert tools == ["search"]
    
    @patch('agentx.config.agent_loader.validate_agent_tools')
    def test_load_multiple_agents_config_format(self, mock_validate, temp_dir):
        """Test loading multiple agents configuration format."""
        mock_validate.return_value = (["search"], [])
        
        agents_yaml = {
            "agents": [
                {
                    "name": "researcher",
                    "role": "assistant",
                    "system_message": "You are a researcher.",
                    "tools": ["search"]
                },
                {
                    "name": "writer",
                    "role": "assistant",
                    "system_message": "You are a writer.",
                    "tools": []
                }
            ]
        }
        
        config_file = temp_dir / "agents.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agents_yaml, f)
        
        agents = load_agents_config(str(config_file), validate_tools=True)
        
        assert len(agents) == 2
        
        researcher_config, researcher_tools = agents[0]
        assert researcher_config.name == "researcher"
        assert researcher_tools == ["search"]
        
        writer_config, writer_tools = agents[1]
        assert writer_config.name == "writer"
        assert writer_tools == []
    
    def test_load_agents_config_with_prompt_file(self, temp_dir):
        """Test loading agent config that specifies prompt_file."""
        agent_yaml = {
            "name": "prompt_agent",
            "role": "assistant",
            "prompt_file": "prompts/agent.md",
            "tools": []
        }
        
        config_file = temp_dir / "agent.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_yaml, f)
        
        agents = load_agents_config(str(config_file), validate_tools=False)
        
        assert len(agents) == 1
        agent_config, tools = agents[0]
        assert agent_config.prompt_template == "prompts/agent.md"
    
    @patch('agentx.config.agent_loader.validate_agent_tools')
    def test_load_agents_invalid_tools(self, mock_validate, temp_dir):
        """Test error handling for invalid tools."""
        mock_validate.return_value = ([], ["invalid_tool"])
        
        agent_yaml = {
            "name": "test_agent",
            "tools": ["invalid_tool"]
        }
        
        config_file = temp_dir / "agent.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_yaml, f)
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_agents_config(str(config_file), validate_tools=True)
        
        assert "invalid tools" in str(exc_info.value).lower()


class TestLoadSingleAgentConfig:
    """Test loading single agent configurations."""
    
    def test_load_single_from_single_config(self, temp_dir):
        """Test loading single agent from single-agent config file."""
        agent_yaml = {
            "name": "solo_agent",
            "role": "assistant",
            "system_message": "Solo agent"
        }
        
        config_file = temp_dir / "solo.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_yaml, f)
        
        agent_config, tools = load_single_agent_config(str(config_file), validate_tools=False)
        
        assert agent_config.name == "solo_agent"
        assert agent_config.prompt_template == "Solo agent"
    
    def test_load_single_from_multi_config(self, temp_dir):
        """Test loading specific agent from multi-agent config file."""
        agents_yaml = {
            "agents": [
                {"name": "agent1", "system_message": "Agent 1"},
                {"name": "agent2", "system_message": "Agent 2"}
            ]
        }
        
        config_file = temp_dir / "multi.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agents_yaml, f)
        
        # Load specific agent
        agent_config, tools = load_single_agent_config(
            str(config_file), agent_name="agent2", validate_tools=False
        )
        
        assert agent_config.name == "agent2"
        assert agent_config.prompt_template == "Agent 2"
    
    def test_load_single_agent_not_found(self, temp_dir):
        """Test error when specified agent not found."""
        agents_yaml = {
            "agents": [
                {"name": "agent1", "system_message": "Agent 1"}
            ]
        }
        
        config_file = temp_dir / "multi.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agents_yaml, f)
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_single_agent_config(
                str(config_file), agent_name="nonexistent", validate_tools=False
            )
        
        assert "not found" in str(exc_info.value).lower()


class TestTemplateGeneration:
    """Test configuration template generation."""
    
    @patch('agentx.config.agent_loader.list_tools')
    @patch('agentx.config.agent_loader.suggest_tools_for_agent')
    def test_create_team_config_template(self, mock_suggest, mock_list, temp_dir):
        """Test creating team configuration template."""
        mock_list.return_value = ["search", "memory", "web"]
        mock_suggest.return_value = ["search"]
        
        output_path = temp_dir / "team_template.yaml"
        
        result_path = create_team_config_template(
            team_name="test_team",
            agent_names=["researcher", "writer"],
            output_path=str(output_path),
            include_suggestions=True
        )
        
        assert result_path == str(output_path)
        assert output_path.exists()
        
        # Read and verify template content
        content = output_path.read_text()
        assert "test_team" in content
        assert "researcher" in content
        assert "writer" in content
        assert "prompt_file" in content
    
    @patch('agentx.config.agent_loader.list_tools')
    @patch('agentx.config.agent_loader.suggest_tools_for_agent')
    def test_create_single_agent_template(self, mock_suggest, mock_list, temp_dir):
        """Test creating single agent configuration template."""
        mock_list.return_value = ["search", "memory"]
        mock_suggest.return_value = ["search"]
        
        output_path = temp_dir / "agent_template.yaml"
        
        result_path = create_single_agent_template(
            agent_name="test_agent",
            output_path=str(output_path),
            include_suggestions=True
        )
        
        assert result_path == str(output_path)
        assert output_path.exists()
        
        # Read and verify template content
        content = output_path.read_text()
        assert "test_agent" in content
        assert "prompt_file" in content
        assert "tools:" in content
    
    def test_template_without_suggestions(self, temp_dir):
        """Test template generation without tool suggestions."""
        output_path = temp_dir / "no_suggestions.yaml"
        
        with patch('agentx.config.agent_loader.list_tools') as mock_list:
            mock_list.return_value = ["search", "memory"]
            
            create_single_agent_template(
                agent_name="simple_agent",
                output_path=str(output_path),
                include_suggestions=False
            )
        
        content = output_path.read_text()
        assert "simple_agent" in content
        # Should not include specific tool suggestions
        assert "# Add tool names here" in content


class TestValidateConfigFile:
    """Test configuration file validation."""
    
    @patch('agentx.config.agent_loader.validate_agent_tools')
    def test_validate_valid_config(self, mock_validate, temp_dir):
        """Test validation of valid configuration file."""
        mock_validate.return_value = (["search"], [])
        
        config_yaml = {
            "agents": [
                {
                    "name": "agent1",
                    "role": "assistant",
                    "tools": ["search"]
                },
                {
                    "name": "agent2", 
                    "role": "assistant",
                    "tools": []
                }
            ]
        }
        
        config_file = temp_dir / "valid.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_yaml, f)
        
        result = validate_config_file(str(config_file))
        
        assert result["valid"] == True
        assert result["total_agents"] == 2
        assert "agent1" in result["agents"]
        assert "agent2" in result["agents"]
        assert "search" in result["tools_used"]
    
    def test_validate_invalid_config(self, temp_dir):
        """Test validation of configuration with ignored role field."""
        config_yaml = {
            "agents": [
                {
                    "name": "agent1",
                    "role": "any_role_is_fine"  # Role field is now ignored
                }
            ]
        }
        
        config_file = temp_dir / "config_with_role.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_yaml, f)
        
        result = validate_config_file(str(config_file))
        
        # Should pass since role validation is removed
        assert result["valid"] == True
        assert result["total_agents"] == 1
        assert "agent1" in result["agents"]


class TestErrorHandling:
    """Test error handling in agent loading."""
    
    def test_missing_config_file(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_agents_config("nonexistent.yaml")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_invalid_yaml_syntax(self, temp_dir):
        """Test error with invalid YAML syntax."""
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: [")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_agents_config(str(config_file))
        
        assert "yaml" in str(exc_info.value).lower()
    
    def test_invalid_config_structure(self, temp_dir):
        """Test error with invalid configuration structure."""
        # Missing required 'agents' or 'name' field
        config_yaml = {"invalid": "structure"}
        
        config_file = temp_dir / "bad_structure.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_yaml, f)
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_agents_config(str(config_file))
        
        assert "invalid config format" in str(exc_info.value).lower()
    
    def test_invalid_agent_structure(self, temp_dir):
        """Test error with invalid agent structure."""
        config_yaml = {
            "agents": [
                {
                    "invalid_field": "value"  # Missing 'name' field
                }
            ]
        }
        
        config_file = temp_dir / "bad_agent.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_yaml, f)
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_agents_config(str(config_file))
        
        assert "invalid agent config structure" in str(exc_info.value).lower()


@pytest.fixture
def sample_agent_configs():
    """Fixture providing sample agent configurations."""
    return {
        "single_agent": {
            "name": "solo_researcher",
            "role": "assistant",
            "system_message": "You are a research specialist.",
            "tools": ["search", "web_extraction"],
            "enable_memory": True
        },
        "multi_agent": {
            "agents": [
                {
                    "name": "researcher",
                    "role": "assistant",
                    "prompt_file": "prompts/researcher.md",
                    "tools": ["search"]
                },
                {
                    "name": "writer",
                    "role": "assistant", 
                    "system_message": "You are a creative writer.",
                    "tools": ["memory"]
                },
                {
                    "name": "coordinator",
                    "role": "system",
                    "system_message": "You coordinate the team.",
                    "tools": []
                }
            ]
        }
    } 