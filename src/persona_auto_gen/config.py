"""Configuration management for the persona generation system."""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from pathlib import Path
import os
from dataclasses import dataclass, field
from enum import Enum


class OpenAIModel(Enum):
    """Available OpenAI models."""
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_3_5_TURBO = "gpt-3.5-turbo"


class AppType(Enum):
    """Supported iPhone app types."""
    CONTACTS = "contacts"
    CALENDAR = "calendar"
    SMS = "sms"
    EMAILS = "emails"
    REMINDERS = "reminders"
    NOTES = "notes"
    WALLET = "wallet"
    ALARMS = "alarms"


@dataclass
class Config:
    """Main configuration class for the persona generation system."""
    
    # OpenAI Configuration
    openai_model: OpenAIModel = OpenAIModel.GPT_4O
    openai_api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    
    # Time Configuration
    start_date: datetime = field(default_factory=lambda: datetime(2024, 1, 1))
    end_date: datetime = field(default_factory=lambda: datetime(2024, 5, 31))
    
    # Data Generation Configuration
    data_volume: Dict[str, int] = field(default_factory=lambda: {
        "contacts": 15,
        "calendar": 20,
        "sms": 30,
        "emails": 25,
        "reminders": 18,
        "notes": 12,
        "wallet": 8,
        "alarms": 10
    })
    
    # Enabled Apps
    enabled_apps: List[str] = field(default_factory=lambda: [
        "contacts", "calendar", "sms", "emails", "reminders", "notes", "wallet", "alarms"
    ])
    
    # Output Configuration
    output_directory: Path = field(default_factory=lambda: Path("./output"))
    create_summary_report: bool = True
    include_metadata: bool = True
    
    # Validation Configuration
    max_validation_errors: int = 10
    strict_validation: bool = True
    
    # Quality Control
    enable_reflection: bool = True
    min_quality_score: float = 6.0
    max_regeneration_attempts: int = 3
    
    # Advanced Options
    use_faker_fallback: bool = True
    preserve_privacy: bool = True
    anonymize_sensitive_data: bool = True
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Get API key from environment if not provided
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            
        if not self.openai_api_key:
            raise ValueError("OpenAI API key must be provided via openai_api_key parameter or OPENAI_API_KEY environment variable")
        
        # Ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Validate date range
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        
        # Validate enabled apps
        valid_apps = {app.value for app in AppType}
        invalid_apps = set(self.enabled_apps) - valid_apps
        if invalid_apps:
            raise ValueError(f"Invalid apps specified: {invalid_apps}. Valid apps: {valid_apps}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        # Handle datetime conversion
        if "start_date" in config_dict and isinstance(config_dict["start_date"], str):
            config_dict["start_date"] = datetime.fromisoformat(config_dict["start_date"])
        
        if "end_date" in config_dict and isinstance(config_dict["end_date"], str):
            config_dict["end_date"] = datetime.fromisoformat(config_dict["end_date"])
            
        # Handle model enum conversion
        if "openai_model" in config_dict and isinstance(config_dict["openai_model"], str):
            config_dict["openai_model"] = OpenAIModel(config_dict["openai_model"])
            
        # Handle Path conversion
        if "output_directory" in config_dict and isinstance(config_dict["output_directory"], str):
            config_dict["output_directory"] = Path(config_dict["output_directory"])
        
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        result = {}
        
        for key, value in self.__dict__.items():
            # Skip sensitive information like API keys
            if key == 'openai_api_key':
                result[key] = "[REDACTED]"
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, OpenAIModel):
                result[key] = value.value
            elif isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
                
        return result
    
    def get_schema_path(self, app_name: str) -> Path:
        """Get the path to the JSON schema for a specific app."""
        schema_dir = Path(__file__).parent / "schemas"
        return schema_dir / f"{app_name}.json"
    
    def get_output_path(self, profile_id: str = None) -> Path:
        """Get the output path for a specific profile."""
        if profile_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            profile_id = f"user_profile_{timestamp}"
            
        return self.output_directory / profile_id
    
    def validate_configuration(self) -> List[str]:
        """Validate the current configuration and return any issues."""
        issues = []
        
        # Check API key
        if not self.openai_api_key or len(self.openai_api_key.strip()) == 0:
            issues.append("OpenAI API key is required")
        
        # Check date range
        if self.start_date >= self.end_date:
            issues.append("Start date must be before end date")
            
        # Check data volumes
        for app, count in self.data_volume.items():
            if count < 0:
                issues.append(f"Data volume for {app} cannot be negative")
            if count > 1000:
                issues.append(f"Data volume for {app} is very high ({count}), consider reducing")
        
        # Check enabled apps have data volumes
        for app in self.enabled_apps:
            if app not in self.data_volume:
                issues.append(f"No data volume specified for enabled app: {app}")
        
        # Check schema files exist
        for app in self.enabled_apps:
            schema_path = self.get_schema_path(app)
            if not schema_path.exists():
                issues.append(f"Schema file missing for {app}: {schema_path}")
        
        return issues
    
    def get_time_range_days(self) -> int:
        """Get the number of days in the configured time range."""
        return (self.end_date - self.start_date).days
    
    def is_app_enabled(self, app_name: str) -> bool:
        """Check if a specific app is enabled."""
        return app_name in self.enabled_apps
    
    def get_app_data_count(self, app_name: str) -> int:
        """Get the configured data count for a specific app."""
        return self.data_volume.get(app_name, 0)
    
    def get_enabled_apps_with_data(self) -> List[str]:
        """Get list of enabled apps that have data_volume > 0."""
        return [
            app for app in self.enabled_apps 
            if self.data_volume.get(app, 0) > 0
        ]