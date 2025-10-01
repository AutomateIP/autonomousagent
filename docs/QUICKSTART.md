# Quick Start Guide

Get up and running with the Autonomous Agent Framework in 5 minutes.

## Prerequisites

- Python 3.11+ installed
- UV package manager installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Anthropic API key: [Get one here](https://console.anthropic.com/)

## Installation

### Step 1: Install Dependencies

```bash
cd autonomous-agent
uv sync
```

This installs all 91 required packages (~30 seconds).

### Step 2: Configure API Key

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

### Step 3: Test the Agent

```bash
# Test basic agent (no tools)
uv run python -m src.agent \
  --agent-file tests/prompts/test_no_tools.prompt \
  --mcp-config mcp_config_empty.json
```

**Expected output**: Agent explains what an autonomous agent is (takes ~5 seconds).

## Your First Custom Task

### Create a Prompt File

```bash
echo "What are the key principles of good software design?" > my_first_task.prompt
```

### Run the Agent

```bash
uv run python -m src.agent --agent-file my_first_task.prompt --mcp-config mcp_config_empty.json
```

**Result**: Agent will provide a thoughtful, detailed response!

## Next Steps

### Enable MCP Tools

To use MCP servers (like itential-mcp, time, filesystem):

1. **Configure MCP server** (if using itential-mcp):
```bash
cp itential-mcp.conf.example itential-mcp.conf
# Edit itential-mcp.conf with your credentials
```

2. **Update mcp_config.json paths** to use absolute paths

3. **Run with tools enabled**:
```bash
uv run python -m src.agent --agent-file tests/prompts/test_itential_health.prompt
```

### Customize Agent Behavior

Edit `agent.conf` to change:
- **Model**: `claude-3-haiku-20240307` (faster/cheaper)
- **Temperature**: `0.3` (more focused) or `0.9` (more creative)
- **Max iterations**: `15` (allow more reasoning steps)

```bash
# Run with custom config
uv run python -m src.agent --agent-file my_task.prompt
```

### Create Your Own Prompts

**Simple prompt** (`examples/simple.prompt`):
```
Explain the benefits of autonomous agents in 3 bullet points.
```

**Multi-step prompt** (`examples/complex.prompt`):
```
1. Summarize what autonomous agents can do
2. List 3 use cases for businesses
3. Provide recommendations for getting started
```

Run it:
```bash
uv run python -m src.agent --agent-file examples/simple.prompt --mcp-config mcp_config_empty.json
```

## Common Commands

```bash
# Basic execution
uv run python -m src.agent --agent-file task.prompt

# With debug logging
uv run python -m src.agent --agent-file task.prompt --debug

# Use faster model
uv run python -m src.agent --agent-file task.prompt --llm-model claude-3-haiku-20240307

# Without MCP tools
uv run python -m src.agent --agent-file task.prompt --mcp-config mcp_config_empty.json
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set in environment"
- Check `.env` file exists
- Verify API key is set correctly
- Ensure no extra spaces or quotes

### "Agent file not found"
- Check file path is correct
- Use relative or absolute path
- Verify file exists: `ls -l your-file.prompt`

### Agent takes a long time
- This is normal for complex tasks
- MCP servers take time to load tools
- LLM reasoning can take 2-4 seconds per step
- Use `--debug` to see what's happening

### ModuleNotFoundError
- Run `uv sync` to install all dependencies
- Verify Python 3.11+ is installed

## Next Reading

- **README.md** - Full user guide
- **docs/ITENTIAL_INTEGRATION.md** - Using itential-mcp (if applicable)
- **docs/ENHANCEMENTS.md** - Future features
- **agent.conf** - Configuration options

## Success!

You now have a working autonomous agent! The agent can:
- ✅ Reason about tasks
- ✅ Make autonomous decisions
- ✅ Execute multi-step workflows
- ✅ Connect to MCP servers for tools
- ✅ Generate intelligent responses

Start creating your own prompts and let the agent work autonomously!
