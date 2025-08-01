"""Basic usage example for Persona Auto Gen."""

import os
import sys
from datetime import datetime

# Add the src directory to the path to import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persona_auto_gen.main import PersonaAgent
from persona_auto_gen.config import Config, OpenAIModel


def main():
    """Demonstrate basic usage of Persona Auto Gen."""
    
    # Set your OpenAI API key
    # Option 1: Set environment variable
    # os.environ["OPENAI_API_KEY"] = "your-api-key-here"
    
    # Option 2: Pass it directly to config
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set your OPENAI_API_KEY environment variable")
        return
    
    # Create configuration
    config = Config(
        openai_model=OpenAIModel.GPT_4O,
        openai_api_key=api_key,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 5, 31),
        data_volume={
            "contacts": 10,
            "calendar": 10,
            "sms": 0,
            "emails": 0,
            "reminders": 2,
            "notes": 0,
            "wallet": 0,
            "alarms": 0
        },
        temperature=0.7,
        max_tokens=4000
    )
    
    # Define user profile
    user_profile = {
        "age": 32,
        "occupation": "Marketing Manager",
        "location": "Austin, TX",
        "interests": ["music", "food", "travel", "photography"],
        "lifestyle": "Busy professional with active social life",
        "tech_savviness": "Medium-High",
        "communication_style": "Friendly and enthusiastic"
    }
    
    # Define events
    events = [
        "Regular yoga classes twice a week",
        "Date nights with partner every Friday",
        "Daily Carpool to work",
    ]
    
    # Initialize the agent
    print("Initializing Persona Auto Gen agent...")
    agent = PersonaAgent(config)
    
    # Validate configuration
    issues = agent.validate_configuration()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return
    
    print("Configuration validated successfully!")
    
    # Show configuration summary
    config_info = agent.get_config_info()
    print(f"\nConfiguration Summary:")
    print(f"  Model: {config_info['model']}")
    print(f"  Time Range: {config_info['time_range']['days']} days")
    print(f"  Enabled Apps: {', '.join(config_info['enabled_apps'])}")
    print(f"  Total Data Points: {sum(config_info['data_volume'].values())}")
    
    # Generate data
    print("\nStarting data generation...")
    print("This may take a few minutes depending on the data volume...")
    
    try:
        result = agent.generate(user_profile, events)
        
        if result["success"]:
            print("\n✅ Generation completed successfully!")
            print(f"📁 Output saved to: {result['output_path']}")
            
            # Show generated data summary
            print("\n📊 Generated Data Summary:")
            generated_data = result["generated_data"]
            for app_name, app_data in generated_data.items():
                if app_data:
                    # Get count of generated items
                    data_keys = {
                        "contacts": "contacts",
                        "calendar": "events",
                        "sms": "conversations", 
                        "emails": "emails",
                        "reminders": "reminders",
                        "notes": "notes",
                        "wallet": "passes",
                        "alarms": "alarms"
                    }
                    data_key = data_keys.get(app_name, app_name)
                    count = len(app_data.get(data_key, []))
                    print(f"  📱 {app_name.title()}: {count} entries")
            
            # Show validation results
            validation = result.get("validation_results", {})
            if validation:
                print("\n🔍 Validation Results:")
                for app_name, results in validation.items():
                    status = "✅ Passed" if results.get("is_valid", False) else "❌ Failed"
                    print(f"  {app_name.title()}: {status}")
            
            # Show quality assessment
            reflection = result.get("reflection_results", {})
            if reflection:
                print("\n🎯 Quality Assessment:")
                print(f"  Overall Quality: {reflection.get('overall_quality', 'unknown').title()}")
                
                for metric in ["realism_score", "diversity_score", "coherence_score"]:
                    score = reflection.get(metric, 0)
                    metric_name = metric.replace('_', ' ').title()
                    print(f"  {metric_name}: {score}/10")
                
                # Show strengths and weaknesses
                strengths = reflection.get("strengths", [])
                if strengths:
                    print("\n  Strengths:")
                    for strength in strengths[:3]:  # Show top 3
                        print(f"    • {strength}")
                
                weaknesses = reflection.get("weaknesses", [])
                if weaknesses:
                    print("\n  Areas for Improvement:")
                    for weakness in weaknesses[:3]:  # Show top 3
                        print(f"    • {weakness}")
            
            print(f"\n🎉 Data generation complete! Check the output directory:")
            print(f"   {result['output_path']}")
            print("\nFiles generated:")
            print("  • Individual JSON files for each app")
            print("  • validation_report.json - Schema validation results")
            print("  • reflection_report.json - Quality assessment")
            print("  • SUMMARY.md - Human-readable summary")
            print("  • README.md - Documentation")
        
        else:
            print("\n❌ Generation failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            errors = result.get('errors', [])
            if errors:
                print("\nDetailed errors:")
                for error in errors:
                    print(f"  • {error}")
    
    except KeyboardInterrupt:
        print("\n\nGeneration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()