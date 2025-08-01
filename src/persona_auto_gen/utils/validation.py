"""Schema validation utilities."""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

from ..config import Config

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates generated data against JSON schemas."""
    
    def __init__(self, config: Config = None):
        self.config = config
        self._schemas = {}
        self._schema_dir = Path(__file__).parent.parent / "schemas"
        
    def _load_schema(self, app_name: str) -> Dict[str, Any]:
        """Load JSON schema for a specific app."""
        if app_name in self._schemas:
            return self._schemas[app_name]
        
        schema_path = self._schema_dir / f"{app_name}.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            self._schemas[app_name] = schema
            return schema
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file {schema_path}: {str(e)}")
    
    def validate_app_data(self, app_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data for a specific app against its schema."""
        logger.info(f"Validating {app_name} data")
        
        try:
            # Load schema
            schema = self._load_schema(app_name)
            
            # Validate data
            validate(instance=data, schema=schema)
            
            # Count entries
            app_data_key = self._get_app_data_key(app_name)
            entry_count = len(data.get(app_data_key, []))
            
            logger.info(f"{app_name} validation passed with {entry_count} entries")
            
            return {
                "is_valid": True,
                "app_name": app_name,
                "entry_count": entry_count,
                "errors": [],
                "warnings": [],
                "total_errors": 0,
                "critical_errors": 0
            }
            
        except ValidationError as e:
            error_msg = f"Validation error in {app_name}: {e.message}"
            logger.error(error_msg)
            
            # Categorize error severity
            is_critical = self._is_critical_error(e)
            
            return {
                "is_valid": False,
                "app_name": app_name,
                "entry_count": 0,
                "errors": [error_msg],
                "warnings": [],
                "total_errors": 1,
                "critical_errors": 1 if is_critical else 0
            }
            
        except Exception as e:
            error_msg = f"Unexpected validation error in {app_name}: {str(e)}"
            logger.error(error_msg)
            
            return {
                "is_valid": False,
                "app_name": app_name,
                "entry_count": 0,
                "errors": [error_msg],
                "warnings": [],
                "total_errors": 1,
                "critical_errors": 1
            }
    
    def validate_all_data(self, generated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all generated data."""
        logger.info("Starting comprehensive data validation")
        
        validation_results = {}
        total_errors = 0
        total_critical_errors = 0
        
        for app_name, app_data in generated_data.items():
            if app_data:  # Only validate non-empty data
                results = self.validate_app_data(app_name, app_data)
                validation_results[app_name] = results
                
                total_errors += results["total_errors"]
                total_critical_errors += results["critical_errors"]
        
        overall_valid = total_critical_errors == 0
        
        logger.info(f"Validation completed: {len(validation_results)} apps validated, "
                   f"{total_errors} total errors, {total_critical_errors} critical errors")
        
        return {
            "overall_valid": overall_valid,
            "total_apps": len(validation_results),
            "total_errors": total_errors,
            "critical_errors": total_critical_errors,
            "app_results": validation_results,
            "summary": self._create_validation_summary(validation_results)
        }
    
    def _get_app_data_key(self, app_name: str) -> str:
        """Get the key used for app data in the JSON structure."""
        # Map app names to their data keys
        key_mapping = {
            "contacts": "contacts",
            "calendar": "events",
            "sms": "conversations", 
            "emails": "emails",
            "reminders": "reminders",
            "notes": "notes",
            "wallet": "passes",
            "alarms": "alarms"
        }
        return key_mapping.get(app_name, app_name)
    
    def _is_critical_error(self, error: ValidationError) -> bool:
        """Determine if a validation error is critical."""
        critical_patterns = [
            "required",
            "type",
            "format",
            "additionalProperties"
        ]
        
        error_message = error.message.lower()
        return any(pattern in error_message for pattern in critical_patterns)
    
    def _create_validation_summary(self, app_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of validation results."""
        valid_apps = []
        invalid_apps = []
        
        for app_name, results in app_results.items():
            if results["is_valid"]:
                valid_apps.append(app_name)
            else:
                invalid_apps.append(app_name)
        
        return {
            "valid_apps": valid_apps,
            "invalid_apps": invalid_apps,
            "validation_rate": len(valid_apps) / len(app_results) if app_results else 0
        }
    
    def get_schema_info(self, app_name: str) -> Dict[str, Any]:
        """Get information about a schema."""
        try:
            schema = self._load_schema(app_name)
            
            return {
                "app_name": app_name,
                "schema_title": schema.get("title", "Unknown"),
                "schema_version": schema.get("$schema", "Unknown"),
                "required_fields": self._extract_required_fields(schema),
                "optional_fields": self._extract_optional_fields(schema)
            }
            
        except Exception as e:
            logger.error(f"Failed to get schema info for {app_name}: {str(e)}")
            return {
                "app_name": app_name,
                "error": str(e)
            }
    
    def _extract_required_fields(self, schema: Dict[str, Any]) -> List[str]:
        """Extract required fields from schema."""
        required_fields = []
        
        # Navigate schema structure to find required fields
        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                if "items" in prop_def and "properties" in prop_def["items"]:
                    # Array of objects
                    item_required = prop_def["items"].get("required", [])
                    required_fields.extend([f"{prop_name}.{field}" for field in item_required])
        
        return required_fields
    
    def _extract_optional_fields(self, schema: Dict[str, Any]) -> List[str]:
        """Extract optional fields from schema."""
        optional_fields = []
        
        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                if "items" in prop_def and "properties" in prop_def["items"]:
                    # Array of objects
                    all_props = list(prop_def["items"]["properties"].keys())
                    required_props = prop_def["items"].get("required", [])
                    optional_props = [prop for prop in all_props if prop not in required_props]
                    optional_fields.extend([f"{prop_name}.{field}" for field in optional_props])
        
        return optional_fields
    
    def validate_single_entry(self, app_name: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single data entry."""
        try:
            schema = self._load_schema(app_name)
            
            # Get the schema for individual items
            app_data_key = self._get_app_data_key(app_name)
            if "properties" in schema and app_data_key in schema["properties"]:
                item_schema = schema["properties"][app_data_key]["items"]
                
                validate(instance=entry, schema=item_schema)
                
                return {
                    "is_valid": True,
                    "errors": []
                }
                
        except ValidationError as e:
            return {
                "is_valid": False,
                "errors": [e.message]
            }
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    def get_available_schemas(self) -> List[str]:
        """Get list of available schema files."""
        schema_files = []
        
        if self._schema_dir.exists():
            for schema_file in self._schema_dir.glob("*.json"):
                schema_files.append(schema_file.stem)
        
        return sorted(schema_files)