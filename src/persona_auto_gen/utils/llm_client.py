"""LLM client for OpenAI API interactions."""

import logging
import time
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI

from ..config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with OpenAI's API."""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum seconds between requests
        
    def generate(self, prompt: str, temperature: Optional[float] = None, 
                max_tokens: Optional[int] = None, 
                max_retries: int = 3) -> str:
        """Generate text using the configured OpenAI model."""
        
        # Use config defaults if not specified
        if temperature is None:
            temperature = self.config.temperature
        if max_tokens is None:
            max_tokens = self.config.max_tokens
            
        # Rate limiting
        self._enforce_rate_limit()
        
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates realistic synthetic data for iPhone apps. Always respond with valid JSON when requested."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Making OpenAI API call (attempt {attempt + 1}/{max_retries})")
                
                response = self.client.chat.completions.create(
                    model=self.config.openai_model.value,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=60.0
                )
                
                content = response.choices[0].message.content
                
                if not content:
                    raise ValueError("Empty response from OpenAI")
                
                logger.debug(f"OpenAI API call successful, {len(content)} characters returned")
                return content
                
            except openai.RateLimitError as e:
                wait_time = (2 ** attempt) * 60  # Exponential backoff in minutes
                logger.warning(f"Rate limit exceeded (attempt {attempt + 1}), waiting {wait_time} seconds")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    raise e
                    
            except openai.APIError as e:
                logger.error(f"OpenAI API error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise e
                    
            except Exception as e:
                logger.error(f"Unexpected error during OpenAI API call (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise e
        
        raise RuntimeError(f"Failed to generate content after {max_retries} attempts")
    
    async def agenerate(self, prompt: str, temperature: Optional[float] = None,
                       max_tokens: Optional[int] = None,
                       max_retries: int = 3) -> str:
        """Asynchronously generate text using the configured OpenAI model."""
        
        # Use config defaults if not specified
        if temperature is None:
            temperature = self.config.temperature
        if max_tokens is None:
            max_tokens = self.config.max_tokens
            
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates realistic synthetic data for iPhone apps. Always respond with valid JSON when requested."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Note: Using sync client in async method for simplicity
        # In production, you might want to use an async OpenAI client
        return self.generate(prompt, temperature, max_tokens, max_retries)
    
    def generate_batch(self, prompts: List[str], temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None) -> List[str]:
        """Generate responses for multiple prompts."""
        responses = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"Processing batch request {i + 1}/{len(prompts)}")
            
            try:
                response = self.generate(prompt, temperature, max_tokens)
                responses.append(response)
                
            except Exception as e:
                logger.error(f"Failed to process batch request {i + 1}: {str(e)}")
                responses.append("")  # Empty response for failed requests
        
        return responses
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting between API calls."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count for a text string."""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """Validate that the API key is working."""
        try:
            # Make a simple API call to test the key
            response = self.client.chat.completions.create(
                model=self.config.openai_model.value,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
                timeout=10.0
            )
            
            logger.info("OpenAI API key validation successful")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {str(e)}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the configured model."""
        try:
            # Try to get model information
            models = self.client.models.list()
            
            for model in models.data:
                if model.id == self.config.openai_model.value:
                    return {
                        "id": model.id,
                        "object": model.object,
                        "created": model.created,
                        "owned_by": model.owned_by
                    }
            
            # If model not found in list, return basic info
            return {
                "id": self.config.openai_model.value,
                "status": "configured",
                "note": "Model details not available"
            }
            
        except Exception as e:
            logger.warning(f"Could not retrieve model info: {str(e)}")
            return {
                "id": self.config.openai_model.value,
                "status": "unknown",
                "error": str(e)
            }
    
    def count_tokens_in_messages(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for a list of messages."""
        total_tokens = 0
        
        for message in messages:
            # Add tokens for role and content
            total_tokens += self.estimate_tokens(message.get("role", ""))
            total_tokens += self.estimate_tokens(message.get("content", ""))
            # Add some overhead for message formatting
            total_tokens += 10
        
        return total_tokens
    
    def create_system_message(self, app_name: str) -> str:
        """Create a system message tailored for a specific app."""
        system_messages = {
            "contacts": "You are an expert at generating realistic contact information for iPhone contacts app.",
            "calendar": "You are an expert at generating realistic calendar events and scheduling data.",
            "sms": "You are an expert at generating realistic SMS conversations and messaging patterns.",
            "emails": "You are an expert at generating realistic email conversations and communication patterns.",
            "reminders": "You are an expert at generating realistic reminders and task management data.",
            "notes": "You are an expert at generating realistic notes and personal documentation.",
            "wallet": "You are an expert at generating realistic wallet passes and digital payment data.",
            "alarms": "You are an expert at generating realistic alarm clock data and wake-up schedules."
        }
        
        base_message = "You are a helpful assistant that generates realistic synthetic data for iPhone apps. Always respond with valid JSON when requested."
        
        return system_messages.get(app_name, base_message)