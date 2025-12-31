# Contributing to Autonomous Agent

This is an experimental project for learning about autonomous agents and MCP. Feel free to fork, experiment, and learn! This document provides guidelines for development workflow.

## Getting Started

1. **Fork and Clone**
   ```bash
   git clone https://github.com/AutomateIP/autonomousagent.git
   cd autonomous_agent
   ```

2. **Install Dependencies**
   ```bash
   uv sync
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   cp examples/mcp_config.json.example mcp_config.json
   # Edit .env and mcp_config.json with your settings
   ```

## Development Workflow

1. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

3. **Test Your Changes**
   ```bash
   uv run agent --agent-file tests/prompts/test_time.prompt
   ```

4. **Commit**
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Keep functions focused and small
- Add docstrings for public functions

## Testing

- Add tests for new features in `tests/`
- Ensure existing tests pass
- Test with multiple MCP servers when applicable

## Documentation

- Update README.md for user-facing changes
- Update docs/ for architecture or integration changes
- Include examples for new features

## Security

- Never commit API keys or credentials
- Use `.env` for secrets (already in `.gitignore`)
- Review the security section in README before contributing

## Experimentation

This project is designed for learning and experimentation. Some ideas to explore:
- Try different LLM models and compare reasoning
- Experiment with custom MCP servers
- Modify the system prompt to change agent behavior
- Add new configuration options
- Test with different types of tasks

## Questions?

Open an issue for questions or to share what you've learned!
