# Persona Auto Gen

AI agent for generating realistic iPhone app user data using LangGraph.

## Overview

This project leverages **LangGraph**, **Python 3.11** and Poetry to build an AI agent capable of generating realistic synthetic user data across various first-party iPhone applications. The goal is to simulate lifelike digital footprints based on a user profile and a set of real-world events.

## 📱 Targeted iPhone Apps

The agent supports data generation for the following apps:

- **Contacts**
- **Calendar (iCal)**
- **SMS**
- **Emails**
- **Reminders**
- **Notes**
- **Wallet**
- **Alarms (Clock)**

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd persona-auto-gen

# Install dependencies
poetry install

# Set up environment variables
export OPENAI_API_KEY="your-api-key-here"
```

### Basic Usage
```
poetry env activate
poetry run python examples/basic_usage.py
```

```python
from persona_auto_gen import PersonaAgent
from persona_auto_gen.config import Config
from datetime import datetime

# Configure the agent
config = Config(
    openai_model="gpt-4",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 5, 31),
    data_volume={
        "contacts": 10,
        "calendar": 15,
        "sms": 25,
        "emails": 20,
        "reminders": 12,
        "notes": 8,
        "alarms": 6
    }
)

# Define user profile
user_profile = {
    "age": 28,
    "occupation": "Software Developer",
    "location": "San Francisco, CA",
    "interests": ["technology", "hiking", "coffee"]
}

# Define events
events = [
    "Attending a tech conference in Austin",
    "Weekly team standup meetings",
    "Friend's wedding in Napa Valley",
    "Monthly book club meetings",
    "Weekend hiking trips"
]

# Generate data
agent = PersonaAgent(config)
generated_data = agent.generate(user_profile, events)

# Output will be saved to ./output/user_profile_001/
```

## 🏗️ Architecture

The project uses LangGraph to orchestrate a multi-step workflow:

1. **Profile Analysis** - Analyze user profile and events
2. **Data Generation** - Generate synthetic data for each app
3. **Schema Validation** - Validate all generated data against JSON schemas
4. **Quality Reflection** - Evaluate realism and consistency
5. **Output Packaging** - Structure and save the final dataset

## 📁 Project Structure

```
persona-auto-gen/
├── src/persona_auto_gen/
│   ├── agents/          # LangGraph agent implementations
│   ├── generators/      # Data generators for each app
│   ├── schemas/         # JSON schemas for validation
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── examples/            # Usage examples
└── docs/                # Documentation
```

## 🔧 Configuration

Customize generation parameters in your config:

- **OpenAI Model**: Choose from available models (gpt-4, gpt-3.5-turbo, etc.)
- **Data Volume**: Specify entries per app
- **Timeframe**: Set start and end dates
- **Output Format**: Configure JSON structure

## 📊 Generated Data Structure

```
/output/user_profile_001/
├── contacts.json
├── calendar.json
├── sms.json
├── emails.json
├── reminders.json
├── notes.json
├── wallet.json
└── alarms.json
```

## 🧪 Testing

```bash
# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src/persona_auto_gen
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.