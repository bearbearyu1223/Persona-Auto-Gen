"""Base generator class for all iPhone app data generators."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime, timedelta
import random

from ..config import Config
from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """Abstract base class for all data generators."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm_client = LLMClient(config)
        self.app_name = self._get_app_name()
    
    @abstractmethod
    def _get_app_name(self) -> str:
        """Return the name of the app this generator handles."""
        pass
    
    @abstractmethod
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate synthetic data for this app."""
        pass
    
    def _create_generation_prompt(self, user_profile: Dict[str, Any], 
                                events: List[str], analysis: Dict[str, Any], 
                                count: int) -> str:
        """Create a prompt for data generation."""
        events_text = "\n".join(f"- {event}" for event in events)
        
        base_prompt = f"""
Generate realistic {self.app_name} data for the following user profile and events.

USER PROFILE:
{json.dumps(user_profile, indent=2)}

EVENTS:
{events_text}

ANALYSIS:
{json.dumps(analysis, indent=2)}

TIME PERIOD: {self.config.start_date.strftime('%Y-%m-%d')} to {self.config.end_date.strftime('%Y-%m-%d')}

Generate {count} realistic {self.app_name} entries that:
1. Reflect the user's personality and lifestyle
2. Connect logically to the provided events
3. Show natural patterns and relationships
4. Include appropriate timestamps within the time period
5. Feel authentic and human-like

"""
        return base_prompt + self._get_app_specific_instructions()
    
    @abstractmethod
    def _get_app_specific_instructions(self) -> str:
        """Return app-specific generation instructions."""
        pass
    
    def _generate_with_llm(self, prompt: str, max_retries: int = 3) -> str:
        """Generate data using the LLM with retry logic."""
        for attempt in range(max_retries):
            try:
                response = self.llm_client.generate(
                    prompt=prompt,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                return response
            
            except Exception as e:
                logger.warning(f"LLM generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                
        return ""
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        try:
            # Find JSON boundaries
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.error("No JSON found in response")
                return self._get_fallback_data()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data when LLM generation fails."""
        return {self.app_name: []}
    
    def _generate_realistic_timestamp(self, base_date: Optional[datetime] = None) -> str:
        """Generate a realistic timestamp within the configured time range."""
        if base_date is None:
            # Random timestamp within the full range
            start_timestamp = self.config.start_date.timestamp()
            end_timestamp = self.config.end_date.timestamp()
            random_timestamp = random.uniform(start_timestamp, end_timestamp)
            generated_datetime = datetime.fromtimestamp(random_timestamp)
        else:
            # Generate timestamp around the base date
            variance_hours = random.randint(-24, 24)
            generated_datetime = base_date + timedelta(hours=variance_hours)
            
            # Ensure it's within bounds
            if generated_datetime < self.config.start_date:
                generated_datetime = self.config.start_date
            elif generated_datetime > self.config.end_date:
                generated_datetime = self.config.end_date
        
        return generated_datetime.isoformat()
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        timestamp = datetime.now().timestamp()
        random_part = random.randint(1000, 9999)
        return f"{self.app_name}_{int(timestamp)}_{random_part}"
    
    def _clean_and_validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate generated data."""
        if self.app_name not in data:
            logger.warning(f"Generated data missing {self.app_name} key")
            return {self.app_name: []}
        
        app_data = data[self.app_name]
        if not isinstance(app_data, list):
            logger.warning(f"{self.app_name} data is not a list")
            return {self.app_name: []}
        
        # Clean individual entries
        cleaned_entries = []
        for entry in app_data:
            if isinstance(entry, dict):
                cleaned_entry = self._clean_entry(entry)
                if cleaned_entry:
                    cleaned_entries.append(cleaned_entry)
        
        return {self.app_name: cleaned_entries}
    
    def _clean_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clean an individual data entry."""
        # Ensure ID exists
        if "id" not in entry:
            entry["id"] = self._generate_id()
        
        # Add timestamps if missing
        self._ensure_timestamps(entry)
        
        return entry
    
    def _ensure_timestamps(self, entry: Dict[str, Any]):
        """Ensure required timestamps exist in entry."""
        timestamp_fields = ["created_date", "timestamp", "start_datetime"]
        
        for field in timestamp_fields:
            if field in entry and not entry[field]:
                entry[field] = self._generate_realistic_timestamp()
    
    def _relate_to_events(self, events: List[str], count: int) -> List[str]:
        """Select which events to relate the generated data to."""
        if not events:
            return []
        
        # Select a subset of events to relate to
        max_events = min(len(events), max(1, count // 3))
        return random.sample(events, max_events)