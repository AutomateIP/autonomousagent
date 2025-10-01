# Itential Platform Integration Guide

This guide covers integration with Itential Platform via the itential-mcp server.

## Overview

The itential-mcp server provides 21 tools (subset based on configuration) for interacting with Itential Platform, including workflow management, device operations, health monitoring, and lifecycle management.

## Setup

### 1. Configure Itential Credentials

```bash
cp itential-mcp.conf.example itential-mcp.conf
```

Edit `itential-mcp.conf`:
```ini
[platform]
host = your-platform.itential.com
port = 443
client_id = your-client-id
client_secret = your-client-secret
disable_verify = False
timeout = 60
log_level = DEBUG
```

### 2. Update MCP Configuration

Edit `mcp_config.json` and set absolute paths:

```json
{
  "mcpServers": {
    "itential-mcp": {
      "disabled": false,
      "timeout": 120,
      "command": "uv",
      "args": [
        "--directory", "/full/absolute/path/to/mcps/itential-mcp",
        "run", "itential-mcp", "run",
        "--config", "/full/absolute/path/to/itential-mcp.conf"
      ],
      "type": "stdio"
    }
  }
}
```

### 3. Test Connection

```bash
# Test itential-mcp server independently
cd mcps/itential-mcp
uv run itential-mcp run --config ../../itential-mcp.conf

# Should see: "Dynamic tool bindings is now complete" after ~2 seconds
```

## Available Tools

### Platform Health
- `get_health` - Comprehensive platform health metrics
  - System resources (CPU, memory, uptime)
  - Core services (MongoDB, Redis, RabbitMQ)
  - Applications status (18 apps)
  - Adapters status (27 adapters)

### Workflow Management
- `get_workflows` - List all available workflows
- `start_workflow` - Execute a workflow
- `get_jobs` - Monitor job status
- `describe_job` - Get detailed job information

### Device Management
- `get_devices` - Retrieve all devices
- `get_device_groups` - List device groups
- `add_devices_to_group` - Group management
- `remove_devices_from_group` - Remove from groups

### Lifecycle Manager
- `get_resources` - List LCM resources
- `describe_resource` - Resource details
- `get_instances` - List resource instances
- `describe_instance` - Instance details
- `run_action` - Execute resource actions

### Configuration Management
- `get_device_configuration` - Device configs
- `backup_device_configuration` - Backup configs
- `apply_device_configuration` - Apply configs

### And More
- Applications management (restart, start, stop)
- Adapters management
- Templates and command execution
- Gateway management
- Projects and integrations

## Example Usage

### Example 1: Platform Health Check

**Prompt** (`check_health.prompt`):
```
Use the get_health tool to check the Itential platform status. 
Provide a summary of key metrics including:
- Overall health status
- Number of applications and adapters  
- System resource utilization
- Any issues or warnings
```

**Command**:
```bash
uv run python -m src.agent --agent-file check_health.prompt
```

**Sample Output**:
```
Overall System Status: HEALTHY ✅

Core Services:
- Redis: Running
- MongoDB: Running
- Applications: 18 running
- Adapters: 27 online

System Resources:
- Memory: 15.36 GB total, 5.34 GB free (65% used)
- CPU Load: [0.0, 0.02, 0.08] - Very low
- Uptime: 92.2 days

Platform Details:
- Version: 6.0.8
- Node.js: 20.19.2
- Uptime: 14.0 days

All services operating normally.
```

### Example 2: Device Inventory

**Prompt** (`get_devices.prompt`):
```
Collect all devices from Itential and create an ASCII table showing:
- Device name
- IP address
- OS type
- Device type

Group by device category if possible.
```

**Command**:
```bash
uv run python -m src.agent --agent-file get_devices.prompt
```

**Sample Output**:
```
Retrieved 39 devices:

Network Devices (19):
┌──────────────────┬─────────────┬───────────┬─────────────┐
│ Name             │ IP          │ OS        │ Type        │
├──────────────────┼─────────────┼───────────┼─────────────┤
│ IOS-CSR-AWS-1   │ 10.1.8.97   │ cisco-ios │ network_cli │
│ EOS-AWS-1       │ 10.1.6.81   │ arista    │ network_cli │
...

AWS VPCs (18):
...

Compute Devices (2):
...
```

### Example 3: Workflow Execution

**Prompt** (`run_workflow.prompt`):
```
List all available workflows in Itential. Then start the workflow 
named "Network_Device_Backup" if it exists, and monitor its status.
```

**Command**:
```bash
uv run python -m src.agent --agent-file run_workflow.prompt
```

The agent will autonomously:
1. Call `get_workflows` to list workflows
2. Find the target workflow
3. Call `start_workflow` to execute it
4. Call `get_jobs` or `describe_job` to monitor status
5. Report results

## Advanced Usage

### Multi-Step Automation

**Prompt** (`audit_task.prompt`):
```
Perform a platform audit:
1. Check overall platform health
2. Get list of all devices
3. Identify any devices that might need attention
4. Create a summary report with recommendations
```

The agent will autonomously:
- Decide which tools to use
- Make multiple tool calls
- Synthesize information
- Generate comprehensive report

### Conditional Logic

**Prompt** (`conditional_workflow.prompt`):
```
Check the platform health. If all services are healthy, 
retrieve the device list. If any issues are found, 
provide detailed diagnostics instead.
```

The agent's LLM-driven nature allows it to make conditional decisions based on tool results!

## Configuration Tips

### Performance Tuning

For Itential-specific tasks, configure `agent.conf`:

```ini
[llm]
# For device queries (predictable output)
model = claude-3-haiku-20240307
temperature = 0.3

# For workflow automation (need reasoning)
model = claude-sonnet-4-20250514
temperature = 0.7
```

### Timeout Settings

Itential tools can take time. In `mcp_config.json`:

```json
{
  "mcpServers": {
    "itential-mcp": {
      "timeout": 120  // 2 minutes for heavy operations
    }
  }
}
```

## Troubleshooting

### Connection Issues

**Symptom**: "Failed to connect to itential-mcp"

**Check**:
1. Verify `itential-mcp.conf` has correct credentials
2. Test platform connectivity: `curl https://your-platform.itential.com`
3. Check MCP server runs: `cd mcps/itential-mcp && uv run itential-mcp run --config ../../itential-mcp.conf`

### Authentication Errors

**Symptom**: "Authentication failed" in logs

**Solutions**:
- Verify `client_id` and `client_secret` in `itential-mcp.conf`
- Check user has required permissions
- Ensure platform host is correct (include https://)

### Tool Discovery Issues

**Symptom**: "Connected but 0 tools discovered"

**Solutions**:
- Check itential-mcp logs for errors
- Verify tool loading completed: Look for "Dynamic tool bindings is now complete"
- Increase timeout if server is slow
- Check network connectivity to platform

## Best Practices

### Prompt Design for Itential

**Good Prompts:**
- "Check platform health and report any issues"
- "Get all Cisco devices and show their IP addresses"
- "List workflows related to backups"
- "Execute the daily_config_backup workflow"

**Avoid:**
- Overly specific API calls (let agent decide)
- Manual step-by-step instructions (agent knows the tools)
- Assume tool names (agent will discover and use correct ones)

### Error Handling

The agent automatically handles errors gracefully:
- Retries on temporary failures
- Provides clear error messages
- Continues execution when possible

### Resource Management

- Platform queries can be resource-intensive
- Use appropriate models (Haiku for simple, Sonnet for complex)
- Monitor agent iterations (max 10 by default)

## Example Workflows

### Daily Health Check

```bash
echo "Perform daily health check: platform status, adapter connectivity, recent job failures" > daily_check.prompt
uv run python -m src.agent --agent-file daily_check.prompt
```

### Device Compliance Check

```bash
echo "Get all network devices and check if they have recent backups. Report any devices without backups in the last 24 hours." > compliance.prompt
uv run python -m src.agent --agent-file compliance.prompt
```

### Workflow Monitoring

```bash
echo "Show status of all running jobs. For any failed jobs, provide error details and recommendations." > monitor_jobs.prompt
uv run python -m src.agent --agent-file monitor_jobs.prompt
```

## Tool Reference

For complete list of available tools and their capabilities, see itential-mcp documentation:
- [itential-mcp GitHub](https://github.com/itential/itential-mcp)
- [itential-mcp Tools Reference](https://github.com/itential/itential-mcp/blob/devel/docs/tools.md)

## Support

For Itential Platform-specific issues:
- Check platform logs
- Verify user permissions
- Review itential-mcp documentation
- Contact Itential support if needed

---

**Next**: Return to [README.md](../README.md) for general agent documentation
