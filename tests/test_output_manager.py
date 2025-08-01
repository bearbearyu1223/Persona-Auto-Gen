"""Tests for output management functionality."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from persona_auto_gen.utils.output_manager import OutputManager


class TestOutputManager:
    """Test the OutputManager class."""
    
    def test_output_manager_creation(self, test_config):
        """Test creating output manager."""
        manager = OutputManager(test_config)
        assert manager.config == test_config
    
    def test_get_app_data_key(self, test_config):
        """Test getting app data keys."""
        manager = OutputManager(test_config)
        
        assert manager._get_app_data_key("contacts") == "contacts"
        assert manager._get_app_data_key("calendar") == "events"
        assert manager._get_app_data_key("sms") == "conversations"
        assert manager._get_app_data_key("emails") == "emails"
        assert manager._get_app_data_key("reminders") == "reminders"
        assert manager._get_app_data_key("notes") == "notes"
        assert manager._get_app_data_key("wallet") == "passes"
    
    def test_save_generated_data_success(self, test_config, sample_user_profile, sample_events):
        """Test successful data saving."""
        manager = OutputManager(test_config)
        
        generated_data = {
            "contacts": {
                "contacts": [
                    {
                        "id": "contact_1",
                        "first_name": "John",
                        "last_name": "Doe",
                        "display_name": "John Doe",
                        "relationship": "friend",
                        "created_date": "2024-01-15T10:00:00"
                    }
                ]
            }
        }
        
        validation_results = {
            "contacts": {
                "is_valid": True,
                "total_errors": 0
            }
        }
        
        reflection_results = {
            "overall_quality": "good",
            "realism_score": 8
        }
        
        analysis = {"user_characteristics": {"lifestyle": "professional"}}
        
        output_path = manager.save_generated_data(
            generated_data=generated_data,
            validation_results=validation_results,
            reflection_results=reflection_results,
            user_profile=sample_user_profile,
            events=sample_events,
            analysis=analysis
        )
        
        assert isinstance(output_path, str)
        output_path_obj = Path(output_path)
        assert output_path_obj.exists()
        
        # Check that files were created
        assert (output_path_obj / "contacts.json").exists()
        assert (output_path_obj / "validation_report.json").exists()
        assert (output_path_obj / "reflection_report.json").exists()
        
        if test_config.include_metadata:
            assert (output_path_obj / "metadata.json").exists()
        
        if test_config.create_summary_report:
            assert (output_path_obj / "SUMMARY.md").exists()
        
        assert (output_path_obj / "README.md").exists()
    
    def test_save_app_data_files(self, test_config, temp_output_dir):
        """Test saving individual app data files."""
        manager = OutputManager(test_config)
        
        generated_data = {
            "contacts": {"contacts": [{"id": "1", "name": "Test"}]},
            "calendar": {"events": [{"id": "1", "title": "Meeting"}]},
            "empty_app": {}  # Should be skipped
        }
        
        manager._save_app_data_files(temp_output_dir, generated_data)
        
        # Check that files were created for non-empty data
        assert (temp_output_dir / "contacts.json").exists()
        assert (temp_output_dir / "calendar.json").exists()
        assert not (temp_output_dir / "empty_app.json").exists()
        
        # Check file contents
        with open(temp_output_dir / "contacts.json", 'r') as f:
            contacts_data = json.load(f)
            assert contacts_data["contacts"][0]["id"] == "1"
    
    def test_save_metadata(self, test_config, temp_output_dir, sample_user_profile, sample_events):
        """Test saving metadata."""
        # Enable metadata saving
        test_config.include_metadata = True
        manager = OutputManager(test_config)
        
        analysis = {"user_characteristics": {"lifestyle": "professional"}}
        
        manager._save_metadata(temp_output_dir, sample_user_profile, sample_events, analysis)
        
        metadata_path = temp_output_dir / "metadata.json"
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            assert "generation_info" in metadata
            assert "input_data" in metadata
            assert metadata["input_data"]["user_profile"] == sample_user_profile
    
    def test_save_metadata_disabled(self, test_config, temp_output_dir, sample_user_profile, sample_events):
        """Test that metadata is not saved when disabled."""
        # Disable metadata saving
        test_config.include_metadata = False
        manager = OutputManager(test_config)
        
        analysis = {}
        manager._save_metadata(temp_output_dir, sample_user_profile, sample_events, analysis)
        
        metadata_path = temp_output_dir / "metadata.json"
        assert not metadata_path.exists()
    
    def test_save_validation_report(self, test_config, temp_output_dir):
        """Test saving validation report."""
        manager = OutputManager(test_config)
        
        validation_results = {
            "contacts": {"is_valid": True, "total_errors": 0},
            "calendar": {"is_valid": False, "total_errors": 2}
        }
        
        manager._save_validation_report(temp_output_dir, validation_results)
        
        validation_path = temp_output_dir / "validation_report.json"
        assert validation_path.exists()
        
        with open(validation_path, 'r') as f:
            report = json.load(f)
            assert "contacts" in report
            assert "calendar" in report
    
    def test_save_reflection_report(self, test_config, temp_output_dir):
        """Test saving reflection report."""
        manager = OutputManager(test_config)
        
        reflection_results = {
            "overall_quality": "good",
            "realism_score": 8,
            "strengths": ["Realistic data"],
            "weaknesses": ["Could be more diverse"]
        }
        
        manager._save_reflection_report(temp_output_dir, reflection_results)
        
        reflection_path = temp_output_dir / "reflection_report.json"
        assert reflection_path.exists()
        
        with open(reflection_path, 'r') as f:
            report = json.load(f)
            assert report["overall_quality"] == "good"
            assert report["realism_score"] == 8
    
    def test_create_summary_report(self, test_config, temp_output_dir, sample_user_profile, sample_events):
        """Test creating summary report."""
        manager = OutputManager(test_config)
        
        generated_data = {
            "contacts": {"contacts": [{"id": "1"}]},
            "calendar": {"events": [{"id": "1"}, {"id": "2"}]}
        }
        
        validation_results = {
            "contacts": {"is_valid": True, "total_errors": 0},
            "calendar": {"is_valid": True, "total_errors": 0}
        }
        
        reflection_results = {
            "overall_quality": "excellent",
            "realism_score": 9,
            "diversity_score": 8,
            "coherence_score": 9,
            "strengths": ["Very realistic", "Good variety"],
            "weaknesses": ["Minor timing issues"]
        }
        
        manager._create_summary_report(
            temp_output_dir, generated_data, validation_results, 
            reflection_results, sample_user_profile, sample_events
        )
        
        summary_path = temp_output_dir / "SUMMARY.md"
        assert summary_path.exists()
        
        with open(summary_path, 'r') as f:
            content = f.read()
            assert "Persona Data Generation Summary" in content
            assert "User Profile" in content
            assert "Events" in content
            assert "Generated Data Summary" in content
            assert "Validation Results" in content
            assert "Quality Assessment" in content
    
    def test_create_readme(self, test_config, temp_output_dir, sample_user_profile):
        """Test creating README file."""
        manager = OutputManager(test_config)
        
        # Create some dummy files first
        (temp_output_dir / "contacts.json").touch()
        (temp_output_dir / "calendar.json").touch()
        
        manager._create_readme(temp_output_dir, "test_profile", sample_user_profile)
        
        readme_path = temp_output_dir / "README.md"
        assert readme_path.exists()
        
        with open(readme_path, 'r') as f:
            content = f.read()
            assert "test_profile" in content
            assert "Contents" in content
            assert "contacts.json" in content
            assert "calendar.json" in content
    
    def test_create_archive(self, test_config, temp_output_dir):
        """Test creating ZIP archive."""
        manager = OutputManager(test_config)
        
        # Create some test files
        (temp_output_dir / "test_file.json").write_text('{"test": "data"}')
        (temp_output_dir / "README.md").write_text("Test README")
        
        archive_path = manager.create_archive(str(temp_output_dir))
        
        assert isinstance(archive_path, str)
        archive_path_obj = Path(archive_path)
        assert archive_path_obj.exists()
        assert archive_path_obj.suffix == ".zip"
    
    def test_create_archive_nonexistent_path(self, test_config):
        """Test creating archive for nonexistent path."""
        manager = OutputManager(test_config)
        
        with pytest.raises(FileNotFoundError):
            manager.create_archive("/nonexistent/path")
    
    def test_get_output_size(self, test_config, temp_output_dir):
        """Test getting output size information."""
        manager = OutputManager(test_config)
        
        # Create test files with known sizes
        (temp_output_dir / "small_file.json").write_text('{"test": "data"}')
        (temp_output_dir / "large_file.json").write_text('{"test": "' + "x" * 1000 + '"}')
        
        size_info = manager.get_output_size(str(temp_output_dir))
        
        assert "total_size_bytes" in size_info
        assert "total_size_mb" in size_info
        assert "file_count" in size_info
        assert "file_sizes" in size_info
        
        assert size_info["file_count"] == 2
        assert size_info["total_size_bytes"] > 0
        assert isinstance(size_info["total_size_mb"], float)
        
        # Check individual file sizes
        assert "small_file.json" in size_info["file_sizes"]
        assert "large_file.json" in size_info["file_sizes"]
    
    def test_get_output_size_nonexistent_path(self, test_config):
        """Test getting output size for nonexistent path."""
        manager = OutputManager(test_config)
        
        size_info = manager.get_output_size("/nonexistent/path")
        
        assert "error" in size_info
        assert "does not exist" in size_info["error"]
    
    def test_cleanup_old_outputs(self, test_config, temp_output_dir):
        """Test cleaning up old output directories."""
        # Update config to use temp directory
        test_config.output_directory = temp_output_dir
        manager = OutputManager(test_config)
        
        # Create mock old directories
        old_dirs = []
        for i in range(5):
            old_dir = temp_output_dir / f"user_profile_{i}"
            old_dir.mkdir()
            (old_dir / "test.json").write_text('{"test": "data"}')
            old_dirs.append(old_dir)
        
        # Create a non-matching directory (should not be deleted)
        other_dir = temp_output_dir / "other_directory"
        other_dir.mkdir()
        
        # Cleanup, keeping only 3 most recent
        manager.cleanup_old_outputs(keep_count=3)
        
        # Check that only 3 directories remain (plus the non-matching one)
        remaining_dirs = [d for d in temp_output_dir.iterdir() if d.is_dir()]
        profile_dirs = [d for d in remaining_dirs if d.name.startswith("user_profile_")]
        
        assert len(profile_dirs) == 3
        assert other_dir.exists()  # Non-matching directory should remain
    
    def test_save_generated_data_error_handling(self, test_config):
        """Test error handling in save_generated_data."""
        manager = OutputManager(test_config)
        
        # Mock Path.mkdir to raise an exception
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                manager.save_generated_data(
                    generated_data={},
                    validation_results={},
                    reflection_results={},
                    user_profile={},
                    events=[],
                    analysis={}
                )