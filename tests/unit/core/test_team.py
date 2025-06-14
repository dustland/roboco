"""
Tests for the Team class.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from roboco.core.team import Team, TeamConfig, SpeakerSelectionMethod, create_team
from roboco.core.agent import Agent, AgentConfig, AgentRole
from roboco.core.brain import Message, ChatHistory


class TestTeamConfig:
    """Test TeamConfig class."""
    
    def test_team_config_defaults(self):
        """Test TeamConfig with default values."""
        config = TeamConfig(name="test_team")
        
        assert config.name == "test_team"
        assert config.max_rounds == 10
        assert config.speaker_selection == SpeakerSelectionMethod.ROUND_ROBIN
        assert config.allow_repeat_speaker is True
        assert config.enable_memory is True
        assert config.auto_save_history is True
        assert config.termination_keywords == ["TERMINATE", "EXIT", "STOP"]
    
    def test_team_config_custom_values(self):
        """Test TeamConfig with custom values."""
        config = TeamConfig(
            name="custom_team",
            max_rounds=20,
            speaker_selection=SpeakerSelectionMethod.RANDOM,
            allow_repeat_speaker=False,
            enable_memory=False,
            auto_save_history=False,
            termination_keywords=["END", "FINISH"]
        )
        
        assert config.name == "custom_team"
        assert config.max_rounds == 20
        assert config.speaker_selection == SpeakerSelectionMethod.RANDOM
        assert config.allow_repeat_speaker is False
        assert config.enable_memory is False
        assert config.auto_save_history is False
        assert config.termination_keywords == ["END", "FINISH"]
    
    def test_team_config_none_termination_keywords(self):
        """Test TeamConfig with None termination keywords (should set defaults)."""
        config = TeamConfig(name="test_team", termination_keywords=None)
        assert config.termination_keywords == ["TERMINATE", "EXIT", "STOP"]


class TestSpeakerSelectionMethod:
    """Test SpeakerSelectionMethod enum."""
    
    def test_speaker_selection_values(self):
        """Test SpeakerSelectionMethod enum values."""
        assert SpeakerSelectionMethod.ROUND_ROBIN.value == "round_robin"
        assert SpeakerSelectionMethod.RANDOM.value == "random"
        assert SpeakerSelectionMethod.LLM_BASED.value == "llm_based"
        assert SpeakerSelectionMethod.MANUAL.value == "manual"
        assert SpeakerSelectionMethod.CUSTOM.value == "custom"


class TestTeam:
    """Test Team class."""
    
    def test_team_initialization_with_config(self, mock_agents):
        """Test Team initialization with TeamConfig."""
        config = TeamConfig(name="test_team", max_rounds=5)
        team = Team(config, mock_agents)
        
        assert team.config == config
        assert team.name == "test_team"
        assert len(team.agents) == 2
        assert len(team.agent_list) == 2
        assert "agent1" in team.agents
        assert "agent2" in team.agents
        assert team.current_round == 0
        assert team.current_speaker is None
        assert team.is_active is False
        assert team._speaker_index == 0
        assert team._custom_selector is None
    
    def test_team_initialization_with_dict(self, mock_agents):
        """Test Team initialization with dictionary config."""
        config_dict = {
            "name": "dict_team",
            "max_rounds": 15,
            "speaker_selection": SpeakerSelectionMethod.RANDOM
        }
        
        team = Team(config_dict, mock_agents)
        
        assert team.name == "dict_team"
        assert team.config.max_rounds == 15
        assert team.config.speaker_selection == SpeakerSelectionMethod.RANDOM
    
    def test_team_initialization_empty_agents(self):
        """Test Team initialization with empty agents list."""
        config = TeamConfig(name="empty_team")
        
        with pytest.raises(ValueError, match="Team must have at least one agent"):
            Team(config, [])
    
    def test_team_initialization_duplicate_names(self):
        """Test Team initialization with duplicate agent names."""
        config = TeamConfig(name="duplicate_team")
        
        # Create agents with same name
        agent1 = Mock(spec=Agent)
        agent1.name = "duplicate"
        agent1.is_assistant_agent = True
        
        agent2 = Mock(spec=Agent)
        agent2.name = "duplicate"
        agent2.is_assistant_agent = True
        
        with pytest.raises(ValueError, match="Agent names must be unique"):
            Team(config, [agent1, agent2])
    
    def test_team_initialization_no_assistant_agents(self):
        """Test Team initialization with no assistant agents (should warn)."""
        config = TeamConfig(name="no_assistant_team")
        
        # Create user agents only
        user_agent = Mock(spec=Agent)
        user_agent.name = "user"
        user_agent.is_assistant_agent = False
        
        with patch('roboco.core.team.logger') as mock_logger:
            team = Team(config, [user_agent])
            mock_logger.warning.assert_called_once()
    
    def test_add_agent(self, mock_agents):
        """Test adding an agent to the team."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        # Create new agent
        new_agent = Mock(spec=Agent)
        new_agent.name = "new_agent"
        
        team.add_agent(new_agent)
        
        assert "new_agent" in team.agents
        assert new_agent in team.agent_list
        assert len(team.agents) == 3
        assert len(team.agent_list) == 3
    
    def test_add_agent_duplicate_name(self, mock_agents):
        """Test adding an agent with duplicate name."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        # Try to add agent with existing name
        duplicate_agent = Mock(spec=Agent)
        duplicate_agent.name = "agent1"  # Same as existing agent
        
        with pytest.raises(ValueError, match="Agent 'agent1' already exists in team"):
            team.add_agent(duplicate_agent)
    
    def test_remove_agent(self, mock_agents):
        """Test removing an agent from the team."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        team.remove_agent("agent1")
        
        assert "agent1" not in team.agents
        assert len(team.agents) == 1
        assert len(team.agent_list) == 1
        assert team.agent_list[0].name == "agent2"
    
    def test_remove_agent_not_found(self, mock_agents):
        """Test removing a non-existent agent."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        with pytest.raises(ValueError, match="Agent 'non_existent' not found in team"):
            team.remove_agent("non_existent")
    
    def test_get_agent(self, mock_agents):
        """Test getting an agent by name."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        agent = team.get_agent("agent1")
        assert agent is not None
        assert agent.name == "agent1"
        
        # Test non-existent agent
        agent = team.get_agent("non_existent")
        assert agent is None
    
    @pytest.mark.asyncio
    async def test_start_conversation_basic(self, mock_agents):
        """Test starting a basic conversation."""
        config = TeamConfig(name="test_team", max_rounds=2)
        team = Team(config, mock_agents)
        
        # Mock agent responses
        mock_agents[0].receive_message = AsyncMock(return_value=Message(
            content="Response from agent1", sender="agent1"
        ))
        mock_agents[1].receive_message = AsyncMock(return_value=Message(
            content="TERMINATE", sender="agent2"
        ))
        
        history = await team.start_conversation("Hello team!")
        
        assert isinstance(history, ChatHistory)
        assert not team.is_active  # Should be inactive after completion
        assert len(history.messages) >= 2  # Initial message + at least one response
    
    @pytest.mark.asyncio
    async def test_start_conversation_with_initial_speaker(self, mock_agents):
        """Test starting conversation with specified initial speaker."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        mock_agents[1].receive_message = AsyncMock(return_value=Message(
            content="TERMINATE", sender="agent2"
        ))
        
        await team.start_conversation("Hello!", initial_speaker="agent2")
        
        assert team.current_speaker.name == "agent2"
    
    @pytest.mark.asyncio
    async def test_start_conversation_invalid_initial_speaker(self, mock_agents):
        """Test starting conversation with invalid initial speaker."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        with pytest.raises(ValueError, match="Initial speaker 'invalid' not found"):
            await team.start_conversation("Hello!", initial_speaker="invalid")
    
    @pytest.mark.asyncio
    async def test_start_conversation_already_active(self, mock_agents):
        """Test starting conversation when already active."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        team.is_active = True
        
        with pytest.raises(RuntimeError, match="Team conversation is already active"):
            await team.start_conversation("Hello!")
    
    @pytest.mark.asyncio
    async def test_conversation_loop_max_rounds(self, mock_agents):
        """Test conversation loop reaching max rounds."""
        config = TeamConfig(name="test_team", max_rounds=2)
        team = Team(config, mock_agents)
        
        # Mock agents to always respond (no termination)
        mock_agents[0].receive_message = AsyncMock(return_value=Message(
            content="Response 1", sender="agent1"
        ))
        mock_agents[1].receive_message = AsyncMock(return_value=Message(
            content="Response 2", sender="agent2"
        ))
        
        await team.start_conversation("Hello!")
        
        # Should stop at max rounds
        assert team.current_round >= config.max_rounds - 1
    
    @pytest.mark.asyncio
    async def test_conversation_loop_no_response(self, mock_agents):
        """Test conversation loop when agent returns no response."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        # Mock agent to return None (no response)
        mock_agents[0].receive_message = AsyncMock(return_value=None)
        
        await team.start_conversation("Hello!")
        
        # Should end conversation when no response
        assert not team.is_active
    
    def test_select_round_robin(self, mock_agents):
        """Test round-robin speaker selection."""
        config = TeamConfig(name="test_team", speaker_selection=SpeakerSelectionMethod.ROUND_ROBIN)
        team = Team(config, mock_agents)
        
        # First selection
        speaker1 = team._select_next_speaker(None)
        assert speaker1 == mock_agents[0]
        
        # Second selection
        speaker2 = team._select_next_speaker(speaker1)
        assert speaker2 == mock_agents[1]
        
        # Third selection (should wrap around)
        speaker3 = team._select_next_speaker(speaker2)
        assert speaker3 == mock_agents[0]
    
    def test_select_round_robin_no_repeat(self, mock_agents):
        """Test round-robin speaker selection with no repeat."""
        config = TeamConfig(
            name="test_team", 
            speaker_selection=SpeakerSelectionMethod.ROUND_ROBIN,
            allow_repeat_speaker=False
        )
        team = Team(config, mock_agents)
        
        # Should skip current speaker
        current_speaker = mock_agents[0]
        next_speaker = team._select_round_robin(current_speaker)
        assert next_speaker != current_speaker
        assert next_speaker == mock_agents[1]
    
    def test_select_random(self, mock_agents):
        """Test random speaker selection."""
        config = TeamConfig(name="test_team", speaker_selection=SpeakerSelectionMethod.RANDOM)
        team = Team(config, mock_agents)
        
        with patch('random.choice', return_value=mock_agents[1]):
            speaker = team._select_random(mock_agents[0])
            assert speaker == mock_agents[1]
    
    def test_select_random_no_repeat(self, mock_agents):
        """Test random speaker selection with no repeat."""
        config = TeamConfig(
            name="test_team", 
            speaker_selection=SpeakerSelectionMethod.RANDOM,
            allow_repeat_speaker=False
        )
        team = Team(config, mock_agents)
        
        # Should exclude current speaker
        current_speaker = mock_agents[0]
        
        with patch('random.choice', return_value=mock_agents[1]):
            speaker = team._select_random(current_speaker)
            assert speaker != current_speaker
    
    def test_select_custom(self, mock_agents):
        """Test custom speaker selection."""
        config = TeamConfig(name="test_team", speaker_selection=SpeakerSelectionMethod.CUSTOM)
        team = Team(config, mock_agents)
        
        # Set custom selector
        def custom_selector(current_speaker, team):
            return mock_agents[1]
        
        team.set_custom_selector(custom_selector)
        
        speaker = team._select_custom(mock_agents[0])
        assert speaker == mock_agents[1]
    
    def test_select_custom_no_selector(self, mock_agents):
        """Test custom speaker selection without selector set."""
        config = TeamConfig(name="test_team", speaker_selection=SpeakerSelectionMethod.CUSTOM)
        team = Team(config, mock_agents)
        
        speaker = team._select_custom(mock_agents[0])
        assert speaker is None
    
    def test_should_terminate(self, mock_agents):
        """Test termination condition checking."""
        config = TeamConfig(name="test_team", termination_keywords=["STOP", "END"])
        team = Team(config, mock_agents)
        
        # Test termination message
        terminate_msg = Message(content="Let's STOP here", sender="agent1")
        assert team._should_terminate(terminate_msg) is True
        
        # Test non-termination message
        normal_msg = Message(content="Continue the conversation", sender="agent1")
        assert team._should_terminate(normal_msg) is False
        
        # Test case insensitive
        case_msg = Message(content="We should stop now", sender="agent1")
        assert team._should_terminate(case_msg) is True
    
    def test_get_chat_history(self, mock_agents):
        """Test getting chat history."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        history = team.get_chat_history()
        assert isinstance(history, ChatHistory)
        assert history == team.chat_history
    
    def test_clear_history(self, mock_agents):
        """Test clearing chat history."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        # Add a message
        team.chat_history.add_message(Message(content="test", sender="test"))
        assert len(team.chat_history.messages) == 1
        
        team.clear_history()
        assert len(team.chat_history.messages) == 0
    
    def test_get_agent_names(self, mock_agents):
        """Test getting agent names."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        names = team.get_agent_names()
        assert names == ["agent1", "agent2"]
    
    def test_get_conversation_summary(self, mock_agents):
        """Test getting conversation summary."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        # Add some messages
        team.chat_history.add_message(Message(content="Hello", sender="agent1"))
        team.chat_history.add_message(Message(content="Hi there", sender="agent2"))
        
        summary = team.get_conversation_summary()
        
        assert summary["team_name"] == "test_team"
        assert summary["total_rounds"] == team.current_round
        assert summary["total_messages"] == 2
        assert summary["participants"] == ["agent1", "agent2"]
        assert "agent1" in summary["message_counts"]
        assert "agent2" in summary["message_counts"]
        assert summary["is_active"] == team.is_active
    
    def test_reset(self, mock_agents):
        """Test resetting team state."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        # Set some state
        team.current_round = 5
        team.current_speaker = mock_agents[0]
        team.is_active = True
        team._speaker_index = 1
        team.chat_history.add_message(Message(content="test", sender="test"))
        
        team.reset()
        
        assert team.current_round == 0
        assert team.current_speaker is None
        assert team.is_active is False
        assert team._speaker_index == 0
        assert len(team.chat_history.messages) == 0
    
    def test_string_representations(self, mock_agents):
        """Test string representation methods."""
        config = TeamConfig(name="test_team")
        team = Team(config, mock_agents)
        
        str_repr = str(team)
        assert "test_team" in str_repr
        assert "2 agents" in str_repr
        
        repr_str = repr(team)
        assert "Team" in repr_str
        assert "test_team" in repr_str


class TestTeamFactoryFunction:
    """Test team factory function."""
    
    def test_create_team(self, mock_agents):
        """Test create_team factory function."""
        team = create_team(
            name="factory_team",
            agents=mock_agents,
            max_rounds=15,
            speaker_selection=SpeakerSelectionMethod.RANDOM,
            allow_repeat_speaker=False
        )
        
        assert isinstance(team, Team)
        assert team.name == "factory_team"
        assert team.config.max_rounds == 15
        assert team.config.speaker_selection == SpeakerSelectionMethod.RANDOM
        assert team.config.allow_repeat_speaker is False
        assert len(team.agents) == 2
