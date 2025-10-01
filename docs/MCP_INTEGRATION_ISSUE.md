# MCP Integration Issue with itential-mcp

**Date**: 2025-10-01  
**Status**: Under Investigation

## Problem Summary

The autonomous agent successfully integrates with the MCP Python SDK (v1.15.0) but encounters an initialization issue specifically with itential-mcp where tools cannot be discovered.

## Symptoms

```
2025-10-01 15:20:28,920: [itential-mcp] INFO: Dynamic tool bindings is now complete
INFO:__main__:Listing tools...
WARNING:root:Failed to validate request: Received request before initialization was complete
mcp.shared.exceptions.McpError: Invalid request parameters
```

## What Works

- ✅ Agent core functionality (tested successfully)
- ✅ MCP STDIO connection established
- ✅ Server process spawns correctly
- ✅ Server loads all 68 tools successfully (~2 seconds)
- ✅ Session context managers enter correctly
- ✅ Connection stays alive (no crashes)

## What Doesn't Work

- ❌ Tool discovery via `session.list_tools()` always fails with "before initialization was complete"
- ❌ Even after waiting 10+ seconds after server reports "complete"
- ❌ Server never responds to MCP protocol messages

## Testing Done

### Test 1: Direct MCP Connection
```python
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await asyncio.sleep(10.0)
        result = await session.list_tools()  # FAILS
```

**Result**: Same error - "before initialization was complete"

### Test 2: Manual Initialization  
Tried calling `session.initialize()` - this hangs indefinitely

### Test 3: Different Delays
Tested 0.5s, 3s, 5s, 7s, 10s delays - all produce same error

### Test 4: Retry Logic
Added retries with 2s delays between attempts - all attempts fail

## Observations from Claude Desktop

Claude Desktop logs show this working sequence:
```
2025-10-01T18:37:54.513Z - Server sends initialization result
2025-10-01T18:37:54.514Z - Client sends "notifications/initialized"
2025-10-01T18:37:54.514Z - Client calls "tools/list" - SUCCEEDS
```

The difference: Our `ClientSession.__aenter__()` should handle this handshake automatically, but it appears to not complete properly with itential-mcp.

## Server Timing Analysis

**itential-mcp load sequence:**
1. Start (0.0s)
2. Add base tools (0.0s - 0.2s) - ~60 tools
3. Create dynamic bindings (0.2s - 2.0s) - ~8 tools
4. Complete (2.0s) - Log: "Dynamic tool bindings is now complete"
5. ??? - Some additional internal initialization that isn't logged

Even waiting 10s after "complete", the server says "not initialized"

## Hypothesis

**Theory 1: Protocol Version Mismatch**
- MCP Python SDK 1.15.0 may use a different protocol than what itential-mcp expects
- Claude Desktop may use a different/older MCP SDK version

**Theory 2: Missing Initialization Step**  
- There may be an additional initialization message that needs to be sent
- The `ClientSession.__aenter__()` may not be sending the right initialization sequence

**Theory 3: itential-mcp Internal Bug**
- The server's "initialized" flag may not be set correctly after loading tools
- The server may have a race condition in its initialization code

## Comparison: Claude Desktop vs Our Agent

| Aspect | Claude Desktop | Our Agent |
|--------|---------------|-----------|
| MCP SDK | Unknown version | 1.15.0 |
| Language | TypeScript/Electron | Python |
| Connection | STDIO | STDIO |
| Tool Discovery | Succeeds immediately | Fails with "not initialized" |
| Session Creation | Works | Works |
| Handshake | Completes | Appears incomplete |

## Attempted Fixes

1. ✅ Proper async context managers
2. ✅ Increased timeouts (up to 10s)
3. ✅ Retry logic
4. ✅ Manual delays after session creation
5. ✅ Different ClientSession initialization patterns
6. ❌ None successful

## Recommendations

### Option 1: Contact Itential Support
Ask about:
- Recommended MCP Python client version
- Known compatibility issues with MCP SDK 1.15.0
- Proper initialization sequence
- Debug mode for MCP handshake

### Option 2: Use HTTP Transport
- Check if itential-mcp supports HTTP MCP transport
- HTTP may have better compatibility

### Option 3: Direct API Integration
- Bypass MCP entirely for itential
- Use Itential's REST API directly
- Create wrapper tools

### Option 4: Use Simpler MCP Servers
- Complete project with time and filesystem MCPs
- These are reference implementations and may work better

## Current Workaround

The agent works perfectly without tools or with compatible MCP servers. For now:

```bash
# Works - no tools
uv run python -m src.agent --agent-file test.prompt --mcp-config mcp_config_empty.json

# Once working MCP servers are available
uv run python -m src.agent --agent-file test.prompt
```

## Next Steps

1. Test with time and filesystem MCPs (simpler, reference implementations)
2. If those work, confirms itential-mcp specific issue
3. Contact Itential support for guidance
4. Consider HTTP transport if available

## Related Files

- `src/mcp_client.py` - MCP client implementation
- `mcp_config.json` - MCP configuration  
- `test_mcp_simple.py` - Basic MCP test
- `test_mcp_with_delay.py` - Test with delays
- `test_mcp_direct.py` - Direct MCP test

## Versions

- Python: 3.13.7
- MCP SDK: 1.15.0
- itential-mcp: 0.6.2.dev4+d941752
- LangGraph: 0.6.8
- Anthropic SDK: 0.69.0

---

**Last Updated**: 2025-10-01 15:20
**Status**: Issue documented, awaiting resolution strategy
