"""Output management and file organization utilities."""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import shutil

from ..config import Config

logger = logging.getLogger(__name__)


class OutputManager:
    """Manages output packaging and file organization."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def save_generated_data(self, generated_data: Dict[str, Any],
                          validation_results: Dict[str, Any],
                          reflection_results: Dict[str, Any],
                          user_profile: Dict[str, Any],
                          events: List[str],
                          analysis: Dict[str, Any]) -> str:
        """Save all generated data to organized output structure."""
        
        # Create unique output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_id = f"user_profile_{timestamp}"
        output_path = self.config.get_output_path(profile_id)
        
        logger.info(f"Saving generated data to: {output_path}")
        
        try:
            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save individual app data files
            self._save_app_data_files(output_path, generated_data)
            
            # Save metadata and reports
            self._save_metadata(output_path, user_profile, events, analysis)
            self._save_validation_report(output_path, validation_results)
            self._save_reflection_report(output_path, reflection_results)
            
            # Create summary report if enabled
            if self.config.create_summary_report:
                self._create_summary_report(
                    output_path, generated_data, validation_results, 
                    reflection_results, user_profile, events
                )
            
            # Create README for the output
            self._create_readme(output_path, profile_id, user_profile)
            
            logger.info(f"Data successfully saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save generated data: {str(e)}")
            raise e
    
    def _save_app_data_files(self, output_path: Path, generated_data: Dict[str, Any]):
        """Save individual JSON files for each app."""
        logger.info("Saving app data files")
        
        for app_name, app_data in generated_data.items():
            if app_data:  # Only save non-empty data
                file_path = output_path / f"{app_name}.json"
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(app_data, f, indent=2, ensure_ascii=False)
                    
                    logger.debug(f"Saved {app_name} data to {file_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to save {app_name} data: {str(e)}")
    
    def _save_metadata(self, output_path: Path, user_profile: Dict[str, Any], 
                      events: List[str], analysis: Dict[str, Any]):
        """Save metadata about the generation process."""
        if not self.config.include_metadata:
            return
            
        logger.info("Saving metadata")
        
        metadata = {
            "generation_info": {
                "timestamp": datetime.now().isoformat(),
                "config": self.config.to_dict(),
                "generator_version": "0.1.0"
            },
            "input_data": {
                "user_profile": user_profile,
                "events": events,
                "analysis": analysis
            }
        }
        
        metadata_path = output_path / "metadata.json"
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved metadata to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {str(e)}")
    
    def _save_validation_report(self, output_path: Path, validation_results: Dict[str, Any]):
        """Save validation results report."""
        logger.info("Saving validation report")
        
        validation_path = output_path / "validation_report.json"
        
        try:
            with open(validation_path, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved validation report to {validation_path}")
            
        except Exception as e:
            logger.error(f"Failed to save validation report: {str(e)}")
    
    def _save_reflection_report(self, output_path: Path, reflection_results: Dict[str, Any]):
        """Save reflection results report."""
        logger.info("Saving reflection report")
        
        reflection_path = output_path / "reflection_report.json"
        
        try:
            with open(reflection_path, 'w', encoding='utf-8') as f:
                json.dump(reflection_results, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved reflection report to {reflection_path}")
            
        except Exception as e:
            logger.error(f"Failed to save reflection report: {str(e)}")
    
    def _create_summary_report(self, output_path: Path, generated_data: Dict[str, Any],
                             validation_results: Dict[str, Any], reflection_results: Dict[str, Any],
                             user_profile: Dict[str, Any], events: List[str]):
        """Create a human-readable summary report."""
        logger.info("Creating summary report")
        
        summary_path = output_path / "SUMMARY.md"
        
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# Persona Data Generation Summary\n\n")
                
                # Generation info
                f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Time Period:** {self.config.start_date.strftime('%Y-%m-%d')} to {self.config.end_date.strftime('%Y-%m-%d')}\n\n")
                
                # User profile summary
                f.write("## User Profile\n\n")
                for key, value in user_profile.items():
                    f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
                f.write("\n")
                
                # Events
                f.write("## Events\n\n")
                for i, event in enumerate(events, 1):
                    f.write(f"{i}. {event}\n")
                f.write("\n")
                
                # Data summary
                f.write("## Generated Data Summary\n\n")
                f.write("| App | Entries Generated |\n")
                f.write("|-----|------------------|\n")
                
                for app_name, app_data in generated_data.items():
                    if app_data:
                        data_key = self._get_app_data_key(app_name)
                        count = len(app_data.get(data_key, []))
                        f.write(f"| {app_name.title()} | {count} |\n")
                
                f.write("\n")
                
                # Validation summary
                f.write("## Validation Results\n\n")
                if validation_results:
                    total_errors = sum(r.get("total_errors", 0) for r in validation_results.values())
                    f.write(f"- **Total Validation Errors:** {total_errors}\n")
                    
                    for app_name, results in validation_results.items():
                        status = "✅ Passed" if results.get("is_valid", False) else "❌ Failed"
                        f.write(f"- **{app_name.title()}:** {status}\n")
                
                f.write("\n")
                
                # Quality reflection
                f.write("## Quality Assessment\n\n")
                if reflection_results:
                    quality = reflection_results.get("overall_quality", "unknown")
                    f.write(f"- **Overall Quality:** {quality.title()}\n")
                    
                    for metric in ["realism_score", "diversity_score", "coherence_score"]:
                        score = reflection_results.get(metric, 0)
                        f.write(f"- **{metric.replace('_', ' ').title()}:** {score}/10\n")
                    
                    strengths = reflection_results.get("strengths", [])
                    if strengths:
                        f.write("\n**Strengths:**\n")
                        for strength in strengths:
                            f.write(f"- {strength}\n")
                    
                    weaknesses = reflection_results.get("weaknesses", [])
                    if weaknesses:
                        f.write("\n**Areas for Improvement:**\n")
                        for weakness in weaknesses:
                            f.write(f"- {weakness}\n")
                
                f.write("\n---\n")
                f.write("*Generated by Persona Auto Gen*\n")
                
            logger.debug(f"Created summary report at {summary_path}")
            
        except Exception as e:
            logger.error(f"Failed to create summary report: {str(e)}")
    
    def _create_readme(self, output_path: Path, profile_id: str, user_profile: Dict[str, Any]):
        """Create a README file for the output directory."""
        logger.info("Creating README file")
        
        readme_path = output_path / "README.md"
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {profile_id}\n\n")
                f.write("This directory contains synthetic iPhone app data generated by Persona Auto Gen.\n\n")
                
                f.write("## Contents\n\n")
                
                # List data files
                for app in self.config.enabled_apps:
                    app_file = output_path / f"{app}.json"
                    if app_file.exists():
                        f.write(f"- `{app}.json` - {app.title()} app data\n")
                
                f.write("\n## Metadata Files\n\n")
                f.write("- `metadata.json` - Generation configuration and input data\n")
                f.write("- `validation_report.json` - Schema validation results\n")
                f.write("- `reflection_report.json` - Quality assessment results\n")
                f.write("- `SUMMARY.md` - Human-readable summary report\n\n")
                
                f.write("## Data Format\n\n")
                f.write("All data files are in JSON format and conform to the iPhone app data schemas.\n")
                f.write("See the validation report for schema compliance details.\n\n")
                
                f.write("## Usage\n\n")
                f.write("This synthetic data can be used for:\n")
                f.write("- Testing iPhone app integrations\n")
                f.write("- User experience research\n")
                f.write("- Data analysis and modeling\n")
                f.write("- Privacy-preserving demonstrations\n\n")
                
                f.write("**Note:** This is synthetic data generated for testing purposes only.\n")
                
            logger.debug(f"Created README at {readme_path}")
            
        except Exception as e:
            logger.error(f"Failed to create README: {str(e)}")
    
    def _get_app_data_key(self, app_name: str) -> str:
        """Get the key used for app data in the JSON structure."""
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
    
    def create_archive(self, output_path: str, archive_name: str = None) -> str:
        """Create a ZIP archive of the generated data."""
        logger.info("Creating data archive")
        
        output_path_obj = Path(output_path)
        
        if not output_path_obj.exists():
            raise FileNotFoundError(f"Output path does not exist: {output_path}")
        
        if archive_name is None:
            archive_name = f"{output_path_obj.name}.zip"
        
        archive_path = output_path_obj.parent / archive_name
        
        try:
            # Create ZIP archive
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'zip',
                output_path_obj.parent,
                output_path_obj.name
            )
            
            logger.info(f"Created archive: {archive_path}")
            return str(archive_path)
            
        except Exception as e:
            logger.error(f"Failed to create archive: {str(e)}")
            raise e
    
    def cleanup_old_outputs(self, keep_count: int = 10):
        """Clean up old output directories, keeping only the most recent ones."""
        logger.info(f"Cleaning up old outputs, keeping {keep_count} most recent")
        
        try:
            output_dirs = [
                d for d in self.config.output_directory.iterdir()
                if d.is_dir() and d.name.startswith("user_profile_")
            ]
            
            # Sort by creation time (newest first)
            output_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            
            # Remove old directories
            dirs_to_remove = output_dirs[keep_count:]
            
            for old_dir in dirs_to_remove:
                logger.info(f"Removing old output directory: {old_dir}")
                shutil.rmtree(old_dir)
            
            logger.info(f"Cleanup completed, removed {len(dirs_to_remove)} old directories")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old outputs: {str(e)}")
    
    def get_output_size(self, output_path: str) -> Dict[str, Any]:
        """Get size information for generated output."""
        output_path_obj = Path(output_path)
        
        if not output_path_obj.exists():
            return {"error": "Path does not exist"}
        
        total_size = 0
        file_sizes = {}
        
        for file_path in output_path_obj.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                file_sizes[file_path.name] = size
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "file_count": len(file_sizes),
            "file_sizes": file_sizes
        }