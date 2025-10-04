# Architecture Overview

## System Design

The autonomous agent framework uses a modular architecture with 100% LLM-driven decision making through LangGraph.

### Core Components

**1. Agent Core (`src/agent_core.py`)**
- LangGraph state machine with 3 nodes: Reasoning, Tool Execution, Response
- Recursion limit: 50 (allows ~20 tool executions)
- Max iterations: Configurable (default 10)
- No hardcoded logic - all routing decisions made by LLM

**2. MCP Client (`src/mcp_client.py`)**
- FastMCP Client integration (compatible with FastMCP servers)
- Supports STDIO transport (HTTP planned)
- Per-server client instances for clean isolation
- Async context manager lifecycle

**3. LLM Provider (`src/llm_provider.py`)**
- Anthropic Claude integration (default)
- Tool format conversion (MCP → Anthropic format)
- Configurable temperature and max_tokens
- Response parsing with tool call extraction

**4. Configuration (`src/config.py`)**
- 4-level precedence: CLI > Config File > Env > Defaults
- Validates all settings before execution
- Loads from agent.conf, .env, CLI arguments
- Supports --show-mcps and --list-tools flags

**5. Main Entry (`src/agent.py`)**
- Orchestrates all components
- Handles display flags (--show-mcps, --list-tools)
- Manages async lifecycle
- Error handling and logging

### Data Flow

```
1. Load Configuration
   ↓
2. Connect to MCP Servers → Discover Tools
   ↓  
3. Initialize LLM with Tool Definitions
   ↓
4. Execute LangGraph:
   ┌─ Reasoning (LLM decides action)
   │  ↓
   │  Tool needed? → Execute → Loop back
   │  ↓
   │  Complete? → Response → END
   └─ (Repeat until done or max limit)
```

### State Machine

```
Entry → Reasoning Node
           ↓
    Has tool calls?
      ↓         ↓
    Yes        No
      ↓         ↓
  Execute    Response → END
  Tools         
      ↓
  Reasoning (loop)
```

### Configuration Precedence

```
Highest → CLI Arguments (--llm-model)
   ↓      agent.conf ([llm] model = ...)
   ↓      Environment (.env ANTHROPIC_API_KEY)
Lowest → Defaults (claude-sonnet-4-5-20250929)
```

## Key Design Decisions

### 1. 100% LLM-Driven
- No hardcoded tool selection
- LLM decides which tools, when, and how
- Conditional routing based on LLM responses

### 2. FastMCP Integration
- itential-mcp uses FastMCP framework
- Standard MCP SDK incompatible
- FastMCP Client provides seamless compatibility

### 3. Modular Design
- Each component has single responsibility
- Clean interfaces between modules
- Easy to test and extend

### 4. Safety Limits
- Max iterations: 10 (configurable)
- Recursion limit: 50 (LangGraph internal)
- Timeouts on MCP connections
- Error handling throughout

## Technical Specifications

### Dependencies
- **LangGraph**: 0.2.45+ (agent framework)
- **FastMCP**: 2.0.0+ (MCP client)
- **Anthropic**: 0.39.0+ (Claude SDK)
- **LangChain**: 0.3.7+ (components)
- **91 total packages**

### MCP Servers
- **itential-mcp**: 24 tools (Itential Platform)
- **time**: 2 tools (time operations)
- **filesystem**: 14 tools (file operations)
- **browser**: HTTP (not implemented yet)

### Performance
- Startup: 1-2 seconds
- MCP connection: 2-3 seconds
- Tool discovery: <1 second
- LLM reasoning: 2-4 seconds/iteration
- Tool execution: 300ms-1s per tool

## Extension Points

### Adding New LLM Providers
Edit `src/llm_provider.py`:
```python
class NewProvider(LLMProvider):
    def chat(self, messages, system_prompt, tools):
        # Implementation
```

### Adding New MCP Servers
Edit `mcp_config.json`:
```json
{
  "new-server": {
    "command": "...",
    "args": [...]
  }
}
```
Tools discovered automatically.

### Modifying Agent Behavior
- Edit `prompts/agent_system.prompt`
- Or create custom prompt and use `--system-prompt`

### Adding HTTP Transport
Edit `src/mcp_client.py`:
```python
if transport_type == "http":
    # Add HTTP client implementation
    # Use httpx for async HTTP calls
```

## Troubleshooting

### Common Issues

**Recursion Limit**: Set in `agent_core.py` line 86
**Max Tokens**: Set in `agent.conf` [llm] section
**MCP Connection**: Check absolute paths in `mcp_config.json`
**Tool Discovery**: Verify server loads (check logs)

## Future Enhancements

See `docs/ENHANCEMENTS.md` for detailed roadmap.

Priority additions:
1. HTTP transport support (for browser MCP)
2. Conversation history persistence
3. Agent memory system
4. Web UI
