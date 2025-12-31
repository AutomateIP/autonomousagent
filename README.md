# Autonomous Agent Framework

An experimental autonomous agent framework with MCP (Model Context Protocol) support for learning and experimentation. This framework enables LLM-powered agents to autonomously execute complex tasks using dynamically discovered tools from MCP servers.

## What is this?

An autonomous AI agent that:
- 🤖 **Makes its own decisions** - The LLM autonomously chooses which tools to use and when
- 🔌 **Connects to MCP servers** - Discovers and uses tools from any MCP-compatible server
- 🔄 **Executes multi-step workflows** - Handles complex tasks requiring multiple tool calls
- 📝 **Logs everything** - Separate console and file logging for debugging and auditing

## Features

- 🤖 **LLM-Driven Decision Making** - Uses LangGraph for autonomous task execution
- 🔌 **MCP Support** - Connects to MCP servers (FastMCP, standard MCP)
- 🛠️ **Dynamic Tool Discovery** - Automatically finds and uses available tools
- ⚙️ **Flexible Configuration** - CLI > Config File > Env Variables > Defaults
- 🔄 **Multi-Step Reasoning** - Handles complex workflows autonomously
- 📊 **Structured Logging** - Separate console and file logging with configurable levels

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/AutomateIP/autonomousagent.git
cd autonomous_agent
uv sync

# 2. Configure API key
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY=your-key-here

# 3. Configure MCP servers (optional)
cp examples/mcp_config.json.example mcp_config.json
# Edit mcp_config.json with your MCP server paths

# 4. Run a simple task
uv run agent --agent-file tests/prompts/test_time.prompt
```

**📖 See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed setup guide**

## Prerequisites

- Python 3.11+
- UV package manager - [Install](https://github.com/astral-sh/uv)
- Anthropic API key - [Get key](https://console.anthropic.com/)

## Installation

```bash
# Install dependencies
uv sync

# Set up configuration files
cp .env.example .env
cp examples/mcp_config.json.example mcp_config.json
# Edit .env with your ANTHROPIC_API_KEY
# Edit mcp_config.json with your MCP server paths (use absolute paths)
```

**See [docs/QUICKSTART.md](docs/QUICKSTART.md) for step-by-step installation**

## Usage

### Basic Usage

```bash
# Run with default configuration (agent.conf and mcp_config.json)
uv run agent --agent-file <your-prompt-file>
```

### With Debug Logging

```bash
# Enable debug output to console and detailed file logging
uv run agent --agent-file task.prompt --debug
```

### Override Settings

```bash
# Use different model
uv run agent --agent-file task.prompt --llm-model claude-3-haiku-20240307

# Custom configuration file
uv run agent --config my.conf --agent-file task.prompt

# List available MCP servers
uv run agent --show-mcps

# List all available tools
uv run agent --list-tools
```

## Configuration

### Configuration Files

1. **agent.conf** - Agent settings (LLM, behavior, MCP)
2. **mcp_config.json** - MCP server definitions
3. **.env** - API keys and credentials

### Configuration Precedence

```
CLI Arguments > agent.conf > Environment Variables > Defaults
```

### Example agent.conf

```ini
[agent]
system_prompt = ./prompts/agent_system.prompt
# Console logging level (what you see in terminal)
console_log_level = ERROR
# File logging level (what gets written to logs/)
file_log_level = INFO
max_iterations = 15

[llm]
provider = anthropic
model = claude-sonnet-4-5-20250929
temperature = 0.7
max_tokens = 4096

[mcp]
config_file = ./mcp_config.json
itential_mcp_conf = ./itential-mcp.conf
timeout = 120
```

See [examples/agent.conf.example](examples/agent.conf.example) for full options.

### Logging Configuration

The agent supports separate console and file logging levels:

- **console_log_level**: Controls what appears in your terminal (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **file_log_level**: Controls what gets written to `logs/agent_TIMESTAMP.log`

Recommended setup:
- Console: `ERROR` (clean terminal output)
- File: `INFO` (detailed logs for debugging)

Log files are automatically created with timestamps in the `logs/` directory.

## Creating Prompts

Prompts are simple text files with instructions:

**Simple Prompt:**
```
What are the key principles of autonomous agent design?
```

**Multi-Step Prompt:**
```
1. Analyze the available tools
2. Recommend which tools to use for system monitoring
3. Explain your reasoning
```

**Tool-Specific Prompt:**
```
Check system health using available monitoring tools.
Report key metrics and any issues found.
```

**Best Practices:**
- Be specific about desired outcome
- Let agent decide HOW to accomplish task
- Mention specific tools if needed
- Request specific output formats (table, JSON, etc.)

**📖 See [docs/QUICKSTART.md](docs/QUICKSTART.md) for prompt creation guide**

## Project Structure

```
autonomous_agent/
├── src/                  # Source code
│   ├── agent.py          # Main entry point
│   ├── agent_core.py     # LangGraph state machine
│   ├── config.py         # Configuration management
│   ├── llm_provider.py   # LLM provider interface
│   └── mcp_client.py     # MCP server client
├── prompts/              # System prompts
├── tests/prompts/        # Test prompt files
├── examples/             # Example configurations
│   ├── agent.conf.example
│   ├── mcp_config.json.example
│   └── itential-mcp.conf.example
├── logs/                 # Generated log files (timestamped)
├── files/                # Agent workspace
│   └── templates/        # Report templates
├── docs/                 # Documentation
├── agent.conf            # Main configuration (not tracked in git)
├── mcp_config.json       # MCP server config (not tracked in git)
└── .env                  # API keys (not tracked in git)
```

**Note**: Configuration files with personal settings are not tracked in git. Use the example files in `examples/` as templates.

## MCP Servers

The agent can connect to any MCP server. Included servers:

- **itential-mcp** - Itential Platform integration (21 tools)
- **time** - Time and timezone operations
- **filesystem** - File system operations

### Adding MCP Servers

1. Add to `mcp_config.json`
2. Tools are discovered automatically
3. Use in prompts - agent will find and use them

**For Itential Platform**: See [docs/ITENTIAL_INTEGRATION.md](docs/ITENTIAL_INTEGRATION.md)

## Command-Line Reference

```bash
# Required
--agent-file PATH     # Path to prompt file

# Optional
--config PATH         # agent.conf path (default: ./agent.conf)
--mcp-config PATH     # MCP config override
--system-prompt PATH  # System prompt override
--llm-provider NAME   # anthropic or openai
--llm-model NAME      # Model identifier
--debug               # Enable debug logging
```

## Architecture

### How It Works

```
User Prompt → Agent Configuration → MCP Connection → Tool Discovery
    ↓
LLM Reasoning (decide action) → Execute Tools (if needed) → Generate Response
    ↑                                  │
    └──────────────────────────────────┘
    (Loop until task complete)
```

### Key Components

- **LangGraph State Machine** - Manages agent flow
- **FastMCP Client** - Connects to MCP servers
- **LLM Provider** - Anthropic Claude integration
- **Configuration System** - Multi-level precedence

**Design Principle**: 100% LLM-driven decisions, zero hardcoded logic

## Examples

Check `tests/prompts/` for working examples:

- `test_no_tools.prompt` - Agent reasoning without tools
- `test_itential_health.prompt` - Platform health check (with itential-mcp)
- `test_get_devices.prompt` - Device inventory retrieval
- `test_filesystem.prompt` - File operations
- `test_time.prompt` - Time queries
- `test_multi_step.prompt` - Complex workflows

## Documentation

- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
- **[docs/ITENTIAL_INTEGRATION.md](docs/ITENTIAL_INTEGRATION.md)** - Itential Platform integration
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[docs/ENHANCEMENTS.md](docs/ENHANCEMENTS.md)** - Future roadmap
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## Troubleshooting

### Quick Fixes

- **Import errors**: Run `uv sync`
- **API key errors**: Check `.env` file
- **MCP connection fails**: Verify paths in `mcp_config.json`
- **No output**: Enable `--debug` to see what's happening

**Full troubleshooting**: See [docs/QUICKSTART.md](docs/QUICKSTART.md#troubleshooting)

## Supported Models

**Anthropic (Recommended):**
- `claude-sonnet-4-20250514` (default - most capable)
- `claude-3-5-sonnet-20241022` (excellent reasoning)
- `claude-3-haiku-20240307` (fast & economical)

**OpenAI (Supported):**
- `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

Configure in `agent.conf` or use `--llm-model` flag.

## Performance

- **Startup**: 1-2 seconds
- **Tool Discovery**: 2-3 seconds
- **Simple Tasks**: 5-10 seconds
- **Complex Workflows**: 20-60 seconds

## Contributing

This is an experimental project for learning purposes. Feel free to fork and experiment! See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
- [FastMCP](https://gofastmcp.com) - MCP client library
- [Anthropic](https://www.anthropic.com/) - Claude LLM
- [Model Context Protocol](https://modelcontextprotocol.io/) - Universal tool protocol

## License

See LICENSE file for details.

---

**Purpose**: Learning and experimentation with autonomous agents and MCP
**Last Updated**: 2025-12-31

**Get Started**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
