"""Reminders data generator."""

from typing import Dict, List, Any
import logging
import random
from datetime import datetime, timedelta
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class RemindersGenerator(BaseGenerator):
    """Generator for iPhone Reminders app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "reminders"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic reminders data."""
        logger.info(f"Generating {count} reminders")
        
        try:
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            response = self._generate_with_llm(prompt)
            generated_data = self._parse_json_response(response)
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            reminders = cleaned_data.get("reminders", [])
            if len(reminders) < count and self.config.use_faker_fallback:
                additional_needed = count - len(reminders)
                fallback_reminders = self._generate_fallback_reminders(
                    additional_needed, user_profile, events
                )
                reminders.extend(fallback_reminders)
            
            return {"reminders": reminders[:count]}
            
        except Exception as e:
            logger.error(f"Reminders generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"reminders": self._generate_fallback_reminders(count, user_profile, events)}
            return {"reminders": []}
    
    def _get_app_specific_instructions(self) -> str:
        return """
Generate realistic reminders data including personal tasks, work items,
shopping lists, and location-based reminders with appropriate due dates and priorities.
"""
    
    def _generate_fallback_reminders(self, count: int, user_profile: Dict[str, Any], 
                                   events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback reminders using templates."""
        reminders = []
        
        reminder_templates = {
            "personal": ["Call dentist", "Pick up dry cleaning", "Pay bills", "Exercise"],
            "work": ["Finish report", "Schedule meeting", "Review documents", "Follow up"],
            "shopping": ["Buy groceries", "Get batteries", "Pick up prescription", "Buy gift"],
            "health": ["Take vitamins", "Doctor appointment", "Gym session", "Walk dog"]
        }
        
        for i in range(count):
            category = random.choice(list(reminder_templates.keys()))
            title = random.choice(reminder_templates[category])
            
            reminder = {
                "id": f"reminder_{self._generate_id()}_{i}",
                "title": title,
                "notes": f"Notes for {title.lower()}",
                "completed": random.choice([True, False]),
                "due_date": self._generate_realistic_timestamp(),
                "priority": random.choice(["low", "medium", "high"]),
                "list_name": category.title(),
                "category": category,
                "location_reminder": {"enabled": False},
                "time_reminder": {
                    "enabled": True,
                    "alert_times": [self._generate_realistic_timestamp()],
                    "repeat": {"frequency": "never"}
                },
                "subtasks": [],
                "flagged": random.random() < 0.1,
                "created_date": self._generate_realistic_timestamp(),
                "modified_date": self._generate_realistic_timestamp()
            }
            
            if reminder["completed"]:
                reminder["completion_date"] = self._generate_realistic_timestamp()
            
            reminders.append(reminder)
        
        return reminders