# Meta Ally

A meta-agent framework for creating and configuring AI copilots using Pydantic AI.

## Project Structure

```
meta_ally/
├── src/meta_ally/          # Core package
│   ├── agents/             # Agent factory, presets, and configurations
│   │   ├── agent_factory.py
│   │   ├── agent_presets.py
│   │   ├── dependencies.py
│   │   ├── model_config.py
│   │   └── variation_agent.py
│   ├── auth/               # Authentication management
│   │   └── auth_manager.py
│   ├── eval/               # Evaluation framework
│   │   ├── analyze_reports.py
│   │   ├── api_test_hooks.py
│   │   ├── case_factory.py
│   │   ├── conversation_turns.py
│   │   ├── dataset_config.py
│   │   ├── dataset_hooks.py
│   │   ├── dataset_manager.py
│   │   ├── eval_tasks.py
│   │   ├── evaluation_suite.py
│   │   └── evaluators.py
│   ├── lib/                # Core libraries
│   │   └── openapi_to_tools.py
│   ├── mock/               # Mock services for testing
│   │   └── analytics_api_mock_service.py
│   ├── prompts/            # System prompts
│   │   └── system_prompts.py
│   ├── tools/              # Tool management
│   │   ├── context_tools.py
│   │   └── tool_group_manager.py
│   ├── ui/                 # User interface components
│   │   ├── conversation_saver.py
│   │   ├── human_approval_callback.py
│   │   ├── terminal_chat.py
│   │   └── visualization.py
│   └── util/               # Utilities and notebooks
│       └── *.ipynb
├── examples/               # Usage examples
│   ├── analytics_api_mock_service_example.py
│   ├── analyze_reports_example.py
│   ├── api_hooks_example.py
│   ├── case_factory_addone_example.py
│   ├── case_factory_website_analytics_example.py
│   ├── case_variants_visualization_example.py
│   ├── create_agent_example.py
│   ├── create_agi_ui_agent_example.py
│   ├── dataset_manager_addone_example.py
│   ├── dataset_manager_website_analytics_example.py
│   ├── evaluation_example.py
│   ├── evaluation_suite_example.py
│   └── terminal_chat_example.py
├── tests/                  # Test suite
│   ├── test_conversation_turns.py
│   ├── test_evaluators.py
│   ├── test_openapi_tools.py
│   └── test_tool_schemas.py
├── Data/                   # Test data and configurations
│   ├── add_one/            # Add one test cases
│   ├── analytics/          # Analytics test cases
│   ├── api_mock_data/      # Anonymized API data
│   └── UserRecords/        # Conversation records
├── docs/                   # Documentation
│   ├── Agent_Evaluation_Guide.md
│   └── Installation.md
├── evaluation_results/     # Evaluation outputs
└── pyproject.toml          # Project configuration
```

## Overview

### What is the idea behind a Meta Ally?

At the current stage, setting up a **Copilot** on our **configuration page** can be somewhat user-unfriendly and requires prior training or experience. For example, a layperson may struggle to understand why a **RAG** system is needed when building a copilot and what such a system is capable of.  

Even when a user does understand these things, creating and configuring a Copilot still involves **multiple complex steps** specific to our configuration page. These steps include:

- Creating an endpoint with **metadata**, such as a display name and route.  
- Configuring the endpoint by defining a **specific LLM**, **system prompt**, **greeting message**, **history reduction**, and **plugins**.  
- Defining **plugin configuration**, including **AI Knowledge**.  
- (Optional but common) Setting up **AI Knowledge**, which includes:
  - Creating one or more **sources**  
  - Combining sources into a **collection**  
  - **Indexing** the collection  
  - Configuring the plugin within the **copilot configuration**

![Meta Ally overview](docs/Images/image.png)

The goal of Meta Ally is to integrate all these steps and assist users in creating and configuring their own copilots easily. The Meta Ally behaves like an autonomous agent that can actively create and configure new endpoints with all required features while **explaining** each concept to the user along the way.

This project improves the usability of Ally's configuration process while exploring existing agent frameworks and contributing insights to improve the Ally project's codebase.

---

## Features

### OpenAPI to Tools Conversion

Meta Ally automatically converts OpenAPI specifications into Pydantic AI–compatible tools. The conversion handles:
- **Recursive resolution** of nested Pydantic models in request bodies
- **Type-safe** parameter descriptions fed directly to the agent
- Support for complex API operations from both Ally and AI Knowledge APIs

![API tools diagram](docs/Images/image-1.png)
![Tool definition example](docs/Images/image-2.png)

### Agent Framework

Built on **Pydantic AI**, Meta Ally provides:
- **Agent Factory**: Easy creation of agents by specifying prompts and curated tool sets
- **Agent Presets**: Pre-configured agents for common tasks
- **ReAct Pattern**: Built-in reasoning and action capabilities
- **Model Configuration**: Flexible LLM backend configuration
- **Variation Agents**: Support for testing different agent behaviors

### Comprehensive Evaluation Suite

The evaluation framework includes:
- **Multi-turn Conversation Testing**: Evaluate agents across entire conversations
- **Dataset Management**: Create and manage test datasets for specific user profiles
- **Case Factory**: Generate test cases from conversation snapshots
- **LLM Judges**: Automated evaluation using language models
- **Custom Evaluators**: Tool usage validation and custom metrics
- **Report Analysis**: Aggregate and analyze evaluation results
- **Logfire Integration**: Track performance metrics through Pydantic's observability platform

### User Interfaces

- **Terminal Chat**: Interactive command-line interface for agent interaction
- **AG-UI Support**: Convert agents to web applications using the AG-UI protocol
- **CopilotKit Integration**: Frontend interface for browser-based interaction
- **Conversation Saving**: Record and replay agent interactions
- **Human Approval**: Callback system for critical actions requiring user confirmation
- **Visualization**: Tools for visualizing case variants and evaluation results

### Mock Services

- **Analytics API Mock**: Testing without requiring live API access
- **Anonymized Data**: Sample data for development and testing

---

## Installation

See [Installation.md](docs/Installation.md) for detailed setup instructions.

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd meta_ally

# Install dependencies using uv
uv sync

# Run tests
uv run pytest tests

# Try an example
uv run python examples/terminal_chat_example.py
```

---

## Usage Examples

### Creating an Agent

```python
from meta_ally.agents.agent_factory import create_agent
from meta_ally.tools.tool_group_manager import ToolGroupManager

# Create an agent with specific tools
agent = create_agent(
    prompt="Help users create and configure copilots",
    tools=tool_manager.get_tools(['ally_config', 'ai_knowledge'])
)
```

### Running Evaluations

```python
from meta_ally.eval.evaluation_suite import run_evaluation

# Evaluate agent performance
results = run_evaluation(
    dataset_path="Data/add_one",
    agent=agent,
    evaluators=['llm_judge', 'tool_usage']
)
```

See the [examples/](examples/) directory for more detailed examples.

---

## Development History

### Initial Exploration

The project began by exploring the original Ally repository, identifying **lack of flexibility** when introducing new LLMs or providers as a key bottleneck. Initial attempts to extend the original Ally were reconsidered in favor of building a standalone version.

### Framework Selection

After researching frameworks including LangChain and Pydantic AI, **Pydantic AI** was chosen for its:
- Type-safe design
- Extensive documentation
- Natural integration with Pydantic models
- Built-in evaluation and observability features

### Implementation Progress

Development progressed through several key phases:

1. **Tool Generation**: Converting Ally and AI Knowledge APIs to Pydantic AI tools, handling recursive resolution of nested Pydantic models in request bodies
2. **Agent Creation**: Building agent factory and preset configurations using Pydantic AI's ReAct pattern
3. **UI Development**: Implementing terminal chat and AG-UI integration with CopilotKit as the frontend interface
4. **Evaluation Framework**: Creating comprehensive testing and evaluation system with multi-turn conversation support

---

## Evaluation & Observability

### Evaluation Framework

Evaluating agent performance is crucial. The evaluation system supports:
- **Message Histories**: Multi-turn conversation performance assessment
- **Datasets**: Created for specific user profiles to simulate full conversations
- **Cases**: Snapshots representing conversation states used to measure agent performance
- **LLM Judges**: Automated evaluation using language models
- **Custom Evaluators**: Comparing expected versus actual tool usage and other metrics

### Logfire Integration

**Logfire** is Pydantic's built-in observability platform. It collects traces from LLM applications and provides:
- Performance metrics through a web dashboard
- Evaluation experiment tracking and outcomes
- Detailed trace inspection

![Logfire evaluation view](docs/Images/image-3.png)

---



## Testing

```bash
# Run all tests
uv run pytest tests

# Run specific test file
uv run pytest tests/test_evaluators.py

# Run with coverage
uv run pytest --cov=src/meta_ally tests/
```

---

## Documentation

- [Installation Guide](docs/Installation.md)
- [Agent Evaluation Guide](docs/Agent_Evaluation_Guide.md)
- [Pydantic AI Documentation](pydantic_ai_full_llm_helper.txt)

---

## License

See project repository for license information.
