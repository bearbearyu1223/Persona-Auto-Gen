"""Alarms data generator."""

from typing import Dict, List, Any
import logging
import random
from datetime import datetime, timedelta
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class AlarmsGenerator(BaseGenerator):
    """Generator for iPhone Clock app alarms data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "alarms"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic alarms data."""
        logger.info(f"Generating {count} alarms")
        
        try:
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            response = self._generate_with_llm(prompt)
            generated_data = self._parse_json_response(response)
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            alarms = cleaned_data.get("alarms", [])
            if len(alarms) < count and self.config.use_faker_fallback:
                additional_needed = count - len(alarms)
                fallback_alarms = self._generate_fallback_alarms(
                    additional_needed, user_profile, events
                )
                alarms.extend(fallback_alarms)
            
            return {"alarms": alarms[:count]}
            
        except Exception as e:
            logger.error(f"Alarms generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"alarms": self._generate_fallback_alarms(count, user_profile, events)}
            return {"alarms": []}
    
    def _get_app_specific_instructions(self) -> str:
        """Return alarms-specific generation instructions."""
        return """
Please generate alarms data in the following JSON format:
{
    "alarms": [
        {
            "id": "unique_identifier",
            "label": "Alarm label/description",
            "time": "HH:MM",
            "enabled": true/false,
            "repeat_schedule": {
                "is_recurring": true/false,
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "frequency": "daily|weekdays|weekends|custom|once"
            },
            "sound": {
                "sound_name": "Sound name",
                "sound_type": "built_in|song|custom",
                "volume": 0.8,
                "vibration": true/false
            },
            "snooze": {
                "enabled": true/false,
                "duration_minutes": 9,
                "max_snoozes": 3
            },
            "bedtime_alarm": false,
            "smart_wake": {
                "enabled": true/false,
                "window_minutes": 15
            },
            "category": "work|personal|medication|exercise|sleep|other",
            "created_date": "ISO timestamp",
            "last_modified": "ISO timestamp",
            "last_triggered": "ISO timestamp",
            "next_trigger": "ISO timestamp",
            "statistics": {
                "times_triggered": 45,
                "times_snoozed": 12,
                "average_snooze_count": 1.2,
                "turned_off_quickly": 8
            },
            "location_based": {
                "enabled": false,
                "travel_adjustment": false
            }
        }
    ]
}

Create realistic alarms that:
- Reflect the user's daily routine and lifestyle
- Include work alarms, personal alarms, and special purpose alarms
- Show realistic usage patterns (some enabled, some disabled)
- Include both recurring and one-time alarms
- Have appropriate timing based on the user's schedule
- Include realistic statistics showing actual usage
- Consider the user's profession and lifestyle for alarm purposes
"""
    
    def _generate_fallback_alarms(self, count: int, user_profile: Dict[str, Any], 
                                 events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback alarms using templates."""
        alarms = []
        
        # Determine user's likely schedule based on profile
        occupation = user_profile.get("occupation", "").lower()
        age = user_profile.get("age", 30)
        lifestyle = user_profile.get("lifestyle", "").lower()
        
        # Define alarm templates based on user characteristics
        alarm_templates = self._get_alarm_templates(occupation, age, lifestyle)
        
        # Generate alarms
        for i in range(count):
            template = random.choice(alarm_templates)
            alarm = self._create_alarm_from_template(template, i)
            alarms.append(alarm)
        
        return alarms
    
    def _get_alarm_templates(self, occupation: str, age: int, lifestyle: str) -> List[Dict[str, Any]]:
        """Get alarm templates based on user characteristics."""
        templates = []
        
        # Work-related alarms
        if any(work_term in occupation for work_term in ["developer", "engineer", "manager", "analyst", "consultant"]):
            templates.extend([
                {
                    "label": "Work Day",
                    "time_range": (7, 0, 8, 30),  # 7:00 AM to 8:30 AM
                    "category": "work",
                    "frequency": "weekdays",
                    "priority": "high"
                },
                {
                    "label": "Stand-up Meeting",
                    "time_range": (8, 45, 9, 15),
                    "category": "work", 
                    "frequency": "weekdays",
                    "priority": "medium"
                }
            ])
        
        # Healthcare/early shift workers
        if any(term in occupation for term in ["nurse", "doctor", "healthcare", "medical"]):
            templates.extend([
                {
                    "label": "Early Shift",
                    "time_range": (5, 30, 6, 30),
                    "category": "work",
                    "frequency": "custom",
                    "priority": "high"
                }
            ])
        
        # Student schedules
        if "student" in occupation or age < 25:
            templates.extend([
                {
                    "label": "Class",
                    "time_range": (8, 0, 9, 0),
                    "category": "personal",
                    "frequency": "weekdays",
                    "priority": "high"
                },
                {
                    "label": "Study Time",
                    "time_range": (19, 0, 20, 0),
                    "category": "personal",
                    "frequency": "daily",
                    "priority": "medium"
                }
            ])
        
        # Health and wellness alarms
        if "health" in lifestyle or age > 40:
            templates.extend([
                {
                    "label": "Morning Medication",
                    "time_range": (8, 0, 8, 30),
                    "category": "medication",
                    "frequency": "daily",
                    "priority": "high"
                },
                {
                    "label": "Evening Medication",
                    "time_range": (20, 0, 21, 0),
                    "category": "medication", 
                    "frequency": "daily",
                    "priority": "high"
                }
            ])
        
        # Fitness alarms
        if any(term in lifestyle for term in ["active", "fitness", "gym", "exercise"]):
            templates.extend([
                {
                    "label": "Gym Time",
                    "time_range": (6, 0, 7, 0),
                    "category": "exercise",
                    "frequency": "custom",
                    "priority": "medium"
                },
                {
                    "label": "Evening Workout",
                    "time_range": (18, 0, 19, 30),
                    "category": "exercise",
                    "frequency": "custom", 
                    "priority": "medium"
                }
            ])
        
        # General personal alarms
        templates.extend([
            {
                "label": "Wake Up",
                "time_range": (6, 30, 8, 0),
                "category": "personal",
                "frequency": "weekdays",
                "priority": "high"
            },
            {
                "label": "Weekend Wake Up",
                "time_range": (8, 0, 10, 0),
                "category": "personal",
                "frequency": "weekends",
                "priority": "medium"
            },
            {
                "label": "Bedtime Reminder",
                "time_range": (22, 0, 23, 30),
                "category": "sleep",
                "frequency": "daily",
                "priority": "low"
            }
        ])
        
        return templates
    
    def _create_alarm_from_template(self, template: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Create an alarm from a template."""
        # Generate time within the specified range
        start_hour, start_min, end_hour, end_min = template["time_range"]
        
        # Convert to minutes for easier calculation
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        # Random time within range
        alarm_minutes = random.randint(start_minutes, end_minutes)
        alarm_hour = alarm_minutes // 60
        alarm_min = alarm_minutes % 60
        
        # Format time
        alarm_time = f"{alarm_hour:02d}:{alarm_min:02d}"
        
        # Determine repeat schedule
        frequency = template["frequency"]
        if frequency == "weekdays":
            repeat_schedule = {
                "is_recurring": True,
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "frequency": "weekdays"
            }
        elif frequency == "weekends":
            repeat_schedule = {
                "is_recurring": True,
                "days_of_week": ["saturday", "sunday"],
                "frequency": "weekends"
            }
        elif frequency == "daily":
            repeat_schedule = {
                "is_recurring": True,
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "frequency": "daily"
            }
        elif frequency == "custom":
            # Random selection of days
            all_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            selected_days = random.sample(all_days, random.randint(2, 5))
            repeat_schedule = {
                "is_recurring": True,
                "days_of_week": sorted(selected_days),
                "frequency": "custom"
            }
        else:  # once
            repeat_schedule = {
                "is_recurring": False,
                "frequency": "once"
            }
        
        # Determine if alarm is enabled (most should be, some disabled)
        enabled = random.choice([True, True, True, False])  # 75% enabled
        
        # Create alarm
        alarm = {
            "id": f"alarm_{self._generate_id()}_{index}",
            "label": template["label"],
            "time": alarm_time,
            "enabled": enabled,
            "repeat_schedule": repeat_schedule,
            "sound": self._generate_alarm_sound(),
            "snooze": self._generate_snooze_settings(template["priority"]),
            "bedtime_alarm": template["category"] == "sleep",
            "smart_wake": self._generate_smart_wake_settings(),
            "category": template["category"],
            "created_date": self._generate_realistic_timestamp(),
            "last_modified": self._generate_realistic_timestamp(),
            "statistics": self._generate_alarm_statistics(enabled, template["priority"])
        }
        
        # Add optional fields
        if enabled and repeat_schedule["is_recurring"]:
            alarm["last_triggered"] = self._generate_recent_timestamp()
            alarm["next_trigger"] = self._generate_future_timestamp(alarm_time, repeat_schedule)
        
        alarm["location_based"] = {
            "enabled": random.choice([True, False]),
            "travel_adjustment": random.choice([True, False])
        }
        
        return alarm
    
    def _generate_alarm_sound(self) -> Dict[str, Any]:
        """Generate alarm sound settings."""
        built_in_sounds = [
            "Radar", "Apex", "Bulletin", "By The Seaside", "Chimes", "Circuit", 
            "Constellation", "Cosmic", "Crystals", "Hillside", "Illuminate",
            "Night Owl", "Opening", "Playtime", "Presto", "Ripples", "Sencha",
            "Signal", "Silk", "Slow Rise", "Stargaze", "Summit", "Synth"
        ]
        
        sound_type = random.choices(
            ["built_in", "song", "custom"],
            weights=[0.7, 0.2, 0.1]
        )[0]
        
        if sound_type == "built_in":
            sound_name = random.choice(built_in_sounds)
        elif sound_type == "song":
            sound_name = f"{self.fake.catch_phrase()} - {self.fake.name()}"
        else:  # custom
            sound_name = f"Custom Sound {random.randint(1, 10)}"
        
        return {
            "sound_name": sound_name,
            "sound_type": sound_type,
            "volume": round(random.uniform(0.4, 1.0), 2),
            "vibration": random.choice([True, False])
        }
    
    def _generate_snooze_settings(self, priority: str) -> Dict[str, Any]:
        """Generate snooze settings based on alarm priority."""
        # Higher priority alarms less likely to have snooze enabled
        if priority == "high":
            snooze_enabled = random.choice([True, False])
        elif priority == "medium":
            snooze_enabled = random.choice([True, True, False])  # 67% enabled
        else:  # low
            snooze_enabled = random.choice([True, True, True, False])  # 75% enabled
        
        snooze_settings = {"enabled": snooze_enabled}
        
        if snooze_enabled:
            snooze_settings.update({
                "duration_minutes": random.choice([5, 9, 10, 15]),
                "max_snoozes": random.choice([1, 2, 3, 5])
            })
        
        return snooze_settings
    
    def _generate_smart_wake_settings(self) -> Dict[str, Any]:
        """Generate smart wake settings."""
        enabled = random.choice([True, False])
        settings = {"enabled": enabled}
        
        if enabled:
            settings["window_minutes"] = random.choice([10, 15, 20, 30])
        
        return settings
    
    def _generate_alarm_statistics(self, enabled: bool, priority: str) -> Dict[str, Any]:
        """Generate realistic alarm usage statistics."""
        if not enabled:
            # Disabled alarms have minimal stats
            return {
                "times_triggered": random.randint(0, 5),
                "times_snoozed": random.randint(0, 2),
                "average_snooze_count": 0,
                "turned_off_quickly": random.randint(0, 3)
            }
        
        # Active alarms have more realistic usage patterns
        base_triggers = random.randint(10, 100)
        
        # Priority affects snooze behavior
        if priority == "high":
            snooze_rate = 0.1  # High priority = less snoozing
        elif priority == "medium":
            snooze_rate = 0.3
        else:  # low
            snooze_rate = 0.5
        
        times_snoozed = int(base_triggers * snooze_rate * random.uniform(0.5, 1.5))
        average_snooze_count = round(times_snoozed / max(base_triggers, 1), 1)
        turned_off_quickly = int(base_triggers * random.uniform(0.1, 0.4))
        
        return {
            "times_triggered": base_triggers,
            "times_snoozed": times_snoozed,
            "average_snooze_count": average_snooze_count,
            "turned_off_quickly": turned_off_quickly
        }
    
    def _generate_recent_timestamp(self) -> str:
        """Generate a recent timestamp for last_triggered."""
        # Within the last week
        recent_date = datetime.now() - timedelta(days=random.randint(0, 7))
        return recent_date.isoformat()
    
    def _generate_future_timestamp(self, alarm_time: str, repeat_schedule: Dict[str, Any]) -> str:
        """Generate future timestamp for next_trigger."""
        hour, minute = map(int, alarm_time.split(':'))
        
        # Find next occurrence
        now = datetime.now()
        
        if repeat_schedule["is_recurring"]:
            # Find next day when this alarm should trigger
            days_of_week = repeat_schedule.get("days_of_week", [])
            if days_of_week:
                weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                day_indices = [weekdays.index(day) for day in days_of_week]
                
                # Find next occurrence
                for i in range(7):  # Check next 7 days
                    check_date = now + timedelta(days=i)
                    if check_date.weekday() in day_indices:
                        next_trigger = check_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        if next_trigger > now:
                            return next_trigger.isoformat()
        
        # Fallback: tomorrow at the alarm time
        tomorrow = now + timedelta(days=1)
        next_trigger = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return next_trigger.isoformat()