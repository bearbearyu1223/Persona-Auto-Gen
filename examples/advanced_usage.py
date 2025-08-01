"""Advanced usage example for Persona Auto Gen."""

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Add the src directory to the path to import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from persona_auto_gen.main import PersonaAgent
from persona_auto_gen.config import Config, OpenAIModel
from persona_auto_gen.utils.validation import SchemaValidator
from persona_auto_gen.utils.output_manager import OutputManager


def create_custom_config():
    """Create a custom configuration for advanced usage."""
    return Config(
        # Use GPT-4 for highest quality
        openai_model=OpenAIModel.GPT_4,
        
        # Custom time range - last 6 months
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        
        # High-volume data generation
        data_volume={
            "contacts": 10,
            "calendar": 40,
            "sms": 10,
            "emails": 50,
            "reminders": 10,
            "notes": 10,
            "wallet": 5,
            "alarms": 2
        },
        
        # Only enable specific apps
        enabled_apps=["contacts", "calendar", "sms", "emails", "reminders", "alarms"],
        
        # Custom generation parameters
        temperature=0.6,  # Slightly more focused
        max_tokens=6000,  # Allow longer responses
        
        # Quality control settings
        enable_reflection=True,
        min_quality_score=7.0,
        max_regeneration_attempts=2,
        
        # Validation settings
        strict_validation=True,
        max_validation_errors=5,
        
        # Output settings
        create_summary_report=True,
        include_metadata=True,
        
        # Privacy settings
        preserve_privacy=True,
        anonymize_sensitive_data=True
    )


def create_detailed_user_profile():
    """Create a detailed user profile for advanced generation."""
    return {
        "demographics": {
            "age": 29,
            "gender": "female",
            "location": "Seattle, WA",
            "education": "Master's degree in Computer Science",
            "income_bracket": "upper-middle"
        },
        "professional": {
            "occupation": "Senior Software Engineer",
            "company": "Tech startup",
            "work_style": "Remote with occasional office days",
            "career_stage": "Mid-level with leadership aspirations",
            "networking_active": True
        },
        "personal": {
            "relationship_status": "In a relationship",
            "living_situation": "Apartment with partner",
            "pets": ["Cat named Pixel"],
            "health_conscious": True,
            "environmentally_conscious": True
        },
        "interests_and_hobbies": {
            "primary": ["software development", "rock climbing", "photography"],
            "secondary": ["cooking", "board games", "podcasts", "hiking"],
            "learning": ["machine learning", "sustainable living", "Japanese language"]
        },
        "technology_usage": {
            "tech_savviness": "Expert",
            "devices": ["iPhone", "MacBook Pro", "Apple Watch", "iPad"],
            "preferred_communication": ["Slack", "text messages", "email"],
            "social_media_usage": "Moderate",
            "privacy_awareness": "High"
        },
        "lifestyle_patterns": {
            "work_schedule": "9am-6pm Pacific Time",
            "exercise_routine": "Rock climbing 3x/week, weekend hikes",
            "social_frequency": "2-3 social events per week",
            "travel_frequency": "4-5 trips per year (mix of work and personal)",
            "productivity_style": "GTD methodology, heavy task management user"
        }
    }


def create_complex_events():
    """Create a complex set of events with different types and patterns."""
    return [
        # Work events
        "Weekly team retrospective meetings every Friday at 2pm",
        "Quarterly company all-hands meetings",
        "Annual team offsite in Portland (3 days)",
        "Monthly one-on-ones with manager",
        "Biweekly architecture review sessions",
        "Tech conference presentation at PyCon",
        
        # Personal recurring events
        "Rock climbing sessions at local gym 3x per week",
        "Weekly date nights with partner on Saturdays",
        "Monthly family video calls with parents",
        "Biweekly board game nights with friends",
        
        # Special occasions
        "Best friend's wedding in San Francisco",
        "Partner's birthday celebration weekend",
        "College reunion weekend in Boston",
        "Sister's baby shower in Portland",
        
        # Travel and adventures
        "Solo photography trip to Iceland",
        "Romantic getaway to Napa Valley",
        "Camping trip in Olympic National Park",
        "Business trip to client in Austin",
        
        # Learning and development
        "Online machine learning course completion",
        "Japanese language classes twice per week",
        "Photography workshop at local community center",
        "Sustainable living seminar series",
        
        # Health and wellness
        "Annual physical and health checkup",
        "Quarterly dental cleanings",
        "Monthly massage therapy sessions",
        "Weekly meal prep Sundays"
    ]


async def demonstrate_async_generation():
    """Demonstrate asynchronous data generation."""
    print("🔄 Demonstrating asynchronous generation...")
    
    config = create_custom_config()
    user_profile = create_detailed_user_profile()
    events = create_complex_events()
    
    agent = PersonaAgent(config)
    
    # Generate data asynchronously
    result = await agent.agenerate(user_profile, events)
    
    if result["success"]:
        print("✅ Async generation completed!")
        return result["output_path"]
    else:
        print(f"❌ Async generation failed: {result.get('error')}")
        return None


def demonstrate_validation_analysis(output_path: str):
    """Demonstrate detailed validation analysis."""
    print("\n🔍 Performing detailed validation analysis...")
    
    validator = SchemaValidator()
    
    # Get available schemas
    available_schemas = validator.get_available_schemas()
    print(f"Available schemas: {', '.join(available_schemas)}")
    
    # Analyze each schema
    for schema_name in available_schemas:
        schema_info = validator.get_schema_info(schema_name)
        
        if "error" not in schema_info:
            print(f"\n📋 {schema_name.title()} Schema:")
            print(f"  Title: {schema_info.get('schema_title', 'N/A')}")
            print(f"  Required fields: {len(schema_info.get('required_fields', []))}")
            print(f"  Optional fields: {len(schema_info.get('optional_fields', []))}")


def demonstrate_output_analysis(output_path: str):
    """Demonstrate output analysis and management."""
    print("\n📊 Analyzing generated output...")
    
    config = create_custom_config()
    output_manager = OutputManager(config)
    
    # Get output size information
    size_info = output_manager.get_output_size(output_path)
    
    print(f"Output Analysis:")
    print(f"  Total size: {size_info.get('total_size_mb', 0)} MB")
    print(f"  File count: {size_info.get('file_count', 0)}")
    
    # Show file sizes
    file_sizes = size_info.get('file_sizes', {})
    if file_sizes:
        print("\n  File sizes:")
        for filename, size_bytes in sorted(file_sizes.items(), key=lambda x: x[1], reverse=True):
            size_kb = round(size_bytes / 1024, 1)
            print(f"    {filename}: {size_kb} KB")
    
    # Create archive
    try:
        archive_path = output_manager.create_archive(output_path)
        print(f"\n📦 Created archive: {archive_path}")
    except Exception as e:
        print(f"❌ Failed to create archive: {str(e)}")


def demonstrate_batch_generation():
    """Demonstrate generating multiple personas in batch."""
    print("\n🎭 Demonstrating batch persona generation...")
    
    # Define multiple personas
    personas = [
        {
            "name": "Tech Entrepreneur",
            "profile": {
                "age": 35,
                "occupation": "Startup Founder",
                "location": "San Francisco, CA",
                "interests": ["entrepreneurship", "AI", "venture capital"],
                "lifestyle": "High-energy, travel-heavy, networking-focused"
            },
            "events": [
                "Pitch deck presentations to VCs",
                "Y Combinator demo day",
                "TechCrunch Disrupt conference",
                "Weekly founder dinners"
            ]
        },
        {
            "name": "Creative Professional", 
            "profile": {
                "age": 27,
                "occupation": "Graphic Designer",
                "location": "Brooklyn, NY",
                "interests": ["design", "art", "photography", "coffee"],
                "lifestyle": "Creative, freelance, community-oriented"
            },
            "events": [
                "Design conference in Barcelona",
                "Local art gallery openings",
                "Freelance client meetings",
                "Creative community meetups"
            ]
        }
    ]
    
    config = Config(
        openai_model=OpenAIModel.GPT_4O,
        data_volume={app: 8 for app in ["contacts", "calendar", "sms", "emails", "reminders", "alarms"]},
        enabled_apps=["contacts", "calendar", "sms", "emails", "reminders", "alarms"]
    )
    
    # Generate data for each persona
    results = []
    for persona in personas:
        print(f"\n👤 Generating data for {persona['name']}...")
        
        agent = PersonaAgent(config)
        result = agent.generate(persona["profile"], persona["events"])
        
        if result["success"]:
            print(f"✅ {persona['name']} generation completed")
            results.append({
                "name": persona["name"],
                "output_path": result["output_path"],
                "success": True
            })
        else:
            print(f"❌ {persona['name']} generation failed")
            results.append({
                "name": persona["name"],
                "error": result.get("error"),
                "success": False
            })
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n📈 Batch generation summary: {successful}/{len(personas)} personas completed successfully")
    
    for result in results:
        if result["success"]:
            print(f"  ✅ {result['name']}: {result['output_path']}")
        else:
            print(f"  ❌ {result['name']}: {result.get('error', 'Unknown error')}")


async def main():
    """Main function demonstrating advanced usage."""
    print("🚀 Persona Auto Gen - Advanced Usage Demo")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set your OPENAI_API_KEY environment variable")
        return
    
    try:
        # 1. Async generation
        output_path = await demonstrate_async_generation()
        
        if output_path:
            # 2. Validation analysis
            demonstrate_validation_analysis(output_path)
            
            # 3. Output analysis
            demonstrate_output_analysis(output_path)
        
        # 4. Batch generation
        demonstrate_batch_generation()
        
        print("\n🎉 Advanced demo completed!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo cancelled by user.")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())