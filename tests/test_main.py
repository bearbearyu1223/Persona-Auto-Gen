"""Tests for main PersonaAgent functionality."""

import pytest
pytestmark = pytest.mark.asyncio

from unittest.mock import Mock, patch

from persona_auto_gen.main import PersonaAgent
from persona_auto_gen.config import Config


class TestPersonaAgent:
    """Test the main PersonaAgent class."""
    
    def test_persona_agent_creation(self, test_config):
        """Test creating PersonaAgent."""
        agent = PersonaAgent(test_config)
        
        assert agent.config == test_config
        assert agent.workflow is not None
    
    def test_persona_agent_default_config(self, mock_openai_key):
        """Test creating PersonaAgent with default config."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': mock_openai_key}):
            agent = PersonaAgent()
            
            assert agent.config is not None
            assert agent.config.openai_api_key == mock_openai_key
    
    def test_validate_inputs_success(self, test_config, sample_user_profile, sample_events):
        """Test successful input validation."""
        agent = PersonaAgent(test_config)
        
        # Should not raise any exception
        agent._validate_inputs(sample_user_profile, sample_events)
    
    def test_validate_inputs_invalid_user_profile(self, test_config, sample_events):
        """Test input validation with invalid user profile."""
        agent = PersonaAgent(test_config)
        
        # Test non-dict user profile
        with pytest.raises(ValueError, match="user_profile must be a dictionary"):
            agent._validate_inputs("not a dict", sample_events)
        
        # Test empty user profile
        with pytest.raises(ValueError, match="user_profile cannot be empty"):
            agent._validate_inputs({}, sample_events)
    
    def test_validate_inputs_invalid_events(self, test_config, sample_user_profile):
        """Test input validation with invalid events."""
        agent = PersonaAgent(test_config)
        
        # Test non-list events
        with pytest.raises(ValueError, match="events must be a list"):
            agent._validate_inputs(sample_user_profile, "not a list")
        
        # Test empty events
        with pytest.raises(ValueError, match="events list cannot be empty"):
            agent._validate_inputs(sample_user_profile, [])
        
        # Test non-string events
        with pytest.raises(ValueError, match="Event .* must be a string"):
            agent._validate_inputs(sample_user_profile, ["valid event", 123])
        
        # Test empty string events
        with pytest.raises(ValueError, match="Event .* cannot be empty"):
            agent._validate_inputs(sample_user_profile, ["valid event", ""])
    
    def test_get_config_info(self, test_config):
        """Test getting config information."""
        agent = PersonaAgent(test_config)
        
        config_info = agent.get_config_info()
        
        assert isinstance(config_info, dict)
        assert "model" in config_info
        assert "enabled_apps" in config_info
        assert "data_volume" in config_info
        assert "time_range" in config_info
        assert "output_directory" in config_info
        assert "validation_settings" in config_info
        
        # Check time range info
        time_range = config_info["time_range"]
        assert "start" in time_range
        assert "end" in time_range
        assert "days" in time_range
        assert isinstance(time_range["days"], int)
    
    def test_validate_configuration(self, test_config):
        """Test configuration validation."""
        agent = PersonaAgent(test_config)
        
        issues = agent.validate_configuration()
        
        assert isinstance(issues, list)
        # May have issues due to missing schema files in test environment
    
    @patch('persona_auto_gen.agents.workflow.PersonaWorkflow.run')
    def test_generate_success(self, mock_workflow_run, test_config, sample_user_profile, sample_events):
        """Test successful data generation."""
        # Mock successful workflow result
        mock_workflow_run.return_value = {
            "success": True,
            "output_path": "/test/output/path",
            "generated_data": {"contacts": {"contacts": []}},
            "validation_results": {"contacts": {"is_valid": True}},
            "reflection_results": {"overall_quality": "good"},
            "errors": []
        }
        
        agent = PersonaAgent(test_config)
        result = agent.generate(sample_user_profile, sample_events)
        
        assert result["success"] is True
        assert "output_path" in result
        assert "generated_data" in result
        assert "validation_results" in result
        assert "reflection_results" in result
        
        # Check that workflow was called with correct parameters
        mock_workflow_run.assert_called_once()
        call_args = mock_workflow_run.call_args[0]
        assert call_args[0] == sample_user_profile
        assert call_args[1] == sample_events
    
    @patch('persona_auto_gen.agents.workflow.PersonaWorkflow.run')
    def test_generate_workflow_failure(self, mock_workflow_run, test_config, sample_user_profile, sample_events):
        """Test generation with workflow failure."""
        # Mock workflow failure
        mock_workflow_run.return_value = {
            "success": False,
            "error": "Workflow failed",
            "output_path": "",
            "generated_data": {},
            "validation_results": {},
            "reflection_results": {},
            "errors": ["Workflow failed"]
        }
        
        agent = PersonaAgent(test_config)
        result = agent.generate(sample_user_profile, sample_events)
        
        assert result["success"] is False
        assert result["error"] == "Workflow failed"
        assert len(result["errors"]) > 0
    
    @patch('persona_auto_gen.agents.workflow.PersonaWorkflow.run')
    def test_generate_exception(self, mock_workflow_run, test_config, sample_user_profile, sample_events):
        """Test generation with unexpected exception."""
        # Mock workflow exception
        mock_workflow_run.side_effect = Exception("Unexpected error")
        
        agent = PersonaAgent(test_config)
        result = agent.generate(sample_user_profile, sample_events)
        
        assert result["success"] is False
        assert "Unexpected error" in result["error"]
        assert len(result["errors"]) > 0
    
    @patch('persona_auto_gen.agents.workflow.PersonaWorkflow.arun')
    async def test_agenerate_success(self, mock_workflow_arun, test_config, sample_user_profile, sample_events):
        """Test successful async data generation."""
        # Mock successful async workflow result
        mock_workflow_arun.return_value = {
            "success": True,
            "output_path": "/test/output/path",
            "generated_data": {"contacts": {"contacts": []}},
            "validation_results": {"contacts": {"is_valid": True}},
            "reflection_results": {"overall_quality": "good"},
            "errors": []
        }
        
        agent = PersonaAgent(test_config)
        result = await agent.agenerate(sample_user_profile, sample_events)
        
        assert result["success"] is True
        assert "output_path" in result
        
        # Check that async workflow was called
        mock_workflow_arun.assert_called_once()
    
    @patch('persona_auto_gen.agents.workflow.PersonaWorkflow.arun')
    async def test_agenerate_exception(self, mock_workflow_arun, test_config, sample_user_profile, sample_events):
        """Test async generation with exception."""
        # Mock async workflow exception
        mock_workflow_arun.side_effect = Exception("Async error")
        
        agent = PersonaAgent(test_config)
        result = await agent.agenerate(sample_user_profile, sample_events)
        
        assert result["success"] is False
        assert "Async error" in result["error"]


class TestExampleFunctions:
    """Test example creation functions."""
    
    def test_create_example_config(self):
        """Test creating example config."""
        from persona_auto_gen.main import create_example_config
        
        config = create_example_config()
        
        assert isinstance(config, Config)
        assert config.openai_model is not None
        assert config.data_volume is not None
        assert len(config.data_volume) > 0
    
    def test_create_example_user_profile(self):
        """Test creating example user profile."""
        from persona_auto_gen.main import create_example_user_profile
        
        profile = create_example_user_profile()
        
        assert isinstance(profile, dict)
        assert "age" in profile
        assert "occupation" in profile
        assert "location" in profile
        assert "interests" in profile
    
    def test_create_example_events(self):
        """Test creating example events."""
        from persona_auto_gen.main import create_example_events
        
        events = create_example_events()
        
        assert isinstance(events, list)
        assert len(events) > 0
        assert all(isinstance(event, str) for event in events)
        assert all(len(event.strip()) > 0 for event in events)


class TestMainFunction:
    """Test the main function."""
    
    @patch('persona_auto_gen.main.PersonaAgent')
    @patch('persona_auto_gen.main.create_example_config')
    @patch('persona_auto_gen.main.create_example_user_profile')
    @patch('persona_auto_gen.main.create_example_events')
    def test_main_success(self, mock_events, mock_profile, mock_config, mock_agent_class):
        """Test successful main function execution."""
        from persona_auto_gen.main import main
        
        # Mock all dependencies
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        mock_profile.return_value = {"age": 28}
        mock_events.return_value = ["Event 1", "Event 2"]
        
        # Mock agent
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get_config_info.return_value = {
            "model": "gpt-4",
            "enabled_apps": ["contacts"],
            "data_volume": {"contacts": 10},
            "time_range": {"days": 30},
            "output_directory": "/tmp",
            "validation_settings": {}
        }
        mock_agent.generate.return_value = {
            "success": True,
            "output_path": "/test/output",
            "generated_data": {"contacts": {"contacts": []}},
            "reflection_results": {
                "overall_quality": "good",
                "realism_score": 8,
                "diversity_score": 7,
                "coherence_score": 8
            }
        }
        
        # Test main function (should not raise)
        try:
            main()
        except SystemExit as e:
            # Main function calls sys.exit(1) on failure, sys.exit(0) on success
            assert e.code == 0 or e.code is None
    
    @patch('persona_auto_gen.main.PersonaAgent')
    @patch('persona_auto_gen.main.create_example_config')
    def test_main_generation_failure(self, mock_config, mock_agent_class):
        """Test main function with generation failure."""
        from persona_auto_gen.main import main
        
        # Mock config
        mock_config_instance = Mock()
        mock_config.return_value = mock_config_instance
        
        # Mock agent with failure
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_agent.get_config_info.return_value = {}
        mock_agent.generate.return_value = {
            "success": False,
            "error": "Generation failed",
            "errors": ["Error 1", "Error 2"]
        }
        
        # Test main function
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1
    
    @patch('persona_auto_gen.main.create_example_config')
    def test_main_keyboard_interrupt(self, mock_config):
        """Test main function with keyboard interrupt."""
        from persona_auto_gen.main import main
        
        # Mock config to raise KeyboardInterrupt
        mock_config.side_effect = KeyboardInterrupt()
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
    
    @patch('persona_auto_gen.main.create_example_config')
    def test_main_unexpected_exception(self, mock_config):
        """Test main function with unexpected exception."""
        from persona_auto_gen.main import main
        
        # Mock config to raise unexpected exception
        mock_config.side_effect = Exception("Unexpected error")
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1