"""Email data generator."""

from typing import Dict, List, Any
import logging
import random
from datetime import datetime, timedelta
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class EmailsGenerator(BaseGenerator):
    """Generator for iPhone Mail app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "emails"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic email data."""
        logger.info(f"Generating {count} emails")
        
        try:
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            response = self._generate_with_llm(prompt)
            generated_data = self._parse_json_response(response)
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            emails = cleaned_data.get("emails", [])
            if len(emails) < count and self.config.use_faker_fallback:
                additional_needed = count - len(emails)
                fallback_emails = self._generate_fallback_emails(
                    additional_needed, user_profile, events
                )
                emails.extend(fallback_emails)
            
            return {"emails": emails[:count]}
            
        except Exception as e:
            logger.error(f"Email generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"emails": self._generate_fallback_emails(count, user_profile, events)}
            return {"emails": []}
    
    def _get_app_specific_instructions(self) -> str:
        return """
Generate realistic email data in JSON format with proper email structure, 
mixing personal and work emails, with realistic subjects and content.
Include sent and received emails with appropriate timing and relationships.
"""
    
    def _generate_fallback_emails(self, count: int, user_profile: Dict[str, Any], 
                                 events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback emails using templates."""
        emails = []
        user_email = "user@example.com"
        
        for i in range(count):
            is_sent = random.choice([True, False])
            category = random.choice(["work", "personal", "promotional", "social"])
            
            email = {
                "id": f"email_{self._generate_id()}_{i}",
                "subject": self._generate_subject(category),
                "from": {"email": user_email, "name": "User"} if is_sent else {"email": self.fake.email(), "name": self.fake.name()},
                "to": [{"email": self.fake.email(), "name": self.fake.name()}] if is_sent else [{"email": user_email, "name": "User"}],
                "cc": [],
                "bcc": [],
                "body": {"text": self._generate_body(category)},
                "timestamp": self._generate_realistic_timestamp(),
                "is_sent": is_sent,
                "is_read": random.choice([True, False]) if not is_sent else True,
                "is_starred": random.random() < 0.1,
                "priority": "normal",
                "folder": "sent" if is_sent else "inbox",
                "labels": [],
                "attachments": [],
                "thread_id": f"thread_{i}",
                "account": "user@example.com",
                "category": category
            }
            
            emails.append(email)
        
        return emails
    
    def _generate_subject(self, category: str) -> str:
        subjects = {
            "work": ["Meeting Follow-up", "Project Update", "Weekly Report", "Review Request"],
            "personal": ["Weekend Plans", "Family Update", "Quick Question", "Thanks!"],
            "promotional": ["Special Offer", "Newsletter", "Sale Alert", "New Products"],
            "social": ["Event Invitation", "Photo Share", "Catch Up", "Party Planning"]
        }
        return random.choice(subjects.get(category, ["General Email"]))
    
    def _generate_body(self, category: str) -> str:
        bodies = {
            "work": "Following up on our meeting today. Please review the attached documents and let me know your thoughts.",
            "personal": "Hope you're doing well! Let me know if you'd like to get together this weekend.",
            "promotional": "Don't miss our special offer! Save 20% on all items this week only.",
            "social": "You're invited to our upcoming event. Hope to see you there!"
        }
        return bodies.get(category, "General email content.")