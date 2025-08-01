"""Tests for configuration management."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from persona_auto_gen.config import Config, OpenAIModel, AppType


class TestConfig:
    """Test the Config class."""
    
    def test_default_config_creation(self, mock_openai_key):
        """Test creating config with defaults."""
        config = Config(openai_api_key=mock_openai_key)
        
        assert config.openai_api_key == mock_openai_key
        assert config.openai_model == OpenAIModel.GPT_4O
        assert config.temperature == 0.7
        assert config.max_tokens == 4000
        assert isinstance(config.start_date, datetime)
        assert isinstance(config.end_date, datetime)
        assert config.start_date < config.end_date
    
    def test_custom_config_creation(self, mock_openai_key):
        """Test creating config with custom values."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        config = Config(
            openai_api_key=mock_openai_key,
            openai_model=OpenAIModel.GPT_4,
            start_date=start_date,
            end_date=end_date,
            temperature=0.5,
            max_tokens=2000
        )
        
        assert config.openai_model == OpenAIModel.GPT_4
        assert config.start_date == start_date
        assert config.end_date == end_date
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
    
    def test_config_validation_missing_api_key(self):
        """Test config validation with missing API key."""
        with pytest.raises(ValueError, match="OpenAI API key must be provided"):
            Config()
    
    def test_config_validation_invalid_date_range(self, mock_openai_key):
        """Test config validation with invalid date range."""
        start_date = datetime(2024, 12, 31)
        end_date = datetime(2024, 1, 1)
        
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            Config(
                openai_api_key=mock_openai_key,
                start_date=start_date,
                end_date=end_date
            )
    
    def test_config_validation_invalid_apps(self, mock_openai_key):
        """Test config validation with invalid apps."""
        with pytest.raises(ValueError, match="Invalid apps specified"):
            Config(
                openai_api_key=mock_openai_key,
                enabled_apps=["invalid_app", "another_invalid"]
            )
    
    def test_config_from_dict(self, mock_openai_key):
        """Test creating config from dictionary."""
        config_dict = {
            "openai_api_key": mock_openai_key,
            "openai_model": "gpt-4",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
            "temperature": 0.8,
            "output_directory": "/tmp/test"
        }
        
        config = Config.from_dict(config_dict)
        
        assert config.openai_api_key == mock_openai_key
        assert config.openai_model == OpenAIModel.GPT_4
        assert config.temperature == 0.8
        assert config.output_directory == Path("/tmp/test")
    
    def test_config_to_dict(self, test_config):
        """Test converting config to dictionary."""
        config_dict = test_config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "openai_api_key" in config_dict
        assert "openai_model" in config_dict
        assert isinstance(config_dict["start_date"], str)
        assert isinstance(config_dict["end_date"], str)
        assert isinstance(config_dict["output_directory"], str)
    
    def test_get_schema_path(self, test_config):
        """Test getting schema path."""
        schema_path = test_config.get_schema_path("contacts")
        
        assert isinstance(schema_path, Path)
        assert schema_path.name == "contacts.json"
        assert "schemas" in str(schema_path)
    
    def test_get_output_path(self, test_config):
        """Test getting output path."""
        output_path = test_config.get_output_path("test_profile")
        
        assert isinstance(output_path, Path)
        assert output_path.name == "test_profile"
        assert test_config.output_directory in output_path.parents
    
    def test_get_output_path_auto_generate(self, test_config):
        """Test getting output path with auto-generated ID."""
        output_path = test_config.get_output_path()
        
        assert isinstance(output_path, Path)
        assert "user_profile_" in output_path.name
    
    def test_validate_configuration(self, test_config):
        """Test configuration validation."""
        issues = test_config.validate_configuration()
        
        assert isinstance(issues, list)
        # Some issues expected due to missing schema files in test environment
    
    def test_get_time_range_days(self, test_config):
        """Test getting time range in days."""
        days = test_config.get_time_range_days()
        
        assert isinstance(days, int)
        assert days > 0
    
    def test_is_app_enabled(self, test_config):
        """Test checking if app is enabled."""
        assert test_config.is_app_enabled("contacts") == True
        assert test_config.is_app_enabled("nonexistent") == False
    
    def test_get_app_data_count(self, test_config):
        """Test getting app data count."""
        count = test_config.get_app_data_count("contacts")
        
        assert isinstance(count, int)
        assert count >= 0
        
        # Test non-existent app
        assert test_config.get_app_data_count("nonexistent") == 0


class TestEnums:
    """Test enum classes."""
    
    def test_openai_model_enum(self):
        """Test OpenAI model enum."""
        assert OpenAIModel.GPT_4.value == "gpt-4"
        assert OpenAIModel.GPT_4O.value == "gpt-4o"
        assert OpenAIModel.GPT_3_5_TURBO.value == "gpt-3.5-turbo"
    
    def test_app_type_enum(self):
        """Test app type enum."""
        assert AppType.CONTACTS.value == "contacts"
        assert AppType.CALENDAR.value == "calendar"
        assert AppType.SMS.value == "sms"
        assert AppType.EMAILS.value == "emails"
        assert AppType.REMINDERS.value == "reminders"
        assert AppType.NOTES.value == "notes"
        assert AppType.WALLET.value == "wallet"