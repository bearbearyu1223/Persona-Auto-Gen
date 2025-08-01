"""Tests for data generators."""

import pytest
from unittest.mock import Mock, patch
import json

from persona_auto_gen.generators.factory import GeneratorFactory
from persona_auto_gen.generators.base import BaseGenerator
from persona_auto_gen.generators.contacts import ContactsGenerator
from persona_auto_gen.generators.calendar import CalendarGenerator
from persona_auto_gen.generators.sms import SMSGenerator
from persona_auto_gen.generators.emails import EmailsGenerator
from persona_auto_gen.generators.reminders import RemindersGenerator
from persona_auto_gen.generators.notes import NotesGenerator
from persona_auto_gen.generators.wallet import WalletGenerator


class TestGeneratorFactory:
    """Test the GeneratorFactory class."""
    
    def test_factory_creation(self, test_config):
        """Test creating generator factory."""
        factory = GeneratorFactory(test_config)
        assert factory.config == test_config
    
    def test_get_available_generators(self, test_config):
        """Test getting available generator names."""
        factory = GeneratorFactory(test_config)
        generators = factory.get_available_generators()
        
        expected_generators = ["contacts", "calendar", "sms", "emails", "reminders", "notes", "wallet", "alarms"]
        assert set(generators) == set(expected_generators)
    
    def test_get_generator_contacts(self, test_config):
        """Test getting contacts generator."""
        factory = GeneratorFactory(test_config)
        generator = factory.get_generator("contacts")
        
        assert isinstance(generator, ContactsGenerator)
        assert generator.config == test_config
    
    def test_get_generator_calendar(self, test_config):
        """Test getting calendar generator."""
        factory = GeneratorFactory(test_config)
        generator = factory.get_generator("calendar")
        
        assert isinstance(generator, CalendarGenerator)
    
    
    def test_get_generator_invalid(self, test_config):
        """Test getting invalid generator."""
        factory = GeneratorFactory(test_config)
        
        with pytest.raises(ValueError, match="No generator available for app"):
            factory.get_generator("invalid_app")
    
    def test_generator_caching(self, test_config):
        """Test that generators are cached."""
        factory = GeneratorFactory(test_config)
        
        generator1 = factory.get_generator("contacts")
        generator2 = factory.get_generator("contacts")
        
        assert generator1 is generator2  # Same instance
    
    def test_register_custom_generator(self, test_config):
        """Test registering a custom generator."""
        factory = GeneratorFactory(test_config)
        
        class CustomGenerator(BaseGenerator):
            def _get_app_name(self):
                return "custom"
            
            def generate(self, user_profile, events, analysis, count):
                return {"custom": []}
            
            def _get_app_specific_instructions(self):
                return "Custom instructions"
        
        factory.register_generator("custom", CustomGenerator)
        
        assert "custom" in factory.get_available_generators()
        generator = factory.get_generator("custom")
        assert isinstance(generator, CustomGenerator)


class TestBaseGenerator:
    """Test the BaseGenerator abstract class."""
    
    def test_base_generator_abstract(self, test_config):
        """Test that BaseGenerator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseGenerator(test_config)
    
    def test_generate_id(self, test_config):
        """Test ID generation."""
        generator = ContactsGenerator(test_config)
        
        id1 = generator._generate_id()
        id2 = generator._generate_id()
        
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
        assert "contacts" in id1
    
    def test_generate_realistic_timestamp(self, test_config):
        """Test timestamp generation."""
        generator = ContactsGenerator(test_config)
        
        timestamp = generator._generate_realistic_timestamp()
        
        assert isinstance(timestamp, str)
        # Should be ISO format
        assert "T" in timestamp
        assert len(timestamp.split("T")) == 2
    
    def test_relate_to_events(self, test_config, sample_events):
        """Test relating data to events."""
        generator = ContactsGenerator(test_config)
        
        related_events = generator._relate_to_events(sample_events, 10)
        
        assert isinstance(related_events, list)
        assert len(related_events) <= len(sample_events)
        assert all(event in sample_events for event in related_events)


class TestContactsGenerator:
    """Test the ContactsGenerator class."""
    
    def test_contacts_generator_creation(self, test_config):
        """Test creating contacts generator."""
        generator = ContactsGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "contacts"
    
    @patch('persona_auto_gen.generators.base.BaseGenerator._generate_with_llm')
    def test_contacts_generation_success(self, mock_llm, test_config, sample_user_profile, sample_events):
        """Test successful contacts generation."""
        # Mock LLM response
        mock_response = json.dumps({
            "contacts": [
                {
                    "id": "contact_1",
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": "John Doe",
                    "phone_numbers": [{"label": "mobile", "number": "+1234567890"}],
                    "email_addresses": [{"label": "home", "email": "john@example.com"}],
                    "addresses": [],
                    "relationship": "friend",
                    "created_date": "2024-01-15T10:00:00"
                }
            ]
        })
        mock_llm.return_value = mock_response
        
        generator = ContactsGenerator(test_config)
        result = generator.generate(sample_user_profile, sample_events, {}, 1)
        
        assert "contacts" in result
        assert len(result["contacts"]) == 1
        assert result["contacts"][0]["first_name"] == "John"
    
    @patch('persona_auto_gen.generators.base.BaseGenerator._generate_with_llm')
    def test_contacts_generation_fallback(self, mock_llm, test_config, sample_user_profile, sample_events):
        """Test contacts generation with fallback."""
        # Mock LLM failure
        mock_llm.side_effect = Exception("API Error")
        
        generator = ContactsGenerator(test_config)
        result = generator.generate(sample_user_profile, sample_events, {}, 2)
        
        assert "contacts" in result
        assert len(result["contacts"]) == 2  # Fallback should generate requested count
        
        # Check fallback data structure
        contact = result["contacts"][0]
        assert "id" in contact
        assert "first_name" in contact
        assert "last_name" in contact
        assert "relationship" in contact
    
    def test_generate_fallback_contacts(self, test_config, sample_user_profile, sample_events):
        """Test fallback contact generation."""
        generator = ContactsGenerator(test_config)
        
        contacts = generator._generate_fallback_contacts(3, sample_user_profile, sample_events)
        
        assert len(contacts) == 3
        
        for contact in contacts:
            assert "id" in contact
            assert "first_name" in contact
            assert "last_name" in contact
            assert "display_name" in contact
            assert "relationship" in contact
            assert "created_date" in contact
            assert contact["relationship"] in ["friend", "colleague", "family", "acquaintance", "business"]


class TestCalendarGenerator:
    """Test the CalendarGenerator class."""
    
    def test_calendar_generator_creation(self, test_config):
        """Test creating calendar generator."""
        generator = CalendarGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "events"
    
    def test_generate_event_start_time(self, test_config):
        """Test event start time generation."""
        generator = CalendarGenerator(test_config)
        
        work_time = generator._generate_event_start_time("work")
        social_time = generator._generate_event_start_time("social")
        
        # Work events should be during business hours
        assert 9 <= work_time.hour <= 17
        
        # Social events typically evening or weekend
        assert isinstance(social_time.hour, int)
    
    def test_get_event_duration(self, test_config):
        """Test event duration calculation."""
        generator = CalendarGenerator(test_config)
        
        work_duration = generator._get_event_duration("work")
        social_duration = generator._get_event_duration("social")
        
        assert isinstance(work_duration, float)
        assert isinstance(social_duration, float)
        assert work_duration > 0
        assert social_duration > 0


class TestSMSGenerator:
    """Test the SMSGenerator class."""
    
    def test_sms_generator_creation(self, test_config):
        """Test creating SMS generator."""
        generator = SMSGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "conversations"
    
    def test_generate_single_participant(self, test_config):
        """Test generating single participant."""
        generator = SMSGenerator(test_config)
        
        family_participant = generator._generate_single_participant("family")
        work_participant = generator._generate_single_participant("work")
        
        assert "phone_number" in family_participant
        assert "contact_name" in family_participant
        assert "phone_number" in work_participant
        assert "contact_name" in work_participant
    
    def test_generate_group_participants(self, test_config):
        """Test generating group participants."""
        generator = SMSGenerator(test_config)
        
        participants = generator._generate_group_participants()
        
        assert isinstance(participants, list)
        assert 3 <= len(participants) <= 6
        
        for participant in participants:
            assert "phone_number" in participant
            assert "contact_name" in participant


class TestEmailsGenerator:
    """Test the EmailsGenerator class."""
    
    def test_emails_generator_creation(self, test_config):
        """Test creating emails generator."""
        generator = EmailsGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "emails"
    
    def test_generate_subject(self, test_config):
        """Test subject generation."""
        generator = EmailsGenerator(test_config)
        
        work_subject = generator._generate_subject("work")
        personal_subject = generator._generate_subject("personal")
        
        assert isinstance(work_subject, str)
        assert isinstance(personal_subject, str)
        assert len(work_subject) > 0
        assert len(personal_subject) > 0


class TestRemindersGenerator:
    """Test the RemindersGenerator class."""
    
    def test_reminders_generator_creation(self, test_config):
        """Test creating reminders generator."""
        generator = RemindersGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "reminders"


class TestNotesGenerator:
    """Test the NotesGenerator class."""
    
    def test_notes_generator_creation(self, test_config):
        """Test creating notes generator."""
        generator = NotesGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "notes"
    
    def test_generate_note_content(self, test_config):
        """Test note content generation."""
        generator = NotesGenerator(test_config)
        
        content = generator._generate_note_content("Meeting Notes", "work")
        
        assert isinstance(content, str)
        assert len(content) > 0


class TestWalletGenerator:
    """Test the WalletGenerator class."""
    
    def test_wallet_generator_creation(self, test_config):
        """Test creating wallet generator."""
        generator = WalletGenerator(test_config)
        
        assert generator.config == test_config
        assert generator._get_app_name() == "passes"
    
    def test_get_organization_name(self, test_config):
        """Test organization name generation."""
        generator = WalletGenerator(test_config)
        
        boarding_org = generator._get_organization_name("boarding_pass")
        store_org = generator._get_organization_name("store_card")
        
        assert isinstance(boarding_org, str)
        assert isinstance(store_org, str)
        assert len(boarding_org) > 0
        assert len(store_org) > 0


