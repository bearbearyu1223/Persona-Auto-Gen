"""Individual workflow nodes for the persona generation process."""

from typing import Dict, List, Any
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from ..config import Config
from ..generators import GeneratorFactory
from ..utils.validation import SchemaValidator
from ..utils.llm_client import LLMClient
from ..utils.output_manager import OutputManager

logger = logging.getLogger(__name__)


class BaseNode:
    """Base class for workflow nodes."""
    
    def __init__(self, config: Config):
        self.config = config
        self.llm_client = LLMClient(config)
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Run the node logic."""
        raise NotImplementedError("Subclasses must implement run method")


class ProfileAnalysisNode(BaseNode):
    """Analyzes user profile and events to inform data generation."""
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the user profile and events."""
        logger.info("Starting profile analysis")
        state["current_step"] = "profile_analysis"
        
        try:
            user_profile = state["user_profile"]
            events = state["events"]
            config = state["config"]
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(user_profile, events, config)
            
            # Get analysis from LLM
            analysis_response = self.llm_client.generate(
                prompt=analysis_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the analysis
            analysis = self._parse_analysis(analysis_response)
            
            state["analysis"] = analysis
            logger.info("Profile analysis completed successfully")
            
        except Exception as e:
            error_msg = f"Profile analysis failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["analysis"] = {"error": error_msg}
        
        return state
    
    def _create_analysis_prompt(self, user_profile: Dict[str, Any], events: List[str], config: Config) -> str:
        """Create the prompt for profile analysis."""
        events_text = "\n".join(f"- {event}" for event in events)
        
        return f"""
Analyze the following user profile and events to inform realistic iPhone app data generation.

USER PROFILE:
{json.dumps(user_profile, indent=2)}

EVENTS:
{events_text}

TIME PERIOD: {config.start_date.strftime('%Y-%m-%d')} to {config.end_date.strftime('%Y-%m-%d')}

Please provide a comprehensive analysis in JSON format with the following structure:
{{
    "user_identity": {{
        "first_name": "realistic first name based on age/location/profile",
        "middle_name": "realistic middle name (can be null)",
        "last_name": "realistic last name",
        "gender": "male|female|non-binary"
    }},
    "user_characteristics": {{
        "lifestyle": "brief description",
        "communication_patterns": "how they likely communicate",
        "technology_usage": "their relationship with technology",
        "social_connections": "types of relationships they maintain",
        "professional_context": "work-related patterns"
    }},
    "event_analysis": {{
        "event_types": ["list of event categories"],
        "recurring_patterns": ["weekly meetings", "monthly events", etc.],
        "seasonal_activities": ["events tied to specific times"],
        "social_implications": ["how events affect relationships"]
    }},
    "app_usage_patterns": {{
        "contacts": "expected contact management behavior",
        "calendar": "scheduling and event management style", 
        "sms": "texting habits and communication style",
        "emails": "email usage patterns and formality",
        "reminders": "task management and reminder preferences",
        "notes": "note-taking habits and organization",
        "wallet": "digital payment and pass usage"
    }},
    "data_relationships": {{
        "cross_app_connections": "how data should connect across apps",
        "event_triggers": "what events should trigger what data",
        "timeline_coherence": "how to maintain temporal consistency"
    }}
}}

Ensure the analysis is detailed and considers realistic human behavior patterns.
"""
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse the LLM analysis response."""
        try:
            # Try to extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: create basic analysis structure
                return {
                    "user_identity": {"first_name": "Alex", "middle_name": None, "last_name": "Smith", "gender": "non-binary"},
                    "user_characteristics": {"lifestyle": "moderate technology user"},
                    "event_analysis": {"event_types": ["personal", "work"]},
                    "app_usage_patterns": {},
                    "data_relationships": {"cross_app_connections": "basic connections"}
                }
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse analysis JSON, using fallback")
            return {
                "user_identity": {"first_name": "Alex", "middle_name": None, "last_name": "Smith", "gender": "non-binary"},
                "user_characteristics": {"lifestyle": "moderate technology user"},
                "event_analysis": {"event_types": ["personal", "work"]},
                "app_usage_patterns": {},
                "data_relationships": {"cross_app_connections": "basic connections"}
            }


class DataGenerationNode(BaseNode):
    """Generates synthetic data for all iPhone apps."""
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate data for all configured apps."""
        logger.info("Starting data generation")
        state["current_step"] = "data_generation"
        
        try:
            config = state["config"]
            user_profile = state["user_profile"]
            events = state["events"]
            analysis = state["analysis"]
            
            generated_data = {}
            generator_factory = GeneratorFactory(config)
            
            # Generate data for each app
            for app_name in config.enabled_apps:
                data_volume = config.data_volume.get(app_name, 10)
                
                # Skip generation if data_volume is 0
                if data_volume == 0:
                    logger.info(f"Skipping {app_name} data generation (data_volume is 0)")
                    generated_data[app_name] = {}
                    continue
                
                logger.info(f"Generating {app_name} data")
                
                try:
                    generator = generator_factory.get_generator(app_name)
                    app_data = generator.generate(
                        user_profile=user_profile,
                        events=events,
                        analysis=analysis,
                        count=data_volume
                    )
                    generated_data[app_name] = app_data
                    logger.info(f"Generated {len(app_data.get(app_name, []))} {app_name} entries")
                    
                except Exception as e:
                    error_msg = f"Failed to generate {app_name} data: {str(e)}"
                    logger.error(error_msg)
                    state["errors"].append(error_msg)
                    generated_data[app_name] = {}
            
            state["generated_data"] = generated_data
            logger.info("Data generation completed")
            
        except Exception as e:
            error_msg = f"Data generation failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["generated_data"] = {}
        
        return state


class ValidationNode(BaseNode):
    """Validates generated data against JSON schemas."""
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all generated data."""
        logger.info("Starting data validation")
        state["current_step"] = "validation"
        
        try:
            generated_data = state["generated_data"]
            validator = SchemaValidator()
            validation_results = {}
            
            for app_name, app_data in generated_data.items():
                # Skip validation if data_volume is 0 or data is empty
                data_volume = state["config"].data_volume.get(app_name, 10)
                if data_volume == 0:
                    logger.info(f"Skipping {app_name} data validation (data_volume is 0)")
                    continue
                    
                if app_data:  # Skip empty data
                    logger.info(f"Validating {app_name} data")
                    results = validator.validate_app_data(app_name, app_data)
                    validation_results[app_name] = results
                    
                    if results["is_valid"]:
                        logger.info(f"{app_name} data validation passed")
                    else:
                        logger.warning(f"{app_name} data validation failed: {results['errors']}")
            
            state["validation_results"] = validation_results
            logger.info("Data validation completed")
            
        except Exception as e:
            error_msg = f"Data validation failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["validation_results"] = {}
        
        return state


class ReflectionNode(BaseNode):
    """Reflects on the quality and realism of generated data."""
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform quality reflection on generated data."""
        logger.info("Starting quality reflection")
        state["current_step"] = "reflection"
        
        try:
            generated_data = state["generated_data"]
            analysis = state["analysis"]
            user_profile = state["user_profile"]
            events = state["events"]
            config = state["config"]
            
            # Filter out apps with data_volume = 0 for reflection
            filtered_data = {}
            for app_name, app_data in generated_data.items():
                data_volume = config.data_volume.get(app_name, 10)
                if data_volume > 0 and app_data:
                    filtered_data[app_name] = app_data
            
            # Skip reflection if no apps have data
            if not filtered_data:
                logger.info("Skipping quality reflection (no apps with data_volume > 0)")
                state["reflection_results"] = {
                    "overall_quality": "skipped",
                    "realism_score": 0,
                    "diversity_score": 0,
                    "coherence_score": 0,
                    "strengths": [],
                    "weaknesses": [],
                    "recommendations": [],
                    "critical_issues": []
                }
                return state
            
            # Create reflection prompt
            reflection_prompt = self._create_reflection_prompt(
                filtered_data, analysis, user_profile, events
            )
            
            # Get reflection from LLM
            reflection_response = self.llm_client.generate(
                prompt=reflection_prompt,
                temperature=0.2,
                max_tokens=1500
            )
            
            # Parse reflection results
            reflection_results = self._parse_reflection(reflection_response)
            
            state["reflection_results"] = reflection_results
            logger.info("Quality reflection completed")
            
        except Exception as e:
            error_msg = f"Quality reflection failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["reflection_results"] = {"overall_quality": "unknown", "issues": [error_msg]}
        
        return state
    
    def _create_reflection_prompt(self, generated_data: Dict[str, Any], 
                                analysis: Dict[str, Any], user_profile: Dict[str, Any], 
                                events: List[str]) -> str:
        """Create prompt for quality reflection."""
        data_summary = {}
        for app_name, app_data in generated_data.items():
            if app_data and app_name in app_data:
                data_summary[app_name] = len(app_data[app_name])
        
        return f"""
Evaluate the quality and realism of the generated iPhone app data.

USER PROFILE: {json.dumps(user_profile, indent=2)}
EVENTS: {events}
ANALYSIS: {json.dumps(analysis, indent=2)}
DATA SUMMARY: {json.dumps(data_summary, indent=2)}

Please provide a comprehensive quality assessment in JSON format:
{{
    "overall_quality": "excellent|good|fair|poor",
    "realism_score": 1-10,
    "diversity_score": 1-10,
    "coherence_score": 1-10,
    "strengths": ["list of strong points"],
    "weaknesses": ["list of areas for improvement"],
    "cross_app_consistency": "assessment of data relationships across apps",
    "temporal_consistency": "assessment of timeline coherence",
    "character_consistency": "how well data matches the user profile",
    "recommendations": ["suggestions for improvement"],
    "critical_issues": ["serious problems that need addressing"]
}}

Focus on whether the data feels authentic and whether it tells a coherent story about this person's digital life.
"""
    
    def _parse_reflection(self, response: str) -> Dict[str, Any]:
        """Parse the reflection response."""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {
                    "overall_quality": "unknown",
                    "realism_score": 5,
                    "diversity_score": 5,
                    "coherence_score": 5,
                    "strengths": [],
                    "weaknesses": ["Unable to parse reflection"],
                    "recommendations": [],
                    "critical_issues": []
                }
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse reflection JSON")
            return {
                "overall_quality": "unknown",
                "realism_score": 5,
                "diversity_score": 5,
                "coherence_score": 5,
                "strengths": [],
                "weaknesses": ["JSON parsing failed"],
                "recommendations": [],
                "critical_issues": []
            }


class OutputNode(BaseNode):
    """Packages and saves the final output."""
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Package and save all generated data."""
        logger.info("Starting output packaging")
        state["current_step"] = "output"
        
        try:
            generated_data = state["generated_data"]
            validation_results = state["validation_results"]
            reflection_results = state["reflection_results"]
            config = state["config"]
            
            output_manager = OutputManager(config)
            output_path = output_manager.save_generated_data(
                generated_data=generated_data,
                validation_results=validation_results,
                reflection_results=reflection_results,
                user_profile=state["user_profile"],
                events=state["events"],
                analysis=state["analysis"]
            )
            
            state["output_path"] = output_path
            logger.info(f"Output packaged successfully at: {output_path}")
            
        except Exception as e:
            error_msg = f"Output packaging failed: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["output_path"] = ""
        
        return state