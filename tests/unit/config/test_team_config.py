"""
Unit tests for team configuration loading and validation.
Tests the design document's team configuration system.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from agentx.config.team_loader import TeamLoader, load_team_config, validate_team_config
from agentx.config.models import TeamConfig, LLMProviderConfig
from agentx.core.exceptions import ConfigurationError


class TestTeamConfigLoading:
    """Test team configuration loading from YAML files."""
    
    def test_load_basic_team_config(self, temp_dir):
        """Test loading a basic team configuration."""
        # Create team config matching design document
        team_yaml = {
            "name": "test_team",
            "agents": [
                {
                    "name": "researcher",
                    "role": "assistant",
                    "system_message": "You are a researcher.",
                    "tools": ["search"]
                }
            ]
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        # Load config
        config = load_team_config(str(config_file))
        
        assert config.name == "test_team"
        assert len(config.agents) == 1
        assert config.agents[0]["name"] == "researcher"
        assert config.agents[0]["role"] == "assistant"
    
    def test_load_design_document_example(self, temp_dir):
        """Test loading the exact example from the design document."""
        # Create directory structure like design doc
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        # Create team.yaml from design doc
        team_yaml = {
            "name": "research_team",
            "llm_provider": {
                "base_url": "https://api.deepseek.com",
                "api_key": "${DEEPSEEK_API_KEY}",
                "model": "deepseek-chat"
            },
            "agents": [
                {
                    "name": "researcher",
                    "role": "assistant",
                    "prompt_file": "prompts/researcher.md",
                    "tools": ["search", "web_extraction", "memory"]
                },
                {
                    "name": "writer", 
                    "role": "assistant",
                    "prompt_file": "prompts/writer.md",
                    "tools": ["memory"]
                }
            ],
            "collaboration": {
                "speaker_selection_method": "auto",
                "max_rounds": 10,
                "termination_condition": "TERMINATE"
            },
            "tools": {
                "search": {
                    "provider": "serpapi",
                    "max_results": 10
                }
            }
        }
        
        # Create prompt files
        (prompts_dir / "researcher.md").write_text(
            "You are a research specialist focused on AI and technology trends."
        )
        (prompts_dir / "writer.md").write_text(
            "You are a creative writer who transforms research into engaging content."
        )
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        # Load config
        config = load_team_config(str(config_file))
        
        # Validate structure matches design doc
        assert config.name == "research_team"
        assert config.llm_provider.base_url == "https://api.deepseek.com"
        assert config.llm_provider.model == "deepseek-chat"
        assert len(config.agents) == 2
        assert config.speaker_selection_method == "auto"
        assert config.max_rounds == 10
    
    def test_load_with_prompt_files(self, temp_dir):
        """Test loading team config that uses prompt files."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        # Create prompt file
        prompt_content = "You are a helpful AI assistant specialized in research."
        (prompts_dir / "researcher.md").write_text(prompt_content)
        
        team_yaml = {
            "name": "prompt_team",
            "agents": [
                {
                    "name": "researcher",
                    "role": "assistant", 
                    "prompt_file": "prompts/researcher.md",
                    "tools": []
                }
            ]
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        # Load team config and test agent creation
        loader = TeamLoader(str(temp_dir))
        config = loader.load_team_config(str(config_file))
        agents = loader.create_agents(config)
        
        assert len(agents) == 1
        agent_config, tools = agents[0]
        assert agent_config.name == "researcher"
        assert agent_config.prompt_template == prompt_content
    
    def test_prompt_file_fallback_to_system_message(self, temp_dir):
        """Test fallback to system_message when prompt file doesn't exist."""
        team_yaml = {
            "name": "fallback_team",
            "agents": [
                {
                    "name": "assistant",
                    "role": "assistant",
                    "prompt_file": "nonexistent.md",
                    "system_message": "Fallback message",
                    "tools": []
                }
            ]
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        loader = TeamLoader(str(temp_dir))
        config = loader.load_team_config(str(config_file))
        agents = loader.create_agents(config)
        
        agent_config, tools = agents[0]
        # Should use prompt_template when prompt file fails
        assert agent_config.prompt_template == "Fallback message"


class TestTeamConfigValidation:
    """Test team configuration validation."""
    
    def test_validate_valid_config(self, temp_dir):
        """Test validation of a valid team config."""
        team_yaml = {
            "name": "valid_team", 
            "agents": [
                {
                    "name": "agent1",
                    "role": "assistant",
                    "system_message": "Test",
                    "tools": []
                }
            ]
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        result = validate_team_config(str(config_file))
        
        assert result["valid"] == True
        assert result["team_name"] == "valid_team"
        assert result["total_agents"] == 1
        assert "agent1" in result["agents"]
    
    def test_validate_missing_name(self, temp_dir):
        """Test validation fails when team name is missing."""
        team_yaml = {
            "agents": [
                {"name": "agent1", "role": "assistant"}
            ]
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        result = validate_team_config(str(config_file))
        
        assert result["valid"] == False
        assert "name" in result["error"].lower()
    
    def test_validate_no_agents(self, temp_dir):
        """Test validation fails when no agents are defined."""
        team_yaml = {
            "name": "empty_team",
            "agents": []
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        result = validate_team_config(str(config_file))
        
        assert result["valid"] == False
        assert "agent" in result["error"].lower()
    
    def test_validate_duplicate_agent_names(self, temp_dir):
        """Test validation fails with duplicate agent names."""
        team_yaml = {
            "name": "duplicate_team",
            "agents": [
                {"name": "agent1", "role": "assistant"},
                {"name": "agent1", "role": "assistant"}  # Duplicate
            ]
        }
        
        config_file = temp_dir / "team.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(team_yaml, f)
        
        result = validate_team_config(str(config_file))
        
        assert result["valid"] == False
        assert "duplicate" in result["error"].lower()


class TestTeamLoader:
    """Test TeamLoader class functionality."""
    
    def test_team_loader_initialization(self, temp_dir):
        """Test TeamLoader initialization with config directory."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        loader = TeamLoader(str(temp_dir))
        assert loader.config_dir == temp_dir
        assert loader.prompt_loader is not None
    
    def test_team_loader_no_prompts_dir(self, temp_dir):
        """Test TeamLoader initialization without prompts directory."""
        loader = TeamLoader(str(temp_dir))
        assert loader.config_dir == temp_dir
        assert loader.prompt_loader is None
    
    def test_agent_config_creation(self, temp_dir):
        """Test creating AgentConfig objects from raw data."""
        loader = TeamLoader(str(temp_dir))
        
        agent_data = {
            "name": "test_agent",
            "role": "assistant",
            "system_message": "Test message",
            "description": "Test description",
            "tools": ["search"],
            "enable_memory": True
        }
        
        agent_config = loader._create_agent_config(agent_data)
        
        assert agent_config.name == "test_agent"
        assert agent_config.prompt_template == "Test message"
        assert agent_config.description == "Test description"
    
    def test_agent_config_with_any_role(self, temp_dir):
        """Test that agent config accepts any role since validation is removed."""
        loader = TeamLoader(str(temp_dir))
        
        agent_data = {
            "name": "test_agent",
            "role": "any_role_is_fine",  # Role is now ignored
            "system_message": "Test"
        }
        
        # Should not raise an error
        agent_config = loader._create_agent_config(agent_data)
        assert agent_config.name == "test_agent"
        assert agent_config.prompt_template == "Test"


class TestConfigModels:
    """Test configuration model validation and structure."""
    
    def test_llm_provider_config(self):
        """Test LLMProviderConfig model."""
        config = LLMProviderConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model="test-model"
        )
        
        assert config.base_url == "https://api.example.com"
        assert config.api_key == "test-key"
        assert config.model == "test-model"
    
    def test_team_config_collaboration_fields(self):
        """Test TeamConfig collaboration fields (formerly CollaborationConfig)."""
        config = TeamConfig(
            name="test_team",
            agents=[{"name": "agent1", "role": "assistant"}],
            speaker_selection_method="round_robin",
            max_rounds=20,
            termination_condition="DONE"
        )
        
        assert config.speaker_selection_method == "round_robin"
        assert config.max_rounds == 20
        assert config.termination_condition == "DONE"
    
    def test_team_config_collaboration_defaults(self):
        """Test TeamConfig collaboration default values."""
        config = TeamConfig(
            name="test_team",
            agents=[{"name": "agent1", "role": "assistant"}]
        )
        
        assert config.speaker_selection_method == "auto"
        assert config.max_rounds == 10
        assert config.termination_condition == "TERMINATE"
    
    def test_team_config_full(self):
        """Test complete TeamConfig model."""
        team_data = {
            "name": "full_team",
            "description": "A complete team",
            "llm_provider": {
                "base_url": "https://api.test.com",
                "model": "test-model"
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "assistant"
                }
            ],
            "speaker_selection_method": "manual",
            "max_rounds": 15
        }
        
        config = TeamConfig(**team_data)
        
        assert config.name == "full_team"
        assert config.description == "A complete team"
        assert config.llm_provider.base_url == "https://api.test.com"
        assert config.max_rounds == 15
        assert len(config.agents) == 1


class TestErrorHandling:
    """Test error handling in config loading."""
    
    def test_missing_config_file(self):
        """Test error when config file doesn't exist."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_team_config("nonexistent.yaml")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_invalid_yaml(self, temp_dir):
        """Test error handling for invalid YAML."""
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_team_config(str(config_file))
        
        assert "yaml" in str(exc_info.value).lower()
    
    def test_invalid_team_structure(self, temp_dir):
        """Test error for invalid team structure."""
        # Not a dictionary
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("- this is a list, not a dict")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_team_config(str(config_file))
        
        assert "format" in str(exc_info.value).lower()


@pytest.fixture
def sample_team_config():
    """Fixture providing a sample team configuration."""
    return {
        "name": "sample_team",
        "llm_provider": {
            "base_url": "https://api.deepseek.com",
            "model": "deepseek-chat"
        },
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
                "tools": ["memory"]
            }
        ],
        "speaker_selection_method": "auto",
        "max_rounds": 10
    } 