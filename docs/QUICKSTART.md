# Quick Start Guide

Get up and running with the Autonomous Agent Framework in 5 minutes.

## Prerequisites

- Python 3.11+ installed
- UV package manager installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- API key for your chosen LLM provider (see [Supported Providers](#supported-llm-providers))

## Installation

### Step 1: Clone and Install Dependencies

```bash
git clone https://github.com/AutomateIP/autonomousagent.git
cd autonomous_agent
uv sync
```

This installs all required packages (~30 seconds).

### Step 2: Configure API Key

```bash
cp .env.example .env
```

Edit `.env` and add your API key for your chosen provider:
```bash
# For Anthropic (Claude) - Recommended
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Or for OpenAI (GPT)
# OPENAI_API_KEY=sk-your-actual-key-here

# Or for Google (Gemini)
# GEMINI_API_KEY=your-actual-key-here

# Or for AWS Bedrock
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_REGION_NAME=us-east-1

# Or for Ollama (local - no API key needed)
```

### Step 3: Configure MCP Servers

```bash
cp examples/mcp_config.json.example mcp_config.json
```

Edit `mcp_config.json` and update paths to use **absolute paths** for your system.

### Step 4: Test the Agent

```bash
# Test with time server
uv run agent --agent-file tests/prompts/test_time.prompt
```

**Expected output**: Agent will tell you the current time using the time MCP server (takes ~5-10 seconds).

## Your First Custom Task

### Create a Prompt File

```bash
echo "What are the key principles of good software design?" > my_first_task.prompt
```

### Run the Agent

```bash
uv run agent --agent-file my_first_task.prompt
```

**Result**: Agent will provide a thoughtful, detailed response!

## Next Steps

### Configure Itential MCP (Optional)

If you want to use the Itential Platform integration:

1. **Configure Itential MCP server**:
```bash
cp examples/itential-mcp.conf.example itential-mcp.conf
# Edit itential-mcp.conf with your Itential Platform credentials
```

2. **Test Itential integration**:
```bash
uv run agent --agent-file tests/prompts/test_itential_health.prompt
```

### Customize Agent Behavior

Edit `agent.conf` to change:
- **Logging**:
  - `console_log_level = ERROR` (clean terminal output)
  - `file_log_level = INFO` (detailed logs in logs/ directory)
- **Model**: `claude-3-haiku-20240307` (faster/cheaper) or `claude-opus-4-5-20251101` (most capable)
- **Temperature**: `0.3` (more focused) or `0.9` (more creative)
- **Max iterations**: `15` (allow more reasoning steps)

The agent uses `agent.conf` by default. All settings can be overridden via CLI arguments.

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
uv run agent --agent-file examples/simple.prompt
```

## Common Commands

```bash
# Basic execution
uv run agent --agent-file task.prompt

# With debug logging (shows everything in console and file)
uv run agent --agent-file task.prompt --debug

# Use different model
uv run agent --agent-file task.prompt --llm-model claude-3-haiku-20240307

# List available MCP servers
uv run agent --show-mcps

# List all available tools
uv run agent --list-tools

# View log files (detailed execution information)
tail -f logs/agent_*.log
```

## Supported LLM Providers

This framework supports 100+ LLM providers through [LiteLLM](https://docs.litellm.ai/docs/). Here are the most common:

### Anthropic (Claude) - Recommended
- Best for complex reasoning and tool use
- Models: `claude-sonnet-4-5-20250929`, `claude-3-5-sonnet-20241022`
- Get API key: [console.anthropic.com](https://console.anthropic.com/)

### OpenAI (GPT)
- Popular and widely available
- Models: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Get API key: [platform.openai.com](https://platform.openai.com/)

### Google (Gemini)
- Google's flagship model
- Models: `gemini/gemini-pro`, `gemini/gemini-1.5-pro`
- Get API key: [makersuite.google.com](https://makersuite.google.com/app/apikey)

### AWS Bedrock
- Access to multiple providers through AWS
- Models: `bedrock/anthropic.claude-v2`, `bedrock/anthropic.claude-3-sonnet-20240229-v1:0`
- Setup: [docs.aws.amazon.com/bedrock](https://docs.aws.amazon.com/bedrock/)

### Ollama (Local)
- Run models locally on your machine
- Models: `ollama/llama2`, `ollama/mistral`, `ollama/codellama`
- Install: [ollama.ai](https://ollama.ai/)

### Switching Providers

Edit `agent.conf`:
```ini
[llm]
provider = openai  # Change to your provider
model = gpt-4      # Change to your model
```

And ensure the corresponding API key is set in `.env`.

## Troubleshooting

### "ANTHROPIC_API_KEY not set in environment" (or similar for other providers)
- Check `.env` file exists
- Verify API key is set correctly
- Ensure no extra spaces or quotes
- Verify you're using the correct environment variable name for your provider

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
