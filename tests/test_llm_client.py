"""Tests for LLM client functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from persona_auto_gen.utils.llm_client import LLMClient
from persona_auto_gen.config import Config, OpenAIModel


class TestLLMClient:
    """Test the LLMClient class."""
    
    def test_llm_client_creation(self, test_config):
        """Test creating LLM client."""
        client = LLMClient(test_config)
        
        assert client.config == test_config
        assert client._min_request_interval == 1.0
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_generate_success(self, mock_openai_class, test_config):
        """Test successful text generation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Generated content"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create client and generate
        llm_client = LLMClient(test_config)
        result = llm_client.generate("Test prompt")
        
        assert result == "Generated content"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_generate_with_custom_params(self, mock_openai_class, test_config):
        """Test generation with custom parameters."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = "Generated content"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create client and generate with custom params
        llm_client = LLMClient(test_config)
        result = llm_client.generate(
            "Test prompt", 
            temperature=0.5, 
            max_tokens=2000
        )
        
        assert result == "Generated content"
        
        # Check that custom parameters were used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['temperature'] == 0.5
        assert call_args[1]['max_tokens'] == 2000
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_generate_empty_response(self, mock_openai_class, test_config):
        """Test handling empty response."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock empty response
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message.content = None
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create client and test
        llm_client = LLMClient(test_config)
        
        with pytest.raises(ValueError, match="Empty response from OpenAI"):
            llm_client.generate("Test prompt")
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_generate_rate_limit_retry(self, mock_openai_class, test_config):
        """Test handling rate limit with retry."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock rate limit error then success
        from openai import RateLimitError
        mock_client.chat.completions.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=Mock(), body=None),
            Mock(choices=[Mock(message=Mock(content="Success after retry"))])
        ]
        
        # Create client and generate
        llm_client = LLMClient(test_config)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm_client.generate("Test prompt", max_retries=2)
        
        assert result == "Success after retry"
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_generate_api_error_retry(self, mock_openai_class, test_config):
        """Test handling API error with retry."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock API error then success
        from openai import APIError
        mock_client.chat.completions.create.side_effect = [
            APIError("API error", response=Mock(), body=None),
            Mock(choices=[Mock(message=Mock(content="Success after retry"))])
        ]
        
        # Create client and generate
        llm_client = LLMClient(test_config)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = llm_client.generate("Test prompt", max_retries=2)
        
        assert result == "Success after retry"
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_generate_max_retries_exceeded(self, mock_openai_class, test_config):
        """Test max retries exceeded."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock consistent API errors
        from openai import APIError
        mock_client.chat.completions.create.side_effect = APIError("Persistent error", response=Mock(), body=None)
        
        # Create client and test
        llm_client = LLMClient(test_config)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with pytest.raises(APIError):
                llm_client.generate("Test prompt", max_retries=2)
        
        assert mock_client.chat.completions.create.call_count == 2
    
    def test_rate_limiting(self, test_config):
        """Test rate limiting functionality."""
        llm_client = LLMClient(test_config)
        
        # Set last request time to now
        llm_client._last_request_time = time.time()
        
        # Mock sleep to verify it's called
        with patch('time.sleep') as mock_sleep:
            llm_client._enforce_rate_limit()
            mock_sleep.assert_called_once()
    
    def test_estimate_tokens(self, test_config):
        """Test token estimation."""
        llm_client = LLMClient(test_config)
        
        tokens = llm_client.estimate_tokens("This is a test string")
        
        assert isinstance(tokens, int)
        assert tokens > 0
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_validate_api_key_success(self, mock_openai_class, test_config):
        """Test successful API key validation."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create client and validate
        llm_client = LLMClient(test_config)
        result = llm_client.validate_api_key()
        
        assert result is True
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_validate_api_key_failure(self, mock_openai_class, test_config):
        """Test API key validation failure."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock error response
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
        
        # Create client and validate
        llm_client = LLMClient(test_config)
        result = llm_client.validate_api_key()
        
        assert result is False
    
    @patch('persona_auto_gen.utils.llm_client.OpenAI')
    def test_get_model_info(self, mock_openai_class, test_config):
        """Test getting model information."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock models list response
        mock_model = Mock()
        mock_model.id = test_config.openai_model.value
        mock_model.object = "model"
        mock_model.created = 1234567890
        mock_model.owned_by = "openai"
        
        mock_models_response = Mock()
        mock_models_response.data = [mock_model]
        mock_client.models.list.return_value = mock_models_response
        
        # Create client and get info
        llm_client = LLMClient(test_config)
        info = llm_client.get_model_info()
        
        assert info["id"] == test_config.openai_model.value
        assert info["object"] == "model"
        assert info["created"] == 1234567890
        assert info["owned_by"] == "openai"
    
    def test_generate_batch(self, test_config):
        """Test batch generation."""
        llm_client = LLMClient(test_config)
        
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        
        # Mock the generate method
        with patch.object(llm_client, 'generate', side_effect=["Response 1", "Response 2", "Response 3"]):
            results = llm_client.generate_batch(prompts)
            
            assert len(results) == 3
            assert results[0] == "Response 1"
            assert results[1] == "Response 2"
            assert results[2] == "Response 3"
    
    def test_generate_batch_with_failure(self, test_config):
        """Test batch generation with some failures."""
        llm_client = LLMClient(test_config)
        
        prompts = ["Prompt 1", "Prompt 2"]
        
        # Mock the generate method with one failure
        def mock_generate(prompt):
            if prompt == "Prompt 1":
                return "Response 1"
            else:
                raise Exception("Generation failed")
        
        with patch.object(llm_client, 'generate', side_effect=mock_generate):
            results = llm_client.generate_batch(prompts)
            
            assert len(results) == 2
            assert results[0] == "Response 1"
            assert results[1] == ""  # Empty string for failed generation
    
    def test_count_tokens_in_messages(self, test_config):
        """Test counting tokens in messages."""
        llm_client = LLMClient(test_config)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Generate some data"}
        ]
        
        token_count = llm_client.count_tokens_in_messages(messages)
        
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_create_system_message(self, test_config):
        """Test creating system messages for different apps."""
        llm_client = LLMClient(test_config)
        
        contacts_msg = llm_client.create_system_message("contacts")
        calendar_msg = llm_client.create_system_message("calendar")
        unknown_msg = llm_client.create_system_message("unknown_app")
        
        assert "contacts" in contacts_msg.lower()
        assert "calendar" in calendar_msg.lower()
        assert "helpful assistant" in unknown_msg
        
        # All should be different (except unknown fallback)
        assert contacts_msg != calendar_msg