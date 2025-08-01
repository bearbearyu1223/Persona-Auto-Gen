"""Notes data generator."""

from typing import Dict, List, Any
import logging
import random
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class NotesGenerator(BaseGenerator):
    """Generator for iPhone Notes app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "notes"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic notes data."""
        logger.info(f"Generating {count} notes")
        
        try:
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            response = self._generate_with_llm(prompt)
            generated_data = self._parse_json_response(response)
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            notes = cleaned_data.get("notes", [])
            if len(notes) < count and self.config.use_faker_fallback:
                additional_needed = count - len(notes)
                fallback_notes = self._generate_fallback_notes(
                    additional_needed, user_profile, events
                )
                notes.extend(fallback_notes)
            
            return {"notes": notes[:count]}
            
        except Exception as e:
            logger.error(f"Notes generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"notes": self._generate_fallback_notes(count, user_profile, events)}
            return {"notes": []}
    
    def _get_app_specific_instructions(self) -> str:
        return """
Generate realistic notes including meeting notes, personal thoughts, 
shopping lists, ideas, and other typical note-taking scenarios.
"""
    
    def _generate_fallback_notes(self, count: int, user_profile: Dict[str, Any], 
                                events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback notes using templates."""
        notes = []
        
        note_templates = {
            "personal": ["Random thoughts", "Weekend plans", "Book recommendations", "Recipe ideas"],
            "work": ["Meeting notes", "Project ideas", "Action items", "Brain dump"],
            "ideas": ["App idea", "Business concept", "Creative project", "Innovation"],
            "shopping": ["Grocery list", "Gift ideas", "Wishlist", "Items to buy"]
        }
        
        for i in range(count):
            category = random.choice(list(note_templates.keys()))
            title = random.choice(note_templates[category])
            
            note = {
                "id": f"note_{self._generate_id()}_{i}",
                "title": title,
                "content": self._generate_note_content(title, category),
                "folder": category.title(),
                "category": category,
                "tags": [category],
                "created_date": self._generate_realistic_timestamp(),
                "modified_date": self._generate_realistic_timestamp(),
                "pinned": random.random() < 0.1,
                "locked": False,
                "shared": False,
                "attachments": [],
                "checklist": {"is_checklist": category == "shopping"},
                "formatting": {"has_formatting": False, "style": "plain"}
            }
            
            if category == "shopping":
                note["checklist"]["items"] = self._generate_checklist_items()
            
            notes.append(note)
        
        return notes
    
    def _generate_note_content(self, title: str, category: str) -> str:
        contents = {
            "personal": f"Personal thoughts about {title.lower()}. Need to think more about this.",
            "work": f"Notes from {title.lower()}. Key points to remember and follow up on.",
            "ideas": f"New idea: {title.lower()}. This could be interesting to explore further.",
            "shopping": "Items to buy:\n• Milk\n• Bread\n• Eggs\n• Apples"
        }
        return contents.get(category, f"Notes about {title}")
    
    def _generate_checklist_items(self) -> List[Dict[str, Any]]:
        items = ["Milk", "Bread", "Eggs", "Apples", "Bananas"]
        return [
            {
                "id": f"item_{i}",
                "text": item,
                "completed": random.choice([True, False])
            }
            for i, item in enumerate(items)
        ]