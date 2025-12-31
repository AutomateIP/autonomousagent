# Troubleshooting Guide

Common issues and solutions for the Autonomous Agent Framework.

## Connection Issues

### MCP Server Won't Connect

**Symptom**: "Failed to connect to [server]"

**Solutions**:
1. Check paths in `mcp_config.json` are absolute paths
2. Verify server executable exists at specified path
3. Test server independently: `cd mcps/[server] && uv run [server-cmd]`
4. Check server timeout is sufficient (itential-mcp needs 120s)

### Node.js Not Found

**Symptom**: `[Errno 2] No such file or directory: 'node'`

**Solution**: Use full path to node in `mcp_config.json`:
```json
"command": "/Users/[user]/.nvm/versions/node/v24.7.0/bin/node"
```

Find your node path: `which node` or `ls ~/.nvm/versions/node/*/bin/node`

### HTTP Transport Not Supported

**Symptom**: "HTTP transport not yet implemented"

**Cause**: Browser MCP and similar servers use HTTP, not STDIO

**Solution**: 
- Disable in `mcp_config.json`: `"disabled": true`
- Or implement HTTP transport in `src/mcp_client.py`

## Execution Issues

### Recursion Limit Reached

**Symptom**: `GraphRecursionError: Recursion limit of 25 reached`

**Cause**: Complex task with many tool calls

**Solutions**:
1. Already fixed: `recursion_limit=50` in `agent_core.py`
2. If still hitting limit, increase to 100:
   ```python
   workflow.compile(recursion_limit=100)
   ```
3. Or simplify task into smaller subtasks

### Max Tokens Exceeded

**Symptom**: `LLM stop reason: max_tokens` + incomplete tool arguments

**Cause**: Generating large content (HTML files, long reports)

**Solutions**:
1. Increase in `agent.conf`: `max_tokens = 16384` (or 32768)
2. Or override per-run: `--max-tokens 32768`
3. Current setting: 16384 (sufficient for most tasks)

### Write File Fails - Missing Content

**Symptom**: `Invalid arguments for write_file: content Required`

**Cause**: LLM hit max_tokens before completing tool arguments

**Fix**: Increase max_tokens (see above)

## Tool Issues

### No Tools Discovered

**Symptom**: "Connected to X servers" but "0 tools"

**Check**:
1. Server isn't disabled: `"disabled": false`
2. Server loaded successfully (check logs for "complete")
3. Timeout sufficient for server initialization
4. Server path correct in config

### Tool Call Fails

**Symptom**: Tool execution error

**Debug**:
1. Run with `--debug` to see full error
2. Check tool arguments match schema
3. Verify tool name is correct (use `--list-tools`)
4. Check server logs for details

## Configuration Issues

### API Key Not Found

**Symptom**: "ANTHROPIC_API_KEY not set"

**Solutions**:
1. Create `.env` from template: `cp .env.example .env`
2. Add key: `ANTHROPIC_API_KEY=sk-ant-api03-...`
3. Verify no extra spaces or quotes
4. Ensure `.env` is in project root

### Config File Not Found

**Symptom**: "Config file not found"

**Solutions**:
1. Check file exists: `ls -l agent.conf`
2. Use full path: `--config /full/path/to/agent.conf`
3. Create from template: `cp agent.conf.example agent.conf`

## Performance Issues

### Agent Takes Too Long

**Normal Timing**:
- Simple tasks: 5-15 seconds
- With tools: 20-60 seconds
- Complex workflows: 1-3 minutes

**If Unusually Slow**:
1. Check MCP server initialization (itential-mcp takes ~2s)
2. Reduce max_tokens for faster responses
3. Use faster model: `claude-3-haiku-20240307`
4. Check network latency to Itential Platform

### Too Many Iterations

**Symptom**: Agent loops without completing

**Solutions**:
1. Check max_iterations in `agent.conf` (default 10)
2. Simplify task prompt
3. Enable `--debug` to see reasoning loop
4. May hit recursion_limit before max_iterations

## Model Issues

### Model Not Found

**Symptom**: Invalid model string error

**Check**:
1. Model name correct in `agent.conf`
2. Supported models:
   - Anthropic: `claude-sonnet-4-5-20250929`, `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`
   - OpenAI: `gpt-4`, `gpt-4-turbo`, `gpt-3.5-turbo`

### Rate Limit Errors

**Symptom**: API rate limit exceeded

**Solutions**:
1. Wait and retry
2. Use slower model (Haiku is cheaper)
3. Check API quota/billing
4. Add delay between runs if automating

## Diagnostic Commands

### Check MCP Status
```bash
uv run python -m src.agent --agent-file any.prompt --show-mcps
```

### List All Tools
```bash
uv run python -m src.agent --agent-file any.prompt --list-tools
```

### Debug Mode
```bash
uv run python -m src.agent --agent-file task.prompt --debug
```

### Test Without Tools
```bash
uv run python -m src.agent --agent-file tests/prompts/test_no_tools.prompt --mcp-config mcp_config_empty.json
```

## Error Messages

### "Client failed to connect"
- Check command path is absolute
- Verify server can run independently
- Check server doesn't require additional setup

### "Invalid request parameters"
- MCP server not fully initialized
- Wait for "complete" message in logs
- Check server logs for errors

### "Connection closed"
- Server crashed during startup
- Check server dependencies installed
- Review server error output

## Getting Help

1. Run with `--debug` flag
2. Check `logs/` directory (if configured)
3. Review `session_summary/` for implementation notes
4. See `docs/ARCHITECTURE.md` for system design
5. Check `docs/ITENTIAL_INTEGRATION.md` for platform-specific issues

## Known Limitations

- STDIO transport only (HTTP coming)
- No conversation persistence
- Max 15 iterations (configurable)
- Filesystem MCP limited to files/ directory
- Upstream UV deprecation warnings (from dependencies)
