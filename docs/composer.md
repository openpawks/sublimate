# Sublimate Composer

## Overview

The Sublimate Composer is the core orchestration engine for managing AI agents in the Sublimate system. It provides a framework for defining, configuring, and running multiple AI agents that can work together on software development tasks. The composer handles agent lifecycle management, heartbeat scheduling (cron-based execution), and pipeline-based workflows.

### Key Features

- **Agent Management**: Create and manage multiple AI agents with different roles and capabilities
- **Heartbeat Scheduling**: Run agents on cron schedules for automated background tasks
- **Pipeline Orchestration**: Chain agents together in sequential workflows
- **Configuration-Driven**: Define agents and workflows using YAML configuration files
- **Tool Integration**: Extend agent capabilities with custom tools
- **Dependency Management**: Agents can depend on each other's outputs

## Table of Contents

1. [Architecture](#architecture)
2. [Installation & Setup](#installation--setup)
3. [Configuration](#configuration)
   - [sublimate-compose.yml Schema](#sublimate-composeyml-schema)
   - [Agent Configuration](#agent-configuration)
   - [Model Configuration](#model-configuration)
   - [Heartbeat Configuration](#heartbeat-configuration)
4. [Core Classes](#core-classes)
   - [BaseAgent](#baseagent)
   - [BaseComposer](#basecomposer)
   - [Heartbeat](#heartbeat)
   - [HeartbeatComposer](#heartbeatcomposer)
   - [PipelineComposer](#pipelinecomposer)
5. [Usage Examples](#usage-examples)
   - [Basic Agent Setup](#basic-agent-setup)
   - [Heartbeat Scheduling](#heartbeat-scheduling)
   - [Custom Tools](#custom-tools)
6. [Testing](#testing)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

## Architecture

The Composer system follows a layered architecture:

```
┌─────────────────────────────────────────────┐
│            Configuration Layer              │
│        (sublimate-compose.yml)             │
└─────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────┐
│            Orchestration Layer              │
│        (BaseComposer/HeartbeatComposer)     │
└─────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────┐
│             Agent Layer                     │
│        (BaseAgent with Tools)               │
└─────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────┐
│             Execution Layer                 │
│        (LangChain + LLM Providers)          │
└─────────────────────────────────────────────┘
```

### Component Relationships

- **Composer**: Loads configuration, initializes models and agents
- **Agents**: Individual AI workers with specific prompts and tools
- **Heartbeats**: Scheduled execution triggers for agents
- **Models**: LLM configurations (Ollama, OpenAI, etc.)
- **Tools**: Python functions that agents can call to interact with the system

## Installation & Setup

### Prerequisites

- Python 3.12+
- Required packages (from `pyproject.toml`):
  - `langchain[ollama]`
  - `croniter`
  - `pyyaml`
  - `pytest` (for testing)

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd paperclip-clone/master
   ```

2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Create an agent home directory:
   ```bash
   mkdir -p my_agents
   cp agent_templates/default/* my_agents/
   ```

4. Configure your `sublimate-compose.yml`:
   ```yaml
   models:
     default-model:
       model_provider: ollama
       model: qwen3.5:0.8b
   
   agents:
     coder:
       model: default-model
       tools: [write_file, read_file]
   
   heartbeats:
     coder:
       schedule: "*/30 * * * *"
   ```

5. Run the composer:
   ```python
   from src.composer.composer import HeartbeatComposer
   
   composer = HeartbeatComposer("my_agents", {})
   composer.init()
   composer.up()
   ```

## Configuration

### sublimate-compose.yml Schema

The configuration file defines models, agents, and their execution schedules. It must be placed in your agent home directory.

#### Required Sections

1. **models**: LLM configurations
2. **agents**: Agent definitions
3. **heartbeats** OR **pipeline**: Execution strategy

#### Full Schema Example

```yaml
models:
  favorite-model:
    model_provider: ollama
    model: qwen3.5:0.8b
    temperature: 0.4
    
  other-model:
    model_provider: ollama
    model: qwen3.5:0.8b

agents:
  main:
    model: favorite-model
    handoffs: [main, coder, tester]
    allow_tools: [write_file, read_file, create_task, close_task]
    deny_tools: [dangerously_run_commands]
    file_access: ["./*"]
    read_only_file_access: ["./tests/*"]
    deny_file_access: ["./private/*"]
    description: "Project Lead Orchestrator"
    path: ./main.md
    
  coder:
    model: other-model
    tools: [write_file, read_file]
    
  tester:
    model: other-model
    tools: [run_tests]

heartbeats:
  main:
    schedule: "* 1 * * *"
    timeout: 30s
    dependencies: [coder, tester]
    path: ./heartbeats/main_heartbeat.md
    
  coder:
    schedule: "30 * * * *"
    
  tester:
    schedule: "30 * * * *"
    dependencies: [coder]
```

### Model Configuration

Each model entry configures an LLM provider:

```yaml
model-name:
  model_provider: ollama  # or "openai", "anthropic", etc.
  model: qwen3.5:0.8b     # model identifier
  temperature: 0.4        # optional, default varies by provider
  # Other provider-specific parameters
```

Supported providers follow LangChain's `init_chat_model` interface. The `api_key` is automatically fetched from the system environment or database.

### Agent Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Reference to a model defined in `models` section |
| `tools` | list | No | List of tool names the agent can use |
| `handoffs` | list | No | Agents this agent can hand off tasks to |
| `allow_tools` | list | No | Explicitly allowed tools (overrides default) |
| `deny_tools` | list | No | Tools this agent cannot use |
| `file_access` | list | No | File patterns the agent can access |
| `read_only_file_access` | list | No | File patterns the agent can read but not write |
| `deny_file_access` | list | No | File patterns the agent cannot access |
| `description` | string | No | Human-readable description of agent's role |
| `path` | string | No | Path to agent's prompt file (defaults to `./{agent_name}.md`) |

### Heartbeat Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schedule` | string | Yes | Cron expression for execution schedule |
| `timeout` | string | No | Maximum execution time (e.g., "30s", "5m") |
| `dependencies` | list | No | Other heartbeats that must complete first |
| `path` | string | No | Path to heartbeat-specific instructions |

## Core Classes

### BaseAgent

The `BaseAgent` class represents an individual AI agent with its own prompt, tools, and context.

#### Key Methods

- `__init__(name, agent_home, model, tools, root_folder)`: Initialize agent
- `load_agent()`: Load prompt and heartbeat files
- `format_message_history(message_history, **kwargs)`: Format messages with context
- `invoke(message_history, **kwargs)`: Synchronous agent invocation
- `ainvoke(message_history, **kwargs)`: Asynchronous agent invocation
- `add_dependency(agent)`: Add another agent as dependency

#### Agent Files

Each agent requires:
1. **Prompt file**: `{agent_home}/{name}.md` - Main instructions and role definition
2. **Heartbeat file**: `{agent_home}/heartbeats/{name}.md` - Instructions for scheduled execution

Additional context is loaded from:
- `{root_folder}/AGENTS.md`
- `{root_folder}/README.md`
- `{root_folder}/../docs/*`

#### Example Agent Prompt

```markdown
# Coder Agent

You are an expert software developer. Your responsibilities include:

- Writing clean, maintainable code
- Following existing patterns in the codebase
- Writing comprehensive tests
- Documenting your changes

## Constraints

- Only modify files in the allowed directories
- Run tests before committing changes
- Ask for clarification if requirements are ambiguous
```

### BaseComposer

The `BaseComposer` class orchestrates multiple agents based on configuration.

#### Key Methods

- `__init__(agent_home, tools, root_folder)`: Initialize composer with configuration
- `init_chat_models()`: Initialize all configured LLM models
- `init_agents()`: Initialize all configured agents
- `init()`: Initialize both models and agents
- `get_agent(name)`: Retrieve an agent by name
- `get_heartbeats_from_settings()`: Get heartbeat configurations
- `up()`: Start all agents (abstract, implemented by subclasses)
- `down()`: Stop all agents (abstract, implemented by subclasses)

#### Error Handling

- `FileNotFoundError`: Raised if `sublimate-compose.yml` is missing
- `KeyError`: Raised if required sections (models, agents, heartbeats/pipeline) are missing

### Heartbeat

The `Heartbeat` class manages scheduled execution of an agent.

#### Key Methods

- `__init__(agent, cron)`: Initialize with agent and cron schedule
- `get_next()`: Get next execution time using `croniter`
- `wait_until_datetime(target_datetime)`: Async sleep until target time
- `beat()`: Synchronous heartbeat execution
- `abeat()`: Asynchronous heartbeat execution
- `start()`: Start heartbeat daemon (continuous execution)
- `stop()`: Stop heartbeat daemon

#### Execution Flow

```
start() → daemon() loop:
  1. wait_until_datetime(get_next())
  2. abeat() → agent.ainvoke(context)
  3. Repeat
```

### HeartbeatComposer

Extends `BaseComposer` to manage heartbeat-scheduled agents.

#### Key Methods

- `__init__(agent_home, tools, root_folder)`: Initialize with heartbeat support
- `init_heartbeats()`: Initialize all heartbeats from configuration
- `get_active_heartbeats()`: Get currently running heartbeats
- `get_inactive_heartbeats()`: Get stopped heartbeats
- `start_heartbeat(name)`: Start a specific heartbeat
- `stop_heartbeat(name)`: Stop a specific heartbeat
- `up()`: Start all configured heartbeats

#### Lifecycle Management

```python
composer = HeartbeatComposer("my_agents", {})
composer.init()           # Initialize models, agents, heartbeats
composer.up()             # Start all heartbeats
# ... run for some time ...
composer.stop_heartbeat("coder")  # Stop specific heartbeat
composer.start_heartbeat("tester") # Start another
```

### PipelineComposer

*Note: Currently a stub implementation - pipeline functionality is planned for future releases.*

Extends `BaseComposer` to manage sequential agent execution pipelines.

## Usage Examples

### Basic Agent Setup

```python
from src.composer.composer import BaseComposer
from unittest.mock import Mock

# Define custom tools
def write_file(path, content):
    """Write content to a file."""
    with open(path, 'w') as f:
        f.write(content)
    return f"Written to {path}"

def read_file(path):
    """Read content from a file."""
    with open(path, 'r') as f:
        return f.read()

tools = {
    'write_file': write_file,
    'read_file': read_file
}

# Initialize composer
composer = BaseComposer(
    agent_home="./agent_templates/default",
    tools=tools
)

# Initialize models and agents
composer.init()

# Get an agent
coder = composer.get_agent("coder")

# Invoke the agent
response = coder.invoke([
    {"role": "user", "content": "Create a hello world script"}
])
print(response)
```

### Heartbeat Scheduling

```python
from src.composer.composer import HeartbeatComposer
import asyncio

async def run_heartbeats():
    composer = HeartbeatComposer(
        agent_home="./agent_templates/default",
        tools={}
    )
    
    composer.init()
    
    # Start all heartbeats
    composer.up()
    
    # Run for 5 minutes
    await asyncio.sleep(300)
    
    # Stop specific heartbeat
    composer.stop_heartbeat("coder")
    
    # Check status
    active = composer.get_active_heartbeats()
    print(f"Active heartbeats: {len(active)}")

# Run in async context
asyncio.run(run_heartbeats())
```

### Custom Tools Integration

```python
from src.composer.composer import BaseComposer
from langchain.tools import tool
import subprocess

@tool
def run_tests(test_path: str) -> str:
    """Run tests at the specified path."""
    result = subprocess.run(
        ["pytest", test_path],
        capture_output=True,
        text=True
    )
    return f"Exit code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"

@tool  
def git_status() -> str:
    """Check git status."""
    result = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True,
        text=True
    )
    return result.stdout

tools = {
    'run_tests': run_tests,
    'git_status': git_status
}

composer = BaseComposer("./my_agents", tools)
composer.init()
```

### Error Handling

```python
from src.composer.composer import BaseComposer
import tempfile
import os

# Test missing configuration
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        composer = BaseComposer(tmpdir, {})
except FileNotFoundError as e:
    print(f"Expected error: {e}")

# Test invalid configuration
try:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "sublimate-compose.yml")
        with open(config_path, 'w') as f:
            f.write("agents: {}")  # Missing models section
        
        composer = BaseComposer(tmpdir, {})
except KeyError as e:
    print(f"Expected error: {e}")
```

## Testing

The composer module includes comprehensive tests using pytest and extensive mocking to avoid real API calls.

### Running Tests

```bash
# Run all composer tests
pytest tests/test_composer.py -v

# Run specific test class
pytest tests/test_composer.py::TestBaseAgent -v

# Run with coverage
pytest tests/test_composer.py --cov=src.composer.composer
```

### Test Structure

- **TestBaseAgent**: Tests agent initialization, file loading, and invocation
- **TestBaseComposer**: Tests composer initialization and configuration validation
- **TestHeartbeat**: Tests heartbeat scheduling and execution
- **TestHeartbeatComposer**: Tests heartbeat orchestration

### Mocking Strategy

Tests use several autouse fixtures in `tests/conftest.py`:

```python
# Mock external API calls
@pytest.fixture(autouse=True)
def mock_init_chat_model():
    with patch("langchain.chat_models.init_chat_model") as mock:
        mock_model = MagicMock()
        mock_model.name = "mock-ollama-model"
        mock.return_value = mock_model
        yield mock

# Mock agent creation
@pytest.fixture(autouse=True)
def mock_create_agent():
    with patch("langchain.agents.create_agent") as mock:
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = "Mocked agent.invoke()"
        mock_agent.ainvoke.return_value = "Mocked agent.ainvoke()"
        mock.return_value = mock_agent
        yield mock
```

### Writing New Tests

When adding new functionality:

1. Use existing mocking patterns to avoid real API calls
2. Test both success and error cases
3. Mock async methods with `AsyncMock` when needed
4. Follow the established test structure

Example test pattern:

```python
def test_new_feature(self):
    with patch("module.to.mock") as mock:
        mock.return_value = expected_value
        result = self.object.method_under_test()
        assert result == expected_value
        mock.assert_called_once_with(expected_args)
```

## API Reference

### BaseAgent

#### `__init__(name: str, agent_home: Union[str, Path], model, tools: List = [], root_folder: str = "")`
Initialize a new agent.

**Parameters:**
- `name`: Unique identifier for the agent
- `agent_home`: Directory containing agent configuration files
- `model`: LangChain chat model instance
- `tools`: List of tools the agent can use
- `root_folder`: Root directory for context files

#### `load_agent() → None`
Load agent prompt, heartbeat, and context files.

**Raises:**
- `FileNotFoundError`: If required files are missing

#### `format_message_history(message_history: List[Dict], **kwargs) → Dict`
Format message history with agent context.

**Parameters:**
- `message_history`: List of message dictionaries with 'role' and 'content'
- `**kwargs`: Boolean flags to control context inclusion:
  - `include_prompt` (True): Include agent prompt
  - `include_heartbeat` (True): Include heartbeat instructions
  - `include_context_files` (True): Include context files
  - `include_dependencies` (True): Include dependency states

**Returns:** Dictionary with "messages" key containing formatted messages

### BaseComposer

#### `__init__(agent_home: Union[str, Path], tools: Dict[str, Callable], root_folder: str = "")`
Initialize composer with configuration.

**Parameters:**
- `agent_home`: Directory containing `sublimate-compose.yml`
- `tools`: Dictionary mapping tool names to callable functions
- `root_folder`: Root directory for project context

**Raises:**
- `FileNotFoundError`: If `sublimate-compose.yml` not found
- `KeyError`: If configuration missing required sections

#### `fetch_api_key_for_provider(provider: str) → str`
Fetch API key for LLM provider.

**Parameters:**
- `provider`: LLM provider name (e.g., "ollama", "openai")

**Returns:** API key string

*Note: Currently returns dummy key - implement database/secret lookup*

### Heartbeat

#### `__init__(agent: BaseAgent, cron: str)`
Initialize heartbeat for agent.

**Parameters:**
- `agent`: Agent to execute on schedule
- `cron`: Cron expression for execution schedule

#### `start() → asyncio.Task`
Start heartbeat daemon.

**Returns:** asyncio Task for the daemon

**Raises:**
- `RuntimeError`: If heartbeat already running

#### `stop() → Optional[bool]`
Stop heartbeat daemon.

**Returns:** Result of task cancellation, or None if not running

## Troubleshooting

### Common Issues

#### Configuration Errors

**Problem:** `KeyError: "You need to have: models, agents and either heartbeats OR a pipeline to run compose."`

**Solution:** Ensure your `sublimate-compose.yml` has all required sections:
```yaml
models:
  default: {model_provider: ollama, model: qwen3.5:0.8b}
agents:
  main: {model: default}
heartbeats:
  main: {schedule: "* * * * *"}
```

#### File Not Found Errors

**Problem:** `FileNotFoundError: {agent_home}/sublimate-compose.yml not found!`

**Solution:**
1. Verify the agent_home directory exists
2. Ensure `sublimate-compose.yml` is in that directory
3. Check file permissions

#### Agent Initialization Failures

**Problem:** Agent fails to load prompt or heartbeat files

**Solution:**
1. Check that `{agent_home}/{name}.md` exists
2. Check that `{agent_home}/heartbeats/{name}.md` exists
3. Verify file encoding (UTF-8)

#### Heartbeat Scheduling Issues

**Problem:** Heartbeats not executing at expected times

**Solution:**
1. Verify cron syntax (e.g., `"* * * * *"` for每分钟)
2. Check system timezone
3. Ensure asyncio event loop is running

### Debugging Tips

1. **Enable verbose logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check agent state:**
   ```python
   agent = composer.get_agent("coder")
   print(f"Prompt: {agent.prompt[:100]}...")
   print(f"Heartbeat: {agent.heartbeat[:100]}...")
   print(f"Context files: {len(agent.context)}")
   ```

3. **Test heartbeat manually:**
   ```python
   heartbeat = composer.get_heartbeat("main")
   result = heartbeat.beat()  # Synchronous execution
   print(f"Heartbeat result: {result}")
   ```

4. **Validate configuration:**
   ```python
   import yaml
   with open("my_agents/sublimate-compose.yml") as f:
       config = yaml.safe_load(f)
       print(yaml.dump(config, default_flow_style=False))
   ```

## Contributing

When contributing to the composer module:

1. Follow existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Ensure all tests pass before submitting

### Code Organization

- `src/composer/composer.py`: Main implementation
- `tests/test_composer.py`: Unit tests
- `tests/conftest.py`: Test fixtures and mocking
- `agent_templates/default/`: Example configurations
- `docs/composer.md`: This documentation

## Future Enhancements

Planned improvements for the composer system:

1. **PipelineComposer Implementation**: Full pipeline orchestration
2. **Database Integration**: Store agent states and execution history
3. **Web Dashboard**: Monitor agent status and outputs
4. **Plugin System**: Easy tool and agent extension
5. **Distributed Execution**: Run agents across multiple machines
6. **Resource Management**: Limit agent resource consumption
7. **Version Control Integration**: Git operations as first-class tools

## License

[Include appropriate license information]

## Support

For issues, questions, or contributions:
- GitHub Issues: [Repository URL]/issues
- Documentation: [Repository URL]/docs
- Community: [Community forum/channel]