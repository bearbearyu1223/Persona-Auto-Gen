"""Calendar data generator."""

from typing import Dict, List, Any
import logging
import random
from datetime import datetime, timedelta
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class CalendarGenerator(BaseGenerator):
    """Generator for iPhone Calendar app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "events"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic calendar events."""
        logger.info(f"Generating {count} calendar events")
        
        try:
            # Create generation prompt
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            
            # Generate with LLM
            response = self._generate_with_llm(prompt)
            
            # Parse response
            generated_data = self._parse_json_response(response)
            
            # Clean and validate
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            # Ensure we have the right number of events
            calendar_events = cleaned_data.get("events", [])
            if len(calendar_events) < count and self.config.use_faker_fallback:
                additional_needed = count - len(calendar_events)
                fallback_events = self._generate_fallback_events(
                    additional_needed, user_profile, events
                )
                calendar_events.extend(fallback_events)
            
            return {"events": calendar_events[:count]}
            
        except Exception as e:
            logger.error(f"Calendar generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"events": self._generate_fallback_events(count, user_profile, events)}
            return {"events": []}
    
    def _get_app_specific_instructions(self) -> str:
        """Return calendar-specific generation instructions."""
        return """
Please generate calendar events data in the following JSON format:
{
    "events": [
        {
            "id": "unique_identifier",
            "title": "Event Title",
            "description": "Event description",
            "start_datetime": "ISO timestamp",
            "end_datetime": "ISO timestamp", 
            "all_day": false,
            "location": {
                "name": "Location Name",
                "latitude": 37.7749,
                "longitude": -122.4194
            },
            "attendees": [
                {
                    "name": "Attendee Name",
                    "email": "attendee@example.com",
                    "status": "accepted|declined|tentative|pending"
                }
            ],
            "calendar_name": "Calendar Name",
            "category": "work|personal|health|travel|social|family|education|other",
            "priority": "low|normal|high",
            "reminder": {
                "enabled": true,
                "minutes_before": 15
            },
            "recurrence": {
                "frequency": "daily|weekly|monthly|yearly",
                "interval": 1,
                "end_date": "YYYY-MM-DD",
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"]
            },
            "created_date": "ISO timestamp",
            "modified_date": "ISO timestamp"
        }
    ]
}

Create realistic events that:
- Relate to the provided events and user profile
- Include both one-time and recurring events
- Have appropriate durations and timing
- Include relevant attendees and locations
- Mix different categories and priorities
- Show realistic calendar usage patterns
"""
    
    def _generate_fallback_events(self, count: int, user_profile: Dict[str, Any], 
                                 provided_events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback calendar events using Faker."""
        events = []
        
        event_categories = {
            "work": 0.4,
            "personal": 0.25,
            "social": 0.15,
            "health": 0.1,
            "family": 0.1
        }
        
        work_events = [
            "Team Meeting", "Project Review", "Client Call", "Stand-up", 
            "Training Session", "Conference Call", "Performance Review",
            "All Hands Meeting", "Planning Session", "Code Review"
        ]
        
        personal_events = [
            "Dentist Appointment", "Grocery Shopping", "Gym Session",
            "Hair Appointment", "Car Service", "Home Repair", 
            "Personal Time", "Reading", "Meditation", "Workout"
        ]
        
        social_events = [
            "Coffee with Friend", "Dinner Party", "Movie Night",
            "Birthday Party", "Happy Hour", "Game Night",
            "Concert", "Art Gallery", "Festival", "Networking Event"
        ]
        
        for i in range(count):
            category = random.choices(
                list(event_categories.keys()),
                list(event_categories.values())
            )[0]
            
            # Choose event title based on category
            if category == "work":
                title = random.choice(work_events)
            elif category == "personal":
                title = random.choice(personal_events)
            elif category == "social":
                title = random.choice(social_events)
            else:
                title = f"{category.title()} Event"
            
            # Generate start time
            start_time = self._generate_event_start_time(category)
            duration_hours = self._get_event_duration(category)
            end_time = start_time + timedelta(hours=duration_hours)
            
            # Create event
            event = {
                "id": self._generate_id(),
                "title": title,
                "description": self._generate_event_description(title, category),
                "start_datetime": start_time.isoformat(),
                "end_datetime": end_time.isoformat(),
                "all_day": False,
                "location": self._generate_location(category),
                "attendees": self._generate_attendees(category),
                "calendar_name": self._get_calendar_name(category),
                "category": category,
                "priority": self._get_priority(category),
                "reminder": {
                    "enabled": True,
                    "minutes_before": self._get_reminder_time(category)
                },
                "created_date": self._generate_realistic_timestamp(),
                "modified_date": self._generate_realistic_timestamp()
            }
            
            # Sometimes add recurrence
            if random.random() < 0.2:
                event["recurrence"] = self._generate_recurrence(category)
            
            events.append(event)
        
        return events
    
    def _generate_event_start_time(self, category: str) -> datetime:
        """Generate realistic start time based on event category."""
        base_date = self.fake.date_between(
            start_date=self.config.start_date.date(),
            end_date=self.config.end_date.date()
        )
        
        if category == "work":
            # Work events typically 9-17
            hour = random.randint(9, 17)
            minute = random.choice([0, 15, 30, 45])
        elif category == "social":
            # Social events typically evenings or weekends
            if random.random() < 0.7:  # Evening
                hour = random.randint(18, 22)
            else:  # Weekend afternoon
                hour = random.randint(12, 18)
            minute = random.choice([0, 30])
        else:
            # Other events can be any time
            hour = random.randint(8, 20)
            minute = random.choice([0, 15, 30, 45])
        
        return datetime.combine(base_date, datetime.min.time().replace(hour=hour, minute=minute))
    
    def _get_event_duration(self, category: str) -> float:
        """Get realistic event duration in hours."""
        if category == "work":
            return random.choice([0.5, 1.0, 1.5, 2.0])
        elif category == "social":
            return random.choice([2.0, 3.0, 4.0])
        else:
            return random.choice([0.5, 1.0, 1.5])
    
    def _generate_event_description(self, title: str, category: str) -> str:
        """Generate event description."""
        descriptions = {
            "work": f"Work-related {title.lower()}",
            "personal": f"Personal appointment: {title}",
            "social": f"Social gathering: {title}",
            "health": f"Health and wellness: {title}",
            "family": f"Family event: {title}"
        }
        return descriptions.get(category, f"{category.title()} event")
    
    def _generate_location(self, category: str) -> Dict[str, Any]:
        """Generate event location."""
        if category == "work":
            return {"name": f"Office - {self.fake.company()}", "latitude": 37.7749, "longitude": -122.4194}
        elif category == "social":
            return {"name": self.fake.company() + " Restaurant", "latitude": 37.7849, "longitude": -122.4094}
        else:
            return {"name": self.fake.address()}
    
    def _generate_attendees(self, category: str) -> List[Dict[str, Any]]:
        """Generate event attendees."""
        if category == "work":
            num_attendees = random.randint(2, 6)
        elif category == "social":
            num_attendees = random.randint(1, 4)
        else:
            return []  # Personal events typically don't have attendees
        
        attendees = []
        for _ in range(num_attendees):
            attendees.append({
                "name": self.fake.name(),
                "email": self.fake.email(),
                "status": random.choice(["accepted", "pending", "tentative"])
            })
        
        return attendees
    
    def _get_calendar_name(self, category: str) -> str:
        """Get calendar name based on category."""
        calendar_names = {
            "work": "Work",
            "personal": "Personal",
            "social": "Personal",
            "health": "Health",
            "family": "Family"
        }
        return calendar_names.get(category, "Personal")
    
    def _get_priority(self, category: str) -> str:
        """Get event priority."""
        if category == "work":
            return random.choice(["normal", "high"])
        else:
            return random.choice(["low", "normal"])
    
    def _get_reminder_time(self, category: str) -> int:
        """Get reminder time in minutes."""
        if category == "work":
            return random.choice([15, 30])
        else:
            return random.choice([15, 60, 1440])  # 15 min, 1 hour, 1 day
    
    def _generate_recurrence(self, category: str) -> Dict[str, Any]:
        """Generate recurrence pattern."""
        if category == "work":
            return {
                "frequency": "weekly",
                "interval": 1,
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "end_date": (self.config.end_date + timedelta(days=30)).strftime("%Y-%m-%d")
            }
        else:
            return {
                "frequency": random.choice(["weekly", "monthly"]),
                "interval": 1,
                "end_date": (self.config.end_date + timedelta(days=60)).strftime("%Y-%m-%d")
            }