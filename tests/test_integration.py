"""Integration tests for the complete Persona Auto Gen workflow."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from persona_auto_gen.main import PersonaAgent
from persona_auto_gen.config import Config, OpenAIModel


class TestIntegrationWorkflow:
    """Integration tests for the complete workflow."""
    
    @pytest.fixture
    def integration_config(self, mock_openai_key, temp_output_dir):
        """Create a minimal config for integration testing."""
        return Config(
            openai_model=OpenAIModel.GPT_3_5_TURBO,
            openai_api_key=mock_openai_key,
            data_volume={
                "contacts": 2,
                "calendar": 2
            },
            enabled_apps=["contacts", "calendar"],
            output_directory=temp_output_dir,
            strict_validation=False,
            max_validation_errors=100,
            temperature=0.1,  # Low temperature for consistency
            max_tokens=1000
        )
    
    @pytest.fixture
    def mock_generated_data(self):
        """Mock realistic generated data for testing."""
        return {
            "contacts": {
                "contacts": [
                    {
                        "id": "contact_1",
                        "first_name": "Alice",
                        "last_name": "Johnson",
                        "display_name": "Alice Johnson",
                        "phone_numbers": [{"label": "mobile", "number": "+1555123456"}],
                        "email_addresses": [{"label": "work", "email": "alice@company.com"}],
                        "addresses": [],
                        "relationship": "colleague",
                        "created_date": "2024-01-15T09:30:00"
                    },
                    {
                        "id": "contact_2",
                        "first_name": "Bob",
                        "last_name": "Smith",
                        "display_name": "Bob Smith",
                        "phone_numbers": [{"label": "mobile", "number": "+1555987654"}],
                        "email_addresses": [{"label": "home", "email": "bob@email.com"}],
                        "addresses": [],
                        "relationship": "friend",
                        "created_date": "2024-01-10T14:20:00"
                    }
                ]
            },
            "calendar": {
                "events": [
                    {
                        "id": "event_1",
                        "title": "Team Meeting",
                        "description": "Weekly team sync meeting",
                        "start_datetime": "2024-01-15T10:00:00",
                        "end_datetime": "2024-01-15T11:00:00",
                        "all_day": False,
                        "calendar_name": "Work",
                        "category": "work",
                        "created_date": "2024-01-14T16:00:00"
                    },
                    {
                        "id": "event_2",
                        "title": "Coffee with Bob",
                        "description": "Catching up over coffee",
                        "start_datetime": "2024-01-16T15:00:00",
                        "end_datetime": "2024-01-16T16:00:00",
                        "all_day": False,
                        "calendar_name": "Personal",
                        "category": "social",
                        "created_date": "2024-01-15T12:00:00"
                    }
                ]
            }
        }
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_end_to_end_workflow(self, mock_openai_class, integration_config, 
                                 sample_user_profile, sample_events, mock_generated_data):
        """Test the complete end-to-end workflow."""
        
        # Mock OpenAI client responses
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock different responses for different calls
        def mock_create_response(*args, **kwargs):
            mock_response = Mock()
            mock_choice = Mock()
            
            # Determine response based on the prompt content
            messages = kwargs.get('messages', [])
            if messages and len(messages) > 1:
                user_content = messages[1].get('content', '').lower()
                
                if 'analyze' in user_content or 'profile' in user_content:
                    # Profile analysis response
                    mock_choice.message.content = json.dumps({
                        "user_characteristics": {
                            "lifestyle": "professional urban lifestyle",
                            "communication_patterns": "frequent digital communication",
                            "technology_usage": "high tech adoption",
                            "social_connections": "maintains diverse professional and personal networks"
                        },
                        "event_analysis": {
                            "event_types": ["work", "social", "personal"],
                            "recurring_patterns": ["weekly meetings", "regular social activities"],
                            "social_implications": ["strong professional network", "active social life"]
                        },
                        "app_usage_patterns": {
                            "contacts": "well-organized contact management",
                            "calendar": "structured scheduling with work-life balance"
                        },
                        "data_relationships": {
                            "cross_app_connections": "contacts should align with calendar events"
                        }
                    })
                
                elif 'contacts' in user_content:
                    # Contacts generation response
                    mock_choice.message.content = json.dumps(mock_generated_data["contacts"])
                
                elif 'calendar' in user_content or 'events' in user_content:
                    # Calendar generation response
                    mock_choice.message.content = json.dumps(mock_generated_data["calendar"])
                
                elif 'evaluate' in user_content or 'quality' in user_content:
                    # Reflection response
                    mock_choice.message.content = json.dumps({
                        "overall_quality": "good",
                        "realism_score": 8,
                        "diversity_score": 7,
                        "coherence_score": 8,
                        "strengths": [
                            "Realistic contact names and relationships",
                            "Logical calendar event scheduling",
                            "Good cross-app consistency"
                        ],
                        "weaknesses": [
                            "Could include more diverse event types",
                            "Limited geographic variety in contacts"
                        ],
                        "cross_app_consistency": "good",
                        "temporal_consistency": "excellent",
                        "character_consistency": "good",
                        "recommendations": [
                            "Add more variety in contact locations",
                            "Include recurring calendar events"
                        ],
                        "critical_issues": []
                    })
                
                else:
                    # Default response
                    mock_choice.message.content = json.dumps({"status": "ok"})
            
            mock_response.choices = [mock_choice]
            return mock_response
        
        mock_client.chat.completions.create.side_effect = mock_create_response
        mock_client.models.list.return_value = Mock(data=[])
        
        # Create agent and run generation
        agent = PersonaAgent(integration_config)
        result = agent.generate(sample_user_profile, sample_events)
        
        # Verify successful completion
        assert result["success"] is True
        assert "output_path" in result
        assert result["output_path"] != ""
        
        # Verify output directory exists
        output_path = Path(result["output_path"])
        assert output_path.exists()
        assert output_path.is_dir()
        
        # Verify generated data structure
        assert "generated_data" in result
        generated_data = result["generated_data"]
        assert "contacts" in generated_data
        assert "calendar" in generated_data
        
        # Verify file outputs
        assert (output_path / "contacts.json").exists()
        assert (output_path / "calendar.json").exists()
        assert (output_path / "validation_report.json").exists()
        assert (output_path / "reflection_report.json").exists()
        assert (output_path / "README.md").exists()
        
        # Verify file contents
        with open(output_path / "contacts.json", 'r') as f:
            contacts_data = json.load(f)
            assert "contacts" in contacts_data
            assert len(contacts_data["contacts"]) > 0
        
        with open(output_path / "calendar.json", 'r') as f:
            calendar_data = json.load(f)
            assert "events" in calendar_data
            assert len(calendar_data["events"]) > 0
        
        # Verify validation results
        assert "validation_results" in result
        validation_results = result["validation_results"]
        assert isinstance(validation_results, dict)
        
        # Verify reflection results
        assert "reflection_results" in result
        reflection_results = result["reflection_results"]
        assert isinstance(reflection_results, dict)
        assert "overall_quality" in reflection_results
    
    def test_workflow_with_validation_errors(self, integration_config, 
                                           sample_user_profile, sample_events):
        """Test workflow handling when validation errors occur."""
        
        # Create agent
        agent = PersonaAgent(integration_config)
        
        # Mock the workflow to return data with validation errors
        with patch.object(agent.workflow, 'run') as mock_run:
            mock_run.return_value = {
                "success": True,
                "output_path": str(integration_config.output_directory / "test_profile"),
                "generated_data": {"contacts": {"contacts": []}},
                "validation_results": {
                    "contacts": {
                        "is_valid": False,
                        "total_errors": 3,
                        "critical_errors": 1,
                        "errors": ["Required field missing", "Invalid format", "Type error"]
                    }
                },
                "reflection_results": {
                    "overall_quality": "fair",
                    "critical_issues": ["Schema validation failures"]
                },
                "errors": []
            }
            
            result = agent.generate(sample_user_profile, sample_events)
            
            assert result["success"] is True  # Should still succeed
            assert "validation_results" in result
            assert not result["validation_results"]["contacts"]["is_valid"]
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_workflow_resilience_to_llm_failures(self, mock_openai_class, 
                                                integration_config, sample_user_profile, sample_events):
        """Test workflow resilience when LLM calls fail."""
        
        # Mock OpenAI client to fail initially then succeed
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        call_count = 0
        def mock_create_with_failures(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:  # First two calls fail
                from openai import APIError
                raise APIError("API temporarily unavailable", response=Mock(), body=None)
            else:  # Subsequent calls succeed
                mock_response = Mock()
                mock_choice = Mock()
                mock_choice.message.content = json.dumps({
                    "contacts": [
                        {
                            "id": "fallback_contact",
                            "first_name": "Test",
                            "last_name": "User",
                            "display_name": "Test User",
                            "relationship": "friend",
                            "created_date": "2024-01-15T10:00:00"
                        }
                    ]
                })
                mock_response.choices = [mock_choice]
                return mock_response
        
        mock_client.chat.completions.create.side_effect = mock_create_with_failures
        
        # Create agent and run generation
        agent = PersonaAgent(integration_config)
        
        with patch('time.sleep'):  # Speed up retries
            result = agent.generate(sample_user_profile, sample_events)
        
        # Should eventually succeed with fallback data
        assert result["success"] is True or len(result.get("errors", [])) > 0
    
    def test_minimal_valid_workflow(self, integration_config, sample_user_profile, sample_events):
        """Test the minimal valid workflow configuration."""
        
        # Configure for minimal generation
        integration_config.data_volume = {"contacts": 1}
        integration_config.enabled_apps = ["contacts"]
        integration_config.use_faker_fallback = True
        
        agent = PersonaAgent(integration_config)
        
        # Mock just the LLM client to fail so we get fallback data
        with patch('persona_auto_gen.utils.llm_client.LLMClient.generate', side_effect=Exception("Mock failure")):
            result = agent.generate(sample_user_profile, sample_events)
            
            # Should succeed with fallback data
            assert result["success"] is True
            assert "contacts" in result["generated_data"]
            
            # Verify fallback data was generated
            contacts = result["generated_data"]["contacts"].get("contacts", [])
            assert len(contacts) > 0
    
    async def test_async_workflow(self, integration_config, sample_user_profile, sample_events):
        """Test the async workflow."""
        
        agent = PersonaAgent(integration_config)
        
        # Mock the async workflow
        with patch.object(agent.workflow, 'arun') as mock_arun:
            mock_arun.return_value = {
                "success": True,
                "output_path": str(integration_config.output_directory / "async_test"),
                "generated_data": {"contacts": {"contacts": []}},
                "validation_results": {},
                "reflection_results": {},
                "errors": []
            }
            
            result = await agent.agenerate(sample_user_profile, sample_events)
            
            assert result["success"] is True
            mock_arun.assert_called_once()
    
    def test_configuration_edge_cases(self, mock_openai_key, temp_output_dir):
        """Test edge cases in configuration."""
        
        # Test with maximum data volumes
        config = Config(
            openai_api_key=mock_openai_key,
            data_volume={app: 1 for app in ["contacts", "calendar", "sms", "emails", "reminders", "notes", "wallet"]},
            enabled_apps=["contacts", "calendar", "sms", "emails", "reminders", "notes", "wallet"],
            output_directory=temp_output_dir,
            strict_validation=True,
            max_validation_errors=0  # Very strict
        )
        
        agent = PersonaAgent(config)
        assert agent.config.max_validation_errors == 0
        
        # Test with minimal configuration
        minimal_config = Config(
            openai_api_key=mock_openai_key,
            data_volume={"contacts": 1},
            enabled_apps=["contacts"],
            output_directory=temp_output_dir
        )
        
        minimal_agent = PersonaAgent(minimal_config)
        assert len(minimal_agent.config.enabled_apps) == 1
    
    def test_error_accumulation(self, integration_config, sample_user_profile, sample_events):
        """Test that errors are properly accumulated throughout the workflow."""
        
        agent = PersonaAgent(integration_config)
        
        # Mock workflow to return multiple errors
        with patch.object(agent.workflow, 'run') as mock_run:
            mock_run.return_value = {
                "success": False,
                "error": "Multiple failures occurred",
                "output_path": "",
                "generated_data": {},
                "validation_results": {},
                "reflection_results": {},
                "errors": [
                    "Profile analysis failed",
                    "Data generation failed for contacts",
                    "Schema validation failed",
                    "Reflection analysis failed"
                ]
            }
            
            result = agent.generate(sample_user_profile, sample_events)
            
            assert result["success"] is False
            assert len(result["errors"]) >= 4
            assert "Profile analysis failed" in result["errors"]
            assert "Data generation failed for contacts" in result["errors"]