# Contributing to Autonomous Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

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
   cp mcp_config.json.example mcp_config.json
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

## Questions?

Open an issue for questions or discussion!
