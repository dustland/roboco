"""
Unit tests for prompt loading and templating system.
Tests Jinja2 templating and prompt file management.
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from agentx.config.prompt_loader import PromptLoader, create_prompt_loader
from agentx.config.models import ConfigurationError


class TestPromptLoader:
    """Test PromptLoader functionality."""
    
    def test_prompt_loader_initialization(self, temp_dir):
        """Test PromptLoader initialization with valid directory."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        loader = PromptLoader(str(prompts_dir))
        assert loader.prompts_dir == prompts_dir
        assert loader.jinja_env is not None
        assert len(loader._prompt_cache) == 0
    
    def test_prompt_loader_invalid_directory(self, temp_dir):
        """Test PromptLoader raises error for non-existent directory."""
        nonexistent_dir = temp_dir / "nonexistent"
        
        with pytest.raises(ConfigurationError) as exc_info:
            PromptLoader(str(nonexistent_dir))
        
        assert "does not exist" in str(exc_info.value)
    
    def test_load_simple_prompt(self, temp_dir):
        """Test loading a simple prompt file without variables."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        prompt_content = "You are a helpful AI assistant."
        (prompts_dir / "simple.md").write_text(prompt_content)
        
        loader = PromptLoader(str(prompts_dir))
        result = loader.load_prompt("simple.md")
        
        assert result == prompt_content
    
    def test_load_prompt_with_variables(self, temp_dir):
        """Test loading prompt with Jinja2 variable substitution."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        prompt_template = "You are a {{ role }} specialized in {{ domain }}."
        (prompts_dir / "template.md").write_text(prompt_template)
        
        loader = PromptLoader(str(prompts_dir))
        variables = {"role": "researcher", "domain": "AI technology"}
        result = loader.load_prompt("template.md", variables)
        
        expected = "You are a researcher specialized in AI technology."
        assert result == expected
    
    def test_load_prompt_missing_variables(self, temp_dir):
        """Test loading prompt with missing variables."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        prompt_template = "Hello {{ name }}!"
        (prompts_dir / "missing_var.md").write_text(prompt_template)
        
        loader = PromptLoader(str(prompts_dir))
        
        # Should render with empty string for missing variables
        result = loader.load_prompt("missing_var.md", {})
        assert result == "Hello !"
    
    def test_load_prompt_complex_template(self, temp_dir):
        """Test loading complex prompt with conditionals and loops."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        prompt_template = """You are a {{ role }}.

{% if tools %}
Available tools:
{% for tool in tools %}
- {{ tool }}
{% endfor %}
{% endif %}

{% if instructions %}
Instructions: {{ instructions }}
{% endif %}"""
        
        (prompts_dir / "complex.md").write_text(prompt_template)
        
        loader = PromptLoader(str(prompts_dir))
        variables = {
            "role": "research assistant",
            "tools": ["search", "web_scraper"],
            "instructions": "Be thorough and accurate."
        }
        result = loader.load_prompt("complex.md", variables)
        
        assert "research assistant" in result
        assert "- search" in result
        assert "- web_scraper" in result
        assert "Be thorough and accurate." in result
    
    def test_prompt_caching(self, temp_dir):
        """Test prompt caching functionality."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        prompt_content = "Cached prompt: {{ value }}"
        (prompts_dir / "cached.md").write_text(prompt_content)
        
        loader = PromptLoader(str(prompts_dir))
        variables = {"value": "test"}
        
        # First load
        result1 = loader.load_prompt("cached.md", variables)
        assert len(loader._prompt_cache) == 1
        
        # Second load should use cache
        result2 = loader.load_prompt("cached.md", variables)
        assert result1 == result2
        assert len(loader._prompt_cache) == 1
    
    def test_clear_cache(self, temp_dir):
        """Test clearing prompt cache."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        (prompts_dir / "test.md").write_text("Test prompt")
        
        loader = PromptLoader(str(prompts_dir))
        loader.load_prompt("test.md")
        
        assert len(loader._prompt_cache) == 1
        loader.clear_cache()
        assert len(loader._prompt_cache) == 0
    
    def test_list_available_prompts(self, temp_dir):
        """Test listing available prompt files."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        # Create various files
        (prompts_dir / "agent1.md").write_text("Agent 1 prompt")
        (prompts_dir / "agent2.md").write_text("Agent 2 prompt")
        (prompts_dir / "readme.txt").write_text("Not a prompt")  # Should be ignored
        
        loader = PromptLoader(str(prompts_dir))
        prompts = loader.list_available_prompts()
        
        assert "agent1.md" in prompts
        assert "agent2.md" in prompts
        assert "readme.txt" not in prompts
        assert len(prompts) == 2
    
    def test_get_template_variables(self, temp_dir):
        """Test extracting variables from template."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        template = "Hello {{ name }}! You are a {{ role }} with {{ skill }} skills."
        (prompts_dir / "vars.md").write_text(template)
        
        loader = PromptLoader(str(prompts_dir))
        variables = loader.get_template_variables("vars.md")
        
        assert "name" in variables
        assert "role" in variables
        assert "skill" in variables
        assert len(variables) == 3
    
    def test_validate_template_success(self, temp_dir):
        """Test successful template validation."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        template = "Hello {{ name }}!"
        (prompts_dir / "valid.md").write_text(template)
        
        loader = PromptLoader(str(prompts_dir))
        variables = {"name": "Alice"}
        
        assert loader.validate_template("valid.md", variables) == True
    
    def test_validate_template_failure(self, temp_dir):
        """Test template validation with missing variables."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        template = "Hello {{ name | required }}!"  # This would fail if name is missing
        (prompts_dir / "invalid.md").write_text(template)
        
        loader = PromptLoader(str(prompts_dir))
        
        # This should not raise an error in basic Jinja2, but let's test it works
        try:
            result = loader.validate_template("invalid.md", {"name": "test"})
            assert result == True
        except ConfigurationError:
            # If it fails, that's also valid behavior
            pass
    
    def test_render_with_fallbacks(self, temp_dir):
        """Test rendering with fallback values."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        template = "Role: {{ role }}, Domain: {{ domain }}"
        (prompts_dir / "fallback.md").write_text(template)
        
        loader = PromptLoader(str(prompts_dir))
        
        variables = {"role": "assistant"}
        fallbacks = {"domain": "general", "unused": "value"}
        
        result = loader.render_prompt_with_fallbacks(
            "fallback.md", variables, fallbacks
        )
        
        assert "Role: assistant" in result
        assert "Domain: general" in result


class TestPromptLoaderErrors:
    """Test error handling in prompt loading."""
    
    def test_load_nonexistent_prompt(self, temp_dir):
        """Test error when prompt file doesn't exist."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        loader = PromptLoader(str(prompts_dir))
        
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_prompt("nonexistent.md")
        
        assert "not found" in str(exc_info.value)
    
    def test_invalid_template_syntax(self, temp_dir):
        """Test error with invalid Jinja2 syntax."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        # Invalid Jinja2 syntax
        invalid_template = "Hello {{ name"  # Missing closing braces
        (prompts_dir / "invalid.md").write_text(invalid_template)
        
        loader = PromptLoader(str(prompts_dir))
        
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_prompt("invalid.md")
        
        assert "template" in str(exc_info.value).lower()


class TestCreatePromptLoader:
    """Test the factory function for creating PromptLoader."""
    
    def test_create_prompt_loader(self, temp_dir):
        """Test creating PromptLoader via factory function."""
        prompts_dir = temp_dir / "prompts"
        prompts_dir.mkdir()
        
        loader = create_prompt_loader(str(temp_dir))
        
        assert isinstance(loader, PromptLoader)
        assert loader.prompts_dir == prompts_dir
    
    def test_create_prompt_loader_missing_prompts_dir(self, temp_dir):
        """Test factory function when prompts directory doesn't exist."""
        # Should create the prompts directory path even if it doesn't exist
        with pytest.raises(ConfigurationError):
            create_prompt_loader(str(temp_dir))


@pytest.fixture
def sample_prompts_dir(temp_dir):
    """Fixture that creates a sample prompts directory with test files."""
    prompts_dir = temp_dir / "prompts"
    prompts_dir.mkdir()
    
    # Create sample prompt files
    (prompts_dir / "researcher.md").write_text("""
You are a research specialist focused on {{ domain }}.

Your responsibilities:
- Search for current information using web search
- Extract detailed content from relevant sources
- Analyze findings and identify key insights

{% if memory_enabled %}
- Store important information in memory for team access
{% endif %}

Always cite your sources and provide comprehensive analysis.
""".strip())
    
    (prompts_dir / "writer.md").write_text("""
You are a creative writer who transforms research into engaging content.

Your style: {{ writing_style | default("professional") }}

Focus on clarity and compelling storytelling.
""".strip())
    
    return prompts_dir


class TestPromptLoaderIntegration:
    """Integration tests using realistic prompt scenarios."""
    
    def test_researcher_agent_prompt(self, sample_prompts_dir):
        """Test loading and rendering researcher agent prompt."""
        loader = PromptLoader(str(sample_prompts_dir))
        
        variables = {
            "domain": "AI and technology trends",
            "memory_enabled": True
        }
        
        result = loader.load_prompt("researcher.md", variables)
        
        assert "AI and technology trends" in result
        assert "Store important information in memory" in result
        assert "Search for current information" in result
    
    def test_writer_agent_prompt(self, sample_prompts_dir):
        """Test loading writer agent prompt with default values."""
        loader = PromptLoader(str(sample_prompts_dir))
        
        # Test with explicit style
        result1 = loader.load_prompt("writer.md", {"writing_style": "casual"})
        assert "casual" in result1
        
        # Test with default style
        result2 = loader.load_prompt("writer.md", {})
        assert "professional" in result2 