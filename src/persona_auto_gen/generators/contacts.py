"""Contacts data generator."""

from typing import Dict, List, Any
import logging
import random
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class ContactsGenerator(BaseGenerator):
    """Generator for iPhone Contacts app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "contacts"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic contacts data."""
        logger.info(f"Generating {count} contacts")
        
        try:
            # Create generation prompt
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            
            # Generate with LLM
            response = self._generate_with_llm(prompt)
            
            # Parse response
            generated_data = self._parse_json_response(response)
            
            # Clean and validate
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            # Ensure we have the right number of contacts
            contacts = cleaned_data.get("contacts", [])
            if len(contacts) < count and self.config.use_faker_fallback:
                additional_needed = count - len(contacts)
                fallback_contacts = self._generate_fallback_contacts(
                    additional_needed, user_profile, events
                )
                contacts.extend(fallback_contacts)
            
            return {"contacts": contacts[:count]}
            
        except Exception as e:
            logger.error(f"Contacts generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"contacts": self._generate_fallback_contacts(count, user_profile, events)}
            return {"contacts": []}
    
    def _get_app_specific_instructions(self) -> str:
        """Return contacts-specific generation instructions."""
        return """
Please generate contacts data in the following JSON format:
{
    "contacts": [
        {
            "id": "unique_identifier",
            "first_name": "string",
            "last_name": "string", 
            "display_name": "string",
            "phone_numbers": [
                {
                    "label": "mobile|home|work|main|other",
                    "number": "+1234567890"
                }
            ],
            "email_addresses": [
                {
                    "label": "home|work|other",
                    "email": "email@example.com"
                }
            ],
            "addresses": [
                {
                    "label": "home|work|other",
                    "street": "123 Main St",
                    "city": "City",
                    "state": "State",
                    "postal_code": "12345",
                    "country": "Country"
                }
            ],
            "organization": "Company Name",
            "job_title": "Job Title",
            "birthday": "YYYY-MM-DD",
            "notes": "Additional notes",
            "relationship": "family|friend|colleague|acquaintance|business|other",
            "created_date": "ISO timestamp"
        }
    ]
}

Include diverse relationship types and ensure contacts relate to the events and user profile.
Mix of complete and partial contact information to be realistic.
Include family, friends, colleagues, and professional contacts as appropriate.
"""
    
    def _generate_fallback_contacts(self, count: int, user_profile: Dict[str, Any], 
                                  events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback contacts using Faker."""
        contacts = []
        
        relationship_weights = {
            "friend": 0.4,
            "colleague": 0.3,
            "family": 0.15,
            "acquaintance": 0.1,
            "business": 0.05
        }
        
        for i in range(count):
            relationship = random.choices(
                list(relationship_weights.keys()),
                list(relationship_weights.values())
            )[0]
            
            contact = {
                "id": self._generate_id(),
                "first_name": self.fake.first_name(),
                "last_name": self.fake.last_name(),
                "display_name": "",
                "phone_numbers": [
                    {
                        "label": "mobile",
                        "number": self.fake.phone_number()
                    }
                ],
                "email_addresses": [
                    {
                        "label": "home" if relationship in ["friend", "family"] else "work",
                        "email": self.fake.email()
                    }
                ],
                "addresses": [],
                "organization": self.fake.company() if relationship in ["colleague", "business"] else "",
                "job_title": self.fake.job() if relationship in ["colleague", "business"] else "",
                "birthday": self.fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%Y-%m-%d"),
                "notes": "",
                "relationship": relationship,
                "created_date": self._generate_realistic_timestamp()
            }
            
            # Set display name
            contact["display_name"] = f"{contact['first_name']} {contact['last_name']}"
            
            # Sometimes add address for close relationships
            if relationship in ["family", "friend"] and random.random() < 0.3:
                contact["addresses"] = [
                    {
                        "label": "home",
                        "street": self.fake.street_address(),
                        "city": self.fake.city(),
                        "state": self.fake.state(),
                        "postal_code": self.fake.postcode(),
                        "country": "United States"
                    }
                ]
            
            # Add work phone for colleagues
            if relationship == "colleague" and random.random() < 0.5:
                contact["phone_numbers"].append({
                    "label": "work",
                    "number": self.fake.phone_number()
                })
            
            contacts.append(contact)
        
        return contacts