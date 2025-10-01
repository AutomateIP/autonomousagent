# Autonomous Agent Framework

A production-ready autonomous agent framework with universal MCP (Model Context Protocol) support. Uses LangGraph for intelligent decision-making and connects to MCP servers to execute tasks autonomously.

## Features

- 🤖 **100% LLM-Driven** - All decisions made autonomously through LangGraph
- 🔌 **Universal MCP Support** - Works with any MCP server (FastMCP, standard MCP)
- 🛠️ **Dynamic Tool Discovery** - Automatically finds and uses available tools
- ⚙️ **Flexible Configuration** - CLI > Config File > Env Variables > Defaults
- 🔄 **Multi-Step Reasoning** - Handles complex workflows autonomously
- 📊 **Production Ready** - Tested, documented, and battle-tested

## Quick Start

```bash
# 1. Install
cd autonomous-agent && uv sync

# 2. Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 3. Run
uv run python -m src.agent --agent-file tests/prompts/test_no_tools.prompt --mcp-config mcp_config_empty.json
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

# Set up configuration
cp .env.example .env
cp agent.conf.example agent.conf
# Edit files with your settings
```

**See [docs/QUICKSTART.md](docs/QUICKSTART.md) for step-by-step installation**

## Usage

### Basic Usage

```bash
uv run python -m src.agent --agent-file <your-prompt-file>
```

### With Debug Logging

```bash
uv run python -m src.agent --agent-file task.prompt --debug
```

### Override Settings

```bash
# Use different model
uv run python -m src.agent --agent-file task.prompt --llm-model claude-3-haiku-20240307

# Custom configuration
uv run python -m src.agent --config my.conf --agent-file task.prompt
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
log_level = INFO
max_iterations = 10

[llm]
provider = anthropic
model = claude-sonnet-4-20250514
temperature = 0.7
max_tokens = 4096

[mcp]
config_file = ./mcp_config.json
timeout = 120
```

See `agent.conf.example` for full options.

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
autonomous-agent/
├── src/                  # Source code (6 modules)
├── mcps/                 # MCP servers
├── prompts/              # System prompts  
├── tests/prompts/        # Test prompt files
├── examples/             # Example configurations
├── logs/                 # Log output
├── docs/                 # Documentation
├── agent.conf            # Main configuration
├── mcp_config.json       # MCP server config
└── .env                  # API keys
```

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
- **[docs/ITENTIAL_INTEGRATION.md](docs/ITENTIAL_INTEGRATION.md)** - Itential Platform integration
- **[docs/ENHANCEMENTS.md](docs/ENHANCEMENTS.md)** - Future roadmap
- **[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)** - Implementation status
- **[session_summary/IMPLEMENTATION_SESSION.md](session_summary/IMPLEMENTATION_SESSION.md)** - Build session notes

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

Contributions welcome! Please:
1. Keep LLM-driven philosophy (no hardcoded logic)
2. Add tests for new features
3. Update documentation
4. Follow existing code style

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
- [FastMCP](https://gofastmcp.com) - MCP client library
- [Anthropic](https://www.anthropic.com/) - Claude LLM
- [Model Context Protocol](https://modelcontextprotocol.io/) - Universal tool protocol

## License

See LICENSE file for details.

---

**Version**: 0.1.0  
**Status**: Production Ready ✅  
**Last Updated**: 2025-10-01

**Get Started**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
