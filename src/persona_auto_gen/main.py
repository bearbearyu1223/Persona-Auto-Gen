"""Main entry point for the Persona Auto Gen system."""

import logging
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import Config, OpenAIModel
from .agents.workflow import PersonaWorkflow

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PersonaAgent:
    """Main class for the Persona Auto Gen system."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the PersonaAgent with configuration."""
        if config is None:
            config = Config()
        
        self.config = config
        self.workflow = PersonaWorkflow(config)
        
        # Validate configuration
        config_issues = config.validate_configuration()
        if config_issues:
            logger.warning(f"Configuration issues found: {config_issues}")
    
    def generate(self, user_profile: Dict[str, Any], events: List[str]) -> Dict[str, Any]:
        """Generate synthetic iPhone app data."""
        logger.info("Starting persona data generation")
        
        # Validate inputs
        self._validate_inputs(user_profile, events)
        
        try:
            # Run the workflow
            result = self.workflow.run(user_profile, events)
            
            if result["success"]:
                logger.info(f"Generation completed successfully. Output saved to: {result['output_path']}")
            else:
                logger.error(f"Generation failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error during generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "output_path": "",
                "generated_data": {},
                "validation_results": {},
                "reflection_results": {},
                "errors": [str(e)]
            }
    
    async def agenerate(self, user_profile: Dict[str, Any], events: List[str]) -> Dict[str, Any]:
        """Asynchronously generate synthetic iPhone app data."""
        logger.info("Starting async persona data generation")
        
        # Validate inputs
        self._validate_inputs(user_profile, events)
        
        try:
            # Run the workflow asynchronously
            result = await self.workflow.arun(user_profile, events)
            
            if result["success"]:
                logger.info(f"Async generation completed successfully. Output saved to: {result['output_path']}")
            else:
                logger.error(f"Async generation failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error during async generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "output_path": "",
                "generated_data": {},
                "validation_results": {},
                "reflection_results": {},
                "errors": [str(e)]
            }
    
    def _validate_inputs(self, user_profile: Dict[str, Any], events: List[str]):
        """Validate input parameters."""
        if not isinstance(user_profile, dict):
            raise ValueError("user_profile must be a dictionary")
        
        if not user_profile:
            raise ValueError("user_profile cannot be empty")
        
        if not isinstance(events, list):
            raise ValueError("events must be a list")
        
        if not events:
            raise ValueError("events list cannot be empty")
        
        # Check that events are strings
        for i, event in enumerate(events):
            if not isinstance(event, str):
                raise ValueError(f"Event {i} must be a string")
            if not event.strip():
                raise ValueError(f"Event {i} cannot be empty")
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get information about the current configuration."""
        return {
            "model": self.config.openai_model.value,
            "enabled_apps": self.config.enabled_apps,
            "data_volume": self.config.data_volume,
            "time_range": {
                "start": self.config.start_date.isoformat(),
                "end": self.config.end_date.isoformat(),
                "days": self.config.get_time_range_days()
            },
            "output_directory": str(self.config.output_directory),
            "validation_settings": {
                "strict_validation": self.config.strict_validation,
                "max_validation_errors": self.config.max_validation_errors
            }
        }
    
    def validate_configuration(self) -> List[str]:
        """Validate the current configuration."""
        return self.config.validate_configuration()


def create_example_config() -> Config:
    """Create an example configuration."""
    from datetime import datetime
    
    return Config(
        openai_model=OpenAIModel.GPT_4O,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 5, 31),
        data_volume={
            "contacts": 15,
            "calendar": 20,
            "sms": 25,
            "emails": 20,
            "reminders": 15,
            "notes": 10,
            "wallet": 8,
            "alarms": 8
        },
        temperature=0.7,
        max_tokens=4000
    )


def create_example_user_profile() -> Dict[str, Any]:
    """Create an example user profile."""
    return {
        "age": 28,
        "occupation": "Software Developer",
        "location": "San Francisco, CA",
        "interests": ["technology", "hiking", "coffee", "reading"],
        "lifestyle": "Urban professional with active social life",
        "tech_savviness": "High",
        "communication_style": "Casual but professional when needed"
    }


def create_example_events() -> List[str]:
    """Create example events."""
    return [
        "Attending a tech conference in Austin",
        "Weekly team standup meetings every Tuesday at 10am",
        "Friend's wedding in Napa Valley on March 15th",
        "Monthly book club meetings on first Thursday",
        "Weekend hiking trips to local trails",
        "Birthday party planning for best friend",
        "Regular gym sessions 3x per week",
        "Coffee meetings with startup mentors",
        "Family dinner every Sunday",
        "Concert at Golden Gate Park"
    ]


def main():
    """Main entry point for command-line usage."""
    try:
        # Create example configuration
        config = create_example_config()
        
        # Create example inputs
        user_profile = create_example_user_profile()
        events = create_example_events()
        
        # Initialize agent
        agent = PersonaAgent(config)
        
        # Show configuration
        logger.info("Configuration:")
        config_info = agent.get_config_info()
        for key, value in config_info.items():
            logger.info(f"  {key}: {value}")
        
        # Generate data
        logger.info("Starting data generation...")
        result = agent.generate(user_profile, events)
        
        if result["success"]:
            logger.info("✅ Generation completed successfully!")
            logger.info(f"📁 Output saved to: {result['output_path']}")
            
            # Show summary
            generated_data = result["generated_data"]
            logger.info("📊 Generated data summary:")
            for app_name, app_data in generated_data.items():
                if app_data:
                    # Get the appropriate data key for each app
                    data_keys = {
                        "contacts": "contacts",
                        "calendar": "events", 
                        "sms": "conversations",
                        "emails": "emails",
                        "reminders": "reminders",
                        "notes": "notes",
                        "wallet": "passes",
                        "alarms": "alarms"
                    }
                    data_key = data_keys.get(app_name, app_name)
                    count = len(app_data.get(data_key, []))
                    logger.info(f"  {app_name}: {count} entries")
            
            # Show quality scores if available
            reflection = result.get("reflection_results", {})
            if reflection:
                logger.info("🎯 Quality Assessment:")
                logger.info(f"  Overall Quality: {reflection.get('overall_quality', 'unknown')}")
                logger.info(f"  Realism Score: {reflection.get('realism_score', 0)}/10")
                logger.info(f"  Diversity Score: {reflection.get('diversity_score', 0)}/10")
                logger.info(f"  Coherence Score: {reflection.get('coherence_score', 0)}/10")
        
        else:
            logger.error("❌ Generation failed!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            for error in result.get('errors', []):
                logger.error(f"  - {error}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Generation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()