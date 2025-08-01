"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from persona_auto_gen.config import Config, OpenAIModel


@pytest.fixture
def mock_openai_key():
    """Provide a mock OpenAI API key."""
    return "sk-test-mock-api-key-for-testing"


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_config(mock_openai_key, temp_output_dir):
    """Create a test configuration."""
    return Config(
        openai_model=OpenAIModel.GPT_3_5_TURBO,
        openai_api_key=mock_openai_key,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 2, 1),
        data_volume={
            "contacts": 3,
            "calendar": 3,
            "sms": 3,
            "emails": 3,
            "reminders": 3,
            "notes": 3,
            "wallet": 3
        },
        enabled_apps=["contacts", "calendar", "sms", "emails", "reminders", "notes", "wallet"],
        output_directory=temp_output_dir,
        temperature=0.7,
        max_tokens=1000,
        strict_validation=False,  # Relax for testing
        max_validation_errors=50
    )


@pytest.fixture
def minimal_config(mock_openai_key, temp_output_dir):
    """Create a minimal test configuration."""
    return Config(
        openai_model=OpenAIModel.GPT_3_5_TURBO,
        openai_api_key=mock_openai_key,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 15),
        data_volume={
            "contacts": 2,
            "calendar": 2
        },
        enabled_apps=["contacts", "calendar"],
        output_directory=temp_output_dir
    )


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return {
        "age": 28,
        "occupation": "Software Developer",
        "location": "San Francisco, CA",
        "interests": ["technology", "hiking", "coffee"],
        "lifestyle": "Urban professional",
        "tech_savviness": "High"
    }


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        "Team meeting on Monday",
        "Coffee with friend",
        "Weekend hiking trip",
        "Birthday party",
        "Dentist appointment"
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM response data."""
    return {
        "contacts": {
            "contacts": [
                {
                    "id": "contact_1",
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": "John Doe",
                    "phone_numbers": [{"label": "mobile", "number": "+1234567890"}],
                    "email_addresses": [{"label": "home", "email": "john@example.com"}],
                    "addresses": [],
                    "relationship": "friend",
                    "created_date": "2024-01-15T10:00:00"
                }
            ]
        },
        "calendar": {
            "events": [
                {
                    "id": "event_1",
                    "title": "Team Meeting",
                    "description": "Weekly team sync",
                    "start_datetime": "2024-01-15T10:00:00",
                    "end_datetime": "2024-01-15T11:00:00",
                    "all_day": False,
                    "calendar_name": "Work",
                    "category": "work",
                    "created_date": "2024-01-14T09:00:00"
                }
            ]
        }
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch('persona_auto_gen.utils.llm_client.OpenAI') as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        
        # Mock chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        {
            "contacts": [
                {
                    "id": "test_contact_1",
                    "first_name": "Test",
                    "last_name": "User",
                    "display_name": "Test User",
                    "phone_numbers": [{"label": "mobile", "number": "+1234567890"}],
                    "email_addresses": [{"label": "home", "email": "test@example.com"}],
                    "addresses": [],
                    "relationship": "friend",
                    "created_date": "2024-01-15T10:00:00"
                }
            ]
        }
        """
        
        mock_instance.chat.completions.create.return_value = mock_response
        mock_instance.models.list.return_value = Mock(data=[])
        
        yield mock_instance


@pytest.fixture
def mock_validation_success():
    """Mock successful validation results."""
    return {
        "contacts": {
            "is_valid": True,
            "app_name": "contacts",
            "entry_count": 1,
            "errors": [],
            "warnings": [],
            "total_errors": 0,
            "critical_errors": 0
        }
    }


@pytest.fixture
def mock_reflection_results():
    """Mock reflection results."""
    return {
        "overall_quality": "good",
        "realism_score": 8,
        "diversity_score": 7,
        "coherence_score": 8,
        "strengths": ["Realistic names", "Consistent timing"],
        "weaknesses": ["Could use more variety"],
        "cross_app_consistency": "good",
        "temporal_consistency": "excellent",
        "character_consistency": "good",
        "recommendations": ["Add more diverse relationships"],
        "critical_issues": []
    }