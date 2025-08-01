"""Wallet data generator."""

from typing import Dict, List, Any
import logging
import random
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class WalletGenerator(BaseGenerator):
    """Generator for iPhone Wallet app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "passes"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic wallet passes data."""
        logger.info(f"Generating {count} wallet passes")
        
        try:
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            response = self._generate_with_llm(prompt)
            generated_data = self._parse_json_response(response)
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            passes = cleaned_data.get("passes", [])
            if len(passes) < count and self.config.use_faker_fallback:
                additional_needed = count - len(passes)
                fallback_passes = self._generate_fallback_passes(
                    additional_needed, user_profile, events
                )
                passes.extend(fallback_passes)
            
            return {"passes": passes[:count]}
            
        except Exception as e:
            logger.error(f"Wallet generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"passes": self._generate_fallback_passes(count, user_profile, events)}
            return {"passes": []}
    
    def _get_app_specific_instructions(self) -> str:
        return """
Generate realistic wallet passes including boarding passes, event tickets,
store cards, membership cards, and coupons with appropriate metadata.
"""
    
    def _generate_fallback_passes(self, count: int, user_profile: Dict[str, Any], 
                                 events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback wallet passes using templates."""
        passes = []
        
        pass_types = ["boarding_pass", "event_ticket", "store_card", "membership", "coupon"]
        
        for i in range(count):
            pass_type = random.choice(pass_types)
            
            pass_data = {
                "id": f"pass_{self._generate_id()}_{i}",
                "type": pass_type,
                "organization_name": self._get_organization_name(pass_type),
                "pass_name": self._get_pass_name(pass_type),
                "description": f"{pass_type.replace('_', ' ').title()} pass",
                "background_color": "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)]),
                "foreground_color": "#FFFFFF",
                "primary_fields": self._get_primary_fields(pass_type),
                "secondary_fields": self._get_secondary_fields(pass_type),
                "barcode": {
                    "format": "QR",
                    "message": f"PASS{random.randint(100000, 999999)}",
                    "message_encoding": "utf-8"
                },
                "created_date": self._generate_realistic_timestamp(),
                "voided": False
            }
            
            passes.append(pass_data)
        
        return passes
    
    def _get_organization_name(self, pass_type: str) -> str:
        orgs = {
            "boarding_pass": random.choice(["American Airlines", "Delta", "United"]),
            "event_ticket": random.choice(["Madison Square Garden", "Staples Center", "Local Theater"]),
            "store_card": random.choice(["Starbucks", "Target", "Best Buy"]),
            "membership": random.choice(["Gym Plus", "Library Card", "Museum Pass"]),
            "coupon": random.choice(["McDonald's", "Pizza Hut", "Local Restaurant"])
        }
        return orgs.get(pass_type, "Generic Company")
    
    def _get_pass_name(self, pass_type: str) -> str:
        names = {
            "boarding_pass": "Flight Boarding Pass",
            "event_ticket": "Concert Ticket", 
            "store_card": "Loyalty Card",
            "membership": "Membership Card",
            "coupon": "Discount Coupon"
        }
        return names.get(pass_type, "Generic Pass")
    
    def _get_primary_fields(self, pass_type: str) -> List[Dict[str, str]]:
        fields = {
            "boarding_pass": [{"label": "Flight", "value": f"AA{random.randint(100, 999)}", "key": "flight"}],
            "event_ticket": [{"label": "Event", "value": "Concert", "key": "event"}],
            "store_card": [{"label": "Points", "value": str(random.randint(100, 5000)), "key": "points"}],
            "membership": [{"label": "Member", "value": "Gold", "key": "level"}],
            "coupon": [{"label": "Discount", "value": "20% OFF", "key": "discount"}]
        }
        return fields.get(pass_type, [])
    
    def _get_secondary_fields(self, pass_type: str) -> List[Dict[str, str]]:
        fields = {
            "boarding_pass": [{"label": "Gate", "value": f"{random.choice('ABCD')}{random.randint(1, 30)}", "key": "gate"}],
            "event_ticket": [{"label": "Seat", "value": f"Row {random.randint(1, 20)}", "key": "seat"}],
            "store_card": [{"label": "Member Since", "value": "2020", "key": "since"}],
            "membership": [{"label": "Expires", "value": "2025-12-31", "key": "expires"}],
            "coupon": [{"label": "Expires", "value": "2024-12-31", "key": "expires"}]
        }
        return fields.get(pass_type, [])