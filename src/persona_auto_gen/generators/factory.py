"""Factory for creating data generators."""

from typing import Dict, Type
from ..config import Config
from .base import BaseGenerator
from .contacts import ContactsGenerator
from .calendar import CalendarGenerator
from .sms import SMSGenerator
from .emails import EmailsGenerator
from .reminders import RemindersGenerator
from .notes import NotesGenerator
from .wallet import WalletGenerator
from .alarms import AlarmsGenerator


class GeneratorFactory:
    """Factory class for creating appropriate data generators."""
    
    _generators: Dict[str, Type[BaseGenerator]] = {
        "contacts": ContactsGenerator,
        "calendar": CalendarGenerator,
        "sms": SMSGenerator,
        "emails": EmailsGenerator,
        "reminders": RemindersGenerator,
        "notes": NotesGenerator,
        "wallet": WalletGenerator,
        "alarms": AlarmsGenerator
    }
    
    def __init__(self, config: Config):
        self.config = config
        self._generator_instances: Dict[str, BaseGenerator] = {}
    
    def get_generator(self, app_name: str) -> BaseGenerator:
        """Get a generator instance for the specified app."""
        if app_name not in self._generators:
            raise ValueError(f"No generator available for app: {app_name}")
        
        # Cache generator instances
        if app_name not in self._generator_instances:
            generator_class = self._generators[app_name]
            self._generator_instances[app_name] = generator_class(self.config)
        
        return self._generator_instances[app_name]
    
    def get_available_generators(self) -> list[str]:
        """Get list of available generator names."""
        return list(self._generators.keys())
    
    def register_generator(self, app_name: str, generator_class: Type[BaseGenerator]):
        """Register a new generator class."""
        self._generators[app_name] = generator_class
        # Clear cached instance if exists
        if app_name in self._generator_instances:
            del self._generator_instances[app_name]