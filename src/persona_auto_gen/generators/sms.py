"""SMS data generator."""

from typing import Dict, List, Any
import logging
import random
from datetime import datetime, timedelta
from faker import Faker

from .base import BaseGenerator

logger = logging.getLogger(__name__)


class SMSGenerator(BaseGenerator):
    """Generator for iPhone SMS/Messages app data."""
    
    def __init__(self, config):
        super().__init__(config)
        self.fake = Faker()
        
    def _get_app_name(self) -> str:
        return "conversations"
    
    def generate(self, user_profile: Dict[str, Any], events: List[str], 
                analysis: Dict[str, Any], count: int) -> Dict[str, Any]:
        """Generate realistic SMS conversations."""
        logger.info(f"Generating {count} SMS conversations")
        
        try:
            # Create generation prompt
            prompt = self._create_generation_prompt(user_profile, events, analysis, count)
            
            # Generate with LLM
            response = self._generate_with_llm(prompt)
            
            # Parse response
            generated_data = self._parse_json_response(response)
            
            # Clean and validate
            cleaned_data = self._clean_and_validate_data(generated_data)
            
            # Ensure we have the right number of conversations
            conversations = cleaned_data.get("conversations", [])
            if len(conversations) < count and self.config.use_faker_fallback:
                additional_needed = count - len(conversations)
                fallback_conversations = self._generate_fallback_conversations(
                    additional_needed, user_profile, events
                )
                conversations.extend(fallback_conversations)
            
            return {"conversations": conversations[:count]}
            
        except Exception as e:
            logger.error(f"SMS generation failed: {str(e)}")
            if self.config.use_faker_fallback:
                return {"conversations": self._generate_fallback_conversations(count, user_profile, events)}
            return {"conversations": []}
    
    def _get_app_specific_instructions(self) -> str:
        """Return SMS-specific generation instructions."""
        return """
Please generate SMS conversation data in the following JSON format:
{
    "conversations": [
        {
            "conversation_id": "unique_identifier",
            "participants": [
                {
                    "phone_number": "+1234567890",
                    "contact_name": "Contact Name"
                }
            ],
            "messages": [
                {
                    "id": "unique_identifier",
                    "sender_phone": "+1234567890",
                    "is_from_user": true/false,
                    "content": "Message content",
                    "timestamp": "ISO timestamp",
                    "message_type": "text|image|video|audio|location|contact|other",
                    "delivery_status": "sent|delivered|read|failed",
                    "attachments": [
                        {
                            "type": "image|video|audio|document|location|contact",
                            "filename": "file.jpg",
                            "size_bytes": 1024,
                            "mime_type": "image/jpeg"
                        }
                    ],
                    "read_receipt": true/false,
                    "group_info": {
                        "is_group": false,
                        "group_name": "Group Name",
                        "group_id": "group_id"
                    }
                }
            ]
        }
    ]
}

Create realistic conversations that:
- Show natural messaging patterns and conversation flow
- Include both individual and group conversations
- Relate to the provided events and user profile
- Mix different message types (text, images, etc.)
- Show realistic timing and response patterns
- Include casual, work, and family communication styles
- Have messages flowing both ways (sent and received)
"""
    
    def _generate_fallback_conversations(self, count: int, user_profile: Dict[str, Any], 
                                       provided_events: List[str]) -> List[Dict[str, Any]]:
        """Generate fallback SMS conversations using templates."""
        conversations = []
        
        conversation_types = {
            "family": 0.3,
            "friend": 0.4,
            "work": 0.2,
            "group": 0.1
        }
        
        for i in range(count):
            conv_type = random.choices(
                list(conversation_types.keys()),
                list(conversation_types.values())
            )[0]
            
            conversation = self._create_conversation(conv_type, i)
            conversations.append(conversation)
        
        return conversations
    
    def _create_conversation(self, conv_type: str, index: int) -> Dict[str, Any]:
        """Create a single conversation."""
        conversation_id = f"conv_{self._generate_id()}_{index}"
        
        if conv_type == "group":
            participants = self._generate_group_participants()
            messages = self._generate_group_messages(participants)
        else:
            participant = self._generate_single_participant(conv_type)
            participants = [participant]
            messages = self._generate_individual_messages(participant, conv_type)
        
        return {
            "conversation_id": conversation_id,
            "participants": participants,
            "messages": messages
        }
    
    def _generate_single_participant(self, conv_type: str) -> Dict[str, Any]:
        """Generate a single conversation participant."""
        if conv_type == "family":
            names = ["Mom", "Dad", "Sister", "Brother", "Grandma", "Uncle", "Aunt"]
            name = random.choice(names)
        elif conv_type == "work":
            name = f"{self.fake.first_name()} {self.fake.last_name()}"
        else:  # friend
            name = self.fake.first_name()
        
        return {
            "phone_number": self.fake.phone_number(),
            "contact_name": name
        }
    
    def _generate_group_participants(self) -> List[Dict[str, Any]]:
        """Generate group conversation participants."""
        num_participants = random.randint(3, 6)
        participants = []
        
        for _ in range(num_participants):
            participants.append({
                "phone_number": self.fake.phone_number(),
                "contact_name": self.fake.first_name()
            })
        
        return participants
    
    def _generate_individual_messages(self, participant: Dict[str, Any], 
                                    conv_type: str) -> List[Dict[str, Any]]:
        """Generate messages for individual conversation."""
        num_messages = random.randint(3, 15)
        messages = []
        
        message_templates = self._get_message_templates(conv_type)
        user_phone = "+1555000000"  # User's phone number
        
        current_time = self.fake.date_time_between(
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )
        
        for i in range(num_messages):
            is_from_user = random.choice([True, False])
            sender_phone = user_phone if is_from_user else participant["phone_number"]
            
            # Select message content
            if is_from_user:
                content = random.choice(message_templates["user_messages"])
            else:
                content = random.choice(message_templates["other_messages"])
            
            message = {
                "id": f"msg_{self._generate_id()}_{i}",
                "sender_phone": sender_phone,
                "is_from_user": is_from_user,
                "content": content,
                "timestamp": current_time.isoformat(),
                "message_type": "text",
                "delivery_status": "read",
                "attachments": [],
                "read_receipt": True,
                "group_info": {
                    "is_group": False
                }
            }
            
            # Sometimes add attachments
            if random.random() < 0.1:
                message["attachments"] = self._generate_attachments()
                message["message_type"] = message["attachments"][0]["type"]
            
            messages.append(message)
            
            # Increment time for next message
            current_time += timedelta(minutes=random.randint(1, 120))
        
        return messages
    
    def _generate_group_messages(self, participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate messages for group conversation."""
        num_messages = random.randint(5, 20)
        messages = []
        
        user_phone = "+1555000000"
        group_id = f"group_{self._generate_id()}"
        group_name = f"{participants[0]['contact_name']}, {participants[1]['contact_name']} and others"
        
        current_time = self.fake.date_time_between(
            start_date=self.config.start_date,
            end_date=self.config.end_date
        )
        
        group_templates = [
            "Hey everyone!",
            "What time are we meeting?",
            "I'll be there in 10 minutes",
            "Can we reschedule?",
            "Thanks for organizing this",
            "See you all there!",
            "Running late, sorry",
            "Great idea!",
            "Count me in",
            "I can't make it today"
        ]
        
        for i in range(num_messages):
            # Choose random sender (could be user or any participant)
            all_senders = [user_phone] + [p["phone_number"] for p in participants]
            sender_phone = random.choice(all_senders)
            is_from_user = sender_phone == user_phone
            
            message = {
                "id": f"msg_{self._generate_id()}_{i}",
                "sender_phone": sender_phone,
                "is_from_user": is_from_user,
                "content": random.choice(group_templates),
                "timestamp": current_time.isoformat(),
                "message_type": "text",
                "delivery_status": "read",
                "attachments": [],
                "read_receipt": True,
                "group_info": {
                    "is_group": True,
                    "group_name": group_name,
                    "group_id": group_id
                }
            }
            
            messages.append(message)
            current_time += timedelta(minutes=random.randint(1, 60))
        
        return messages
    
    def _get_message_templates(self, conv_type: str) -> Dict[str, List[str]]:
        """Get message templates based on conversation type."""
        templates = {
            "family": {
                "user_messages": [
                    "Hey! How are you doing?",
                    "Can you pick up some groceries?",
                    "I'll be home late tonight",
                    "Thanks for dinner!",
                    "Love you too",
                    "I'm running late",
                    "See you at the family dinner",
                    "Happy birthday!",
                    "Miss you",
                    "Call me when you get a chance"
                ],
                "other_messages": [
                    "Hi sweetie!",
                    "Of course, what do you need?",
                    "No problem, drive safe",
                    "You're welcome!",
                    "Love you",
                    "No worries",
                    "Looking forward to it",
                    "Thank you so much!",
                    "Miss you too",
                    "Will call you later"
                ]
            },
            "friend": {
                "user_messages": [
                    "What's up?",
                    "Want to hang out later?",
                    "Did you see that movie?",
                    "LOL that's hilarious",
                    "I'm so tired",
                    "Coffee tomorrow?",
                    "Thanks for the help!",
                    "Can't wait for the weekend",
                    "How was your day?",
                    "Let's do this!"
                ],
                "other_messages": [
                    "Not much, you?",
                    "Sure! What time?",
                    "Yes! It was amazing",
                    "I know right! 😂",
                    "Same here",
                    "Absolutely! 10am?",
                    "Anytime!",
                    "Me too!",
                    "Pretty good, thanks!",
                    "I'm in!"
                ]
            },
            "work": {
                "user_messages": [
                    "Can we schedule a meeting?",
                    "I sent the report",
                    "Running a few minutes late",
                    "Thanks for the update",
                    "I'll get that done today",
                    "Can you review this?",
                    "Meeting went well",
                    "I'll follow up on that",
                    "Have a great weekend!",
                    "Let me know if you need anything"
                ],
                "other_messages": [
                    "Sure, when works for you?",
                    "Got it, thanks!",
                    "No problem",
                    "You're welcome",
                    "Sounds good",
                    "Will do",
                    "Great to hear",
                    "Perfect",
                    "You too!",
                    "Will reach out if needed"
                ]
            }
        }
        
        return templates.get(conv_type, templates["friend"])
    
    def _generate_attachments(self) -> List[Dict[str, Any]]:
        """Generate message attachments."""
        attachment_types = ["image", "video", "audio", "document"]
        attachment_type = random.choice(attachment_types)
        
        mime_types = {
            "image": "image/jpeg",
            "video": "video/mp4",
            "audio": "audio/mp3",
            "document": "application/pdf"
        }
        
        filenames = {
            "image": f"IMG_{random.randint(1000, 9999)}.jpg",
            "video": f"VID_{random.randint(1000, 9999)}.mp4",
            "audio": f"AUD_{random.randint(1000, 9999)}.mp3",
            "document": f"DOC_{random.randint(1000, 9999)}.pdf"
        }
        
        return [{
            "type": attachment_type,
            "filename": filenames[attachment_type],
            "size_bytes": random.randint(1024, 10485760),  # 1KB to 10MB
            "mime_type": mime_types[attachment_type]
        }]