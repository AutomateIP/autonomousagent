"""Configuration management for the autonomous agent."""

import argparse
import configparser
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the agent."""
    
    def __init__(self):
        """Initialize configuration from environment, config file, and CLI arguments."""
        load_dotenv()
        self.args = self._parse_cli_args()
        self.conf = self._load_config_file()
        self._validate_config()
    
    def _parse_cli_args(self) -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(
            description="Autonomous Agent with MCP Support"
        )
        parser.add_argument(
            "--config",
            type=str,
            default="./agent.conf",
            help="Path to agent configuration file"
        )
        parser.add_argument(
            "--agent-file",
            type=str,
            required=True,
            help="Path to agent task prompt file"
        )
        parser.add_argument(
            "--mcp-config",
            type=str,
            help="Path to MCP configuration file (overrides config file)"
        )
        parser.add_argument(
            "--system-prompt",
            type=str,
            help="Path to system prompt file (overrides config file)"
        )
        parser.add_argument(
            "--llm-provider",
            type=str,
            help="LLM provider (anthropic, openai) (overrides config file)"
        )
        parser.add_argument(
            "--llm-model",
            type=str,
            help="LLM model string (overrides config file)"
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging (overrides config file)"
        )
        parser.add_argument(
            "--show-mcps",
            action="store_true",
            help="Show connected MCP servers and exit"
        )
        parser.add_argument(
            "--list-tools",
            action="store_true",
            help="List all available tools from all MCPs and exit"
        )
        return parser.parse_args()
    
    def _load_config_file(self) -> configparser.ConfigParser:
        """Load configuration from config file."""
        config = configparser.ConfigParser()
        
        if Path(self.args.config).exists():
            logger.info(f"Loading configuration from {self.args.config}")
            config.read(self.args.config)
        else:
            logger.warning(f"Config file {self.args.config} not found, using defaults")
        
        return config
    
    def _get_config_value(self, cli_arg: Optional[str], config_section: str, config_key: str, env_var: str, default: str) -> str:
        """Get configuration value with precedence: CLI > Config File > Env Var > Default."""
        # CLI argument has highest priority
        if cli_arg is not None:
            return cli_arg
        
        # Config file second
        if self.conf.has_option(config_section, config_key):
            return self.conf.get(config_section, config_key)
        
        # Environment variable third
        env_value = os.getenv(env_var)
        if env_value:
            return env_value
        
        # Default last
        return default
    
    def _validate_config(self) -> None:
        """Validate configuration settings."""
        # Check agent file exists
        if not Path(self.args.agent_file).exists():
            raise FileNotFoundError(f"Agent file not found: {self.args.agent_file}")
        
        # Check system prompt exists
        system_prompt_path = self._get_config_value(
            self.args.system_prompt,
            "agent", "system_prompt",
            "AGENT_SYSTEM_PROMPT",
            "./prompts/agent_system.prompt"
        )
        if not Path(system_prompt_path).exists():
            raise FileNotFoundError(f"System prompt not found: {system_prompt_path}")
        
        # Check MCP config exists
        mcp_config_path = self._get_config_value(
            self.args.mcp_config,
            "mcp", "config_file",
            "MCP_CONFIG",
            "./mcp_config.json"
        )
        if not Path(mcp_config_path).exists():
            raise FileNotFoundError(f"MCP config not found: {mcp_config_path}")
        
        # Check API keys
        provider = self._get_config_value(
            self.args.llm_provider,
            "llm", "provider",
            "LLM_PROVIDER",
            "anthropic"
        )
        
        if provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
        elif provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY not set in environment")
    
    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP server configuration from JSON file."""
        mcp_config_path = self._get_config_value(
            self.args.mcp_config,
            "mcp", "config_file",
            "MCP_CONFIG",
            "./mcp_config.json"
        )
        
        logger.info(f"Loading MCP config from {mcp_config_path}")
        with open(mcp_config_path, 'r') as f:
            config = json.load(f)
        
        if "mcpServers" not in config:
            raise ValueError("Invalid MCP config: missing 'mcpServers' key")
        
        return config["mcpServers"]
    
    def load_prompt_file(self, path: str) -> str:
        """Load prompt content from file."""
        logger.info(f"Loading prompt from {path}")
        with open(path, 'r') as f:
            return f.read().strip()
    
    def load_system_prompt(self) -> str:
        """Load system prompt."""
        system_prompt_path = self._get_config_value(
            self.args.system_prompt,
            "agent", "system_prompt",
            "AGENT_SYSTEM_PROMPT",
            "./prompts/agent_system.prompt"
        )
        return self.load_prompt_file(system_prompt_path)
    
    def load_agent_prompt(self) -> str:
        """Load agent task prompt."""
        return self.load_prompt_file(self.args.agent_file)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        provider = self._get_config_value(
            self.args.llm_provider,
            "llm", "provider",
            "LLM_PROVIDER",
            "anthropic"
        )
        
        model = self._get_config_value(
            self.args.llm_model,
            "llm", "model",
            "LLM_MODEL",
            "claude-sonnet-4-20250514"
        )
        
        temperature = float(self.conf.get("llm", "temperature", fallback="0.7"))
        max_tokens = int(self.conf.get("llm", "max_tokens", fallback="4096"))
        
        return {
            "provider": provider,
            "model": model,
            "api_key": self._get_api_key(provider),
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key for configured provider."""
        if provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY", "")
        elif provider == "openai":
            return os.getenv("OPENAI_API_KEY", "")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def get_max_iterations(self) -> int:
        """Get maximum iterations from config."""
        return int(self.conf.get("agent", "max_iterations", fallback="10"))
    
    def setup_logging(self) -> None:
        """Configure logging based on settings."""
        if self.args.debug:
            level = logging.DEBUG
        else:
            log_level_str = self.conf.get("agent", "log_level", fallback="INFO")
            level = getattr(logging, log_level_str.upper(), logging.INFO)
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
