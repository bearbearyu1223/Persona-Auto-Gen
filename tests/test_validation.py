"""Tests for schema validation system."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from persona_auto_gen.utils.validation import SchemaValidator
from persona_auto_gen.config import Config


class TestSchemaValidator:
    """Test the SchemaValidator class."""
    
    def test_validator_creation(self):
        """Test creating schema validator."""
        validator = SchemaValidator()
        assert validator is not None
    
    def test_validator_with_config(self, test_config):
        """Test creating validator with config."""
        validator = SchemaValidator(test_config)
        assert validator.config == test_config
    
    def test_get_app_data_key(self):
        """Test getting app data keys."""
        validator = SchemaValidator()
        
        assert validator._get_app_data_key("contacts") == "contacts"
        assert validator._get_app_data_key("calendar") == "events"
        assert validator._get_app_data_key("sms") == "conversations"
        assert validator._get_app_data_key("emails") == "emails"
        assert validator._get_app_data_key("reminders") == "reminders"
        assert validator._get_app_data_key("notes") == "notes"
        assert validator._get_app_data_key("wallet") == "passes"
    
    def test_is_critical_error(self):
        """Test identifying critical errors."""
        validator = SchemaValidator()
        
        # Mock ValidationError
        class MockValidationError:
            def __init__(self, message):
                self.message = message
        
        # Critical errors
        assert validator._is_critical_error(MockValidationError("'field' is a required property"))
        assert validator._is_critical_error(MockValidationError("Invalid type"))
        assert validator._is_critical_error(MockValidationError("Format error"))
        
        # Non-critical errors
        assert not validator._is_critical_error(MockValidationError("Optional field missing"))
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"$schema": "http://json-schema.org/draft-07/schema#", "title": "Test Schema", "type": "object"}')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_schema_success(self, mock_exists, mock_file):
        """Test successful schema loading."""
        validator = SchemaValidator()
        
        schema = validator._load_schema("test_app")
        
        assert isinstance(schema, dict)
        assert schema["title"] == "Test Schema"
    
    @patch('pathlib.Path.exists', return_value=False)
    def test_load_schema_file_not_found(self, mock_exists):
        """Test schema loading with missing file."""
        validator = SchemaValidator()
        
        with pytest.raises(FileNotFoundError):
            validator._load_schema("nonexistent_app")
    
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('pathlib.Path.exists', return_value=True)
    def test_load_schema_invalid_json(self, mock_exists, mock_file):
        """Test schema loading with invalid JSON."""
        validator = SchemaValidator()
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            validator._load_schema("invalid_app")
    
    def test_create_validation_summary(self):
        """Test creating validation summary."""
        validator = SchemaValidator()
        
        app_results = {
            "contacts": {"is_valid": True},
            "calendar": {"is_valid": False},
            "sms": {"is_valid": True}
        }
        
        summary = validator._create_validation_summary(app_results)
        
        assert "valid_apps" in summary
        assert "invalid_apps" in summary
        assert "validation_rate" in summary
        
        assert "contacts" in summary["valid_apps"]
        assert "sms" in summary["valid_apps"]
        assert "calendar" in summary["invalid_apps"]
        assert summary["validation_rate"] == 2/3  # 2 out of 3 valid
    
    def test_validate_app_data_missing_schema(self):
        """Test validating app data with missing schema."""
        validator = SchemaValidator()
        
        with patch.object(validator, '_load_schema', side_effect=FileNotFoundError("Schema not found")):
            result = validator.validate_app_data("nonexistent", {})
            
            assert not result["is_valid"]
            assert "errors" in result
            assert len(result["errors"]) > 0
    
    def test_validate_all_data(self):
        """Test validating all generated data."""
        validator = SchemaValidator()
        
        generated_data = {
            "contacts": {"contacts": []},
            "calendar": {"events": []},
            "empty_app": {}
        }
        
        # Mock individual validation results
        def mock_validate_app_data(app_name, data):
            if app_name == "contacts":
                return {"is_valid": True, "total_errors": 0, "critical_errors": 0}
            elif app_name == "calendar":
                return {"is_valid": False, "total_errors": 2, "critical_errors": 1}
            else:
                return {"is_valid": True, "total_errors": 0, "critical_errors": 0}
        
        with patch.object(validator, 'validate_app_data', side_effect=mock_validate_app_data):
            results = validator.validate_all_data(generated_data)
            
            assert "overall_valid" in results
            assert "total_apps" in results
            assert "total_errors" in results
            assert "critical_errors" in results
            assert "app_results" in results
            assert "summary" in results
            
            # Should be invalid due to critical errors
            assert not results["overall_valid"]
            assert results["total_errors"] == 2
            assert results["critical_errors"] == 1
    
    def test_get_available_schemas_empty_directory(self):
        """Test getting available schemas from empty directory."""
        validator = SchemaValidator()
        
        with patch('pathlib.Path.exists', return_value=False):
            schemas = validator.get_available_schemas()
            assert schemas == []
    
    @patch('pathlib.Path.exists', return_value=True)
    def test_get_available_schemas_with_files(self, mock_exists):
        """Test getting available schemas with files."""
        validator = SchemaValidator()
        
        # Mock glob to return some schema files
        mock_files = [
            Path("contacts.json"),
            Path("calendar.json"),
            Path("sms.json")
        ]
        
        with patch.object(Path, 'glob', return_value=mock_files):
            schemas = validator.get_available_schemas()
            
            assert "contacts" in schemas
            assert "calendar" in schemas
            assert "sms" in schemas
            assert len(schemas) == 3
    
    def test_validate_single_entry_success(self):
        """Test validating a single entry successfully."""
        validator = SchemaValidator()
        
        # Mock schema loading
        mock_schema = {
            "properties": {
                "contacts": {
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"}
                        },
                        "required": ["id", "name"]
                    }
                }
            }
        }
        
        entry = {"id": "123", "name": "Test"}
        
        with patch.object(validator, '_load_schema', return_value=mock_schema):
            with patch('jsonschema.validate') as mock_validate:
                mock_validate.return_value = None  # No exception = valid
                
                result = validator.validate_single_entry("contacts", entry)
                
                assert result["is_valid"]
                assert len(result["errors"]) == 0
    
    def test_validate_single_entry_failure(self):
        """Test validating a single entry with failure."""
        validator = SchemaValidator()
        
        # Mock schema loading
        mock_schema = {
            "properties": {
                "contacts": {
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"}
                        },
                        "required": ["id", "name"]
                    }
                }
            }
        }
        
        entry = {"id": "123"}  # Missing required 'name'
        
        with patch.object(validator, '_load_schema', return_value=mock_schema):
            from jsonschema import ValidationError
            with patch('jsonschema.validate', side_effect=ValidationError("'name' is required")):
                result = validator.validate_single_entry("contacts", entry)
                
                assert not result["is_valid"]
                assert len(result["errors"]) > 0
                assert "'name' is required" in result["errors"][0]


class TestSchemaInfo:
    """Test schema information extraction."""
    
    def test_get_schema_info_success(self):
        """Test getting schema info successfully."""
        validator = SchemaValidator()
        
        mock_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Test Schema",
            "type": "object",
            "properties": {
                "test_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "required_field": {"type": "string"},
                            "optional_field": {"type": "string"}
                        },
                        "required": ["required_field"]
                    }
                }
            }
        }
        
        with patch.object(validator, '_load_schema', return_value=mock_schema):
            info = validator.get_schema_info("test_app")
            
            assert info["app_name"] == "test_app"
            assert info["schema_title"] == "Test Schema"
            assert info["schema_version"] == "http://json-schema.org/draft-07/schema#"
            assert isinstance(info["required_fields"], list)
            assert isinstance(info["optional_fields"], list)
    
    def test_get_schema_info_error(self):
        """Test getting schema info with error."""
        validator = SchemaValidator()
        
        with patch.object(validator, '_load_schema', side_effect=Exception("Schema error")):
            info = validator.get_schema_info("error_app")
            
            assert info["app_name"] == "error_app"
            assert "error" in info
            assert "Schema error" in info["error"]