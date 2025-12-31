"""LLM provider abstraction layer using LiteLLM."""

import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple

import litellm

logger = logging.getLogger(__name__)

# MCP tool name encoding/decoding helpers
_MCP_PREFIX = "mcp__"
_MCP_DELIMITER = "__"


def encode_tool_name(server: str, name: str) -> str:
    """
    Encode MCP server and tool name into a single function name.

    Args:
        server: MCP server name
        name: Tool name

    Returns:
        Encoded function name in format: mcp__server__name
    """
    # Escape existing delimiter occurrences to prevent parsing ambiguity
    safe_server = server.replace(_MCP_DELIMITER, "_")
    safe_name = name.replace(_MCP_DELIMITER, "_")
    return f"{_MCP_PREFIX}{safe_server}{_MCP_DELIMITER}{safe_name}"


def decode_tool_name(full_name: str) -> Tuple[str, str]:
    """
    Decode function name back to MCP server and tool name.

    Args:
        full_name: Encoded function name

    Returns:
        Tuple of (server, tool_name)
    """
    try:
        if not full_name.startswith(_MCP_PREFIX):
            # Fallback for non-prefixed names
            if "_" in full_name:
                parts = full_name.split("_", 1)
                return parts[0], parts[1]
            return "unknown", full_name

        # Remove prefix and split on delimiter
        without_prefix = full_name[len(_MCP_PREFIX):]
        parts = without_prefix.split(_MCP_DELIMITER, 1)

        if len(parts) == 2:
            return parts[0], parts[1]
        else:
            # Malformed, return as-is
            return "unknown", without_prefix
    except Exception as e:
        logger.warning(f"Failed to decode tool name '{full_name}': {e}")
        return "unknown", full_name


def sanitize_messages(messages: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Sanitize and validate message history.

    Args:
        messages: Raw message history

    Returns:
        Validated list of message dicts
    """
    if not messages:
        return []

    sanitized = []
    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            logger.warning(f"Message {i} is not a dict, skipping")
            continue

        if "role" not in msg:
            logger.warning(f"Message {i} missing 'role' key, skipping")
            continue

        if "content" not in msg and "tool_calls" not in msg:
            logger.warning(f"Message {i} missing 'content' and 'tool_calls', skipping")
            continue

        sanitized.append(msg)

    return sanitized


class LLMProvider:
    """Universal LLM provider using LiteLLM."""

    def __init__(self, model: str, api_key: Optional[str] = None):
        """
        Initialize LLM provider.

        Args:
            model: Model identifier (e.g., "claude-3-opus-20240229", "gpt-4", "gemini/gemini-pro")
            api_key: API key for authentication (optional, can use env vars)
        """
        self.model = model

        # LiteLLM uses environment variables for API keys by default
        # Only set env vars if api_key is provided AND the env var is not already set
        if api_key:
            self._set_provider_api_key(model, api_key)

    def _set_provider_api_key(self, model: str, api_key: str) -> None:
        """
        Set API key environment variable for the provider.
        Only sets if not already set to avoid overwriting existing configuration.

        Args:
            model: Model identifier
            api_key: API key to set
        """
        env_var = None

        # Determine provider from model name and set appropriate env var
        if model.startswith("claude") or model.startswith("anthropic"):
            env_var = "ANTHROPIC_API_KEY"
        elif model.startswith("gpt") or model.startswith("openai"):
            env_var = "OPENAI_API_KEY"
        elif model.startswith("gemini") or model.startswith("google"):
            # Try both common env var names for Gemini
            if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
                env_var = "GOOGLE_API_KEY"  # Prefer GOOGLE_API_KEY
            else:
                logger.debug("Gemini API key already set in environment")
                return
        elif model.startswith("bedrock"):
            # Bedrock uses AWS credentials, not a single API key
            logger.debug("Bedrock uses AWS credentials from environment")
            return
        elif model.startswith("ollama"):
            # Ollama typically doesn't need API key
            logger.debug("Ollama doesn't require API key")
            return

        # Set the env var only if it's not already set
        if env_var:
            if not os.getenv(env_var):
                os.environ[env_var] = api_key
                logger.debug(f"Set {env_var} environment variable for provider")
            else:
                logger.debug(f"{env_var} already set in environment, not overwriting")

    def format_messages(self, system_prompt: str, user_prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, str]]:
        """
        Format messages for the LLM.

        Note: system_prompt is handled separately in chat() method.
        This method constructs the message history + user prompt portion.

        Args:
            system_prompt: System prompt (unused here, kept for API compatibility)
            user_prompt: User prompt
            history: Conversation history

        Returns:
            Formatted messages list
        """
        messages = []

        # Add sanitized history
        if history:
            messages.extend(sanitize_messages(history))

        # Add user message
        messages.append({
            "role": "user",
            "content": user_prompt
        })

        return messages

    def _convert_tools_to_openai_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert MCP tool definitions to OpenAI function calling format.
        LiteLLM uses OpenAI's format as the standard and converts for other providers.

        Args:
            tools: List of MCP tool definitions

        Returns:
            List of OpenAI-formatted tools
        """
        openai_tools = []

        for tool in tools:
            try:
                # Defensive extraction with defaults
                server = tool.get("server", "unknown")
                name = tool.get("name", "unnamed")
                description = tool.get("description") or f"Tool {name} from {server} MCP server"
                input_schema = tool.get("input_schema") or {"type": "object", "properties": {}}

                # Encode tool name to avoid ambiguity
                encoded_name = encode_tool_name(server, name)

                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": encoded_name,
                        "description": description,
                        "parameters": input_schema
                    }
                }
                openai_tools.append(openai_tool)
            except Exception as e:
                tool_name = tool.get('name', 'unknown') if isinstance(tool, dict) else 'invalid'
                logger.warning(f"Failed to convert tool {tool_name}: {e}")
                continue

        return openai_tools

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: Optional[float] = None,
        max_retries: int = 0
    ) -> Dict[str, Any]:
        """
        Send chat request to LLM via LiteLLM.

        Args:
            messages: List of messages (OpenAI format)
            system_prompt: System prompt
            tools: Available MCP tools
            temperature: Temperature for response generation
            max_tokens: Maximum tokens for response
            timeout: Optional timeout in seconds for the request
            max_retries: Number of retries for transient errors (default: 0)

        Returns:
            Dict containing response and any tool calls with stable schema:
            {
                "id": str,
                "model": str,
                "stop_reason": str|None,
                "content": [{"type":"text","text":...}],
                "tool_calls": [{"id":..., "name":..., "server":..., "arguments":...}],
                "usage": {"input_tokens": int, "output_tokens": int}
            }
        """
        # Sanitize input messages
        sanitized_messages = sanitize_messages(messages)

        # Build request with system prompt first, then messages
        full_messages = [{"role": "system", "content": system_prompt}] + sanitized_messages

        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Sending request to {self.model} via LiteLLM (attempt {attempt + 1}/{max_retries + 1})")

                # Prepare request parameters
                request_params = {
                    "model": self.model,
                    "messages": full_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                # Add timeout if provided (LiteLLM supports request_timeout)
                if timeout is not None:
                    request_params["request_timeout"] = timeout

                # Add tools if provided
                if tools:
                    openai_tools = self._convert_tools_to_openai_format(tools)
                    if openai_tools:  # Only add if conversion succeeded
                        request_params["tools"] = openai_tools
                        request_params["tool_choice"] = "auto"
                        logger.debug(f"Including {len(openai_tools)} tools in request")

                # Make API call via LiteLLM
                response = litellm.completion(**request_params)

                # Parse response with defensive guards
                return self._parse_response(response)

            except Exception as e:
                error_msg = str(e)
                is_retryable = (
                    "timeout" in error_msg.lower() or
                    "5" in error_msg[:3] or  # 5xx errors
                    "rate" in error_msg.lower()
                )

                if attempt < max_retries and is_retryable:
                    backoff = 0.2 * (attempt + 1)
                    logger.warning(f"Retryable error on attempt {attempt + 1}: {e}. Retrying in {backoff}s...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"Error calling LLM via LiteLLM: {e}")
                    raise

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse LiteLLM response into stable output schema.

        Args:
            response: LiteLLM response object

        Returns:
            Normalized response dict
        """
        try:
            # Guard: ensure choices exist
            if not hasattr(response, "choices") or not response.choices:
                raise ValueError("Response missing choices")

            choice = response.choices[0]

            # Guard: ensure message exists
            if not hasattr(choice, "message"):
                raise ValueError("Response choice missing message")

            message = choice.message

            # Build stable response structure
            result = {
                "id": getattr(response, "id", "unknown"),
                "model": getattr(response, "model", self.model),
                "stop_reason": getattr(choice, "finish_reason", None),
                "content": [],
                "tool_calls": [],
                "usage": self._extract_usage(response)
            }

            # Extract content
            if hasattr(message, "content") and message.content:
                result["content"].append({
                    "type": "text",
                    "text": message.content
                })

            # Extract tool calls with defensive parsing
            if hasattr(message, "tool_calls") and message.tool_calls:
                for tool_call in message.tool_calls:
                    try:
                        parsed_tool = self._parse_tool_call(tool_call)
                        if parsed_tool:
                            result["tool_calls"].append(parsed_tool)
                    except Exception as e:
                        logger.warning(f"Failed to parse tool call: {e}")
                        continue

            logger.debug(f"Received response: {result['stop_reason']}, {len(result['tool_calls'])} tool calls")
            return result

        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            raise

    def _extract_usage(self, response: Any) -> Dict[str, int]:
        """
        Extract token usage from response, with safe defaults.

        Args:
            response: LiteLLM response object

        Returns:
            Dict with input_tokens and output_tokens
        """
        try:
            if hasattr(response, "usage") and response.usage:
                return {
                    "input_tokens": getattr(response.usage, "prompt_tokens", 0),
                    "output_tokens": getattr(response.usage, "completion_tokens", 0)
                }
        except Exception as e:
            logger.debug(f"Could not extract usage: {e}")

        # Default to zero if unavailable
        return {"input_tokens": 0, "output_tokens": 0}

    def _parse_tool_call(self, tool_call: Any) -> Optional[Dict[str, Any]]:
        """
        Parse a single tool call from LiteLLM response.

        Args:
            tool_call: Tool call object from response

        Returns:
            Parsed tool call dict or None if parsing fails
        """
        try:
            if not hasattr(tool_call, "function"):
                return None

            function = tool_call.function
            full_name = getattr(function, "name", "unknown")

            # Decode server and tool name
            server, tool_name = decode_tool_name(full_name)

            # Parse arguments - defensive JSON parsing
            arguments_str = getattr(function, "arguments", "{}")
            try:
                if isinstance(arguments_str, str):
                    arguments = json.loads(arguments_str)
                else:
                    # Already parsed
                    arguments = arguments_str
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse tool arguments as JSON: {e}")
                # Store raw string for debugging
                arguments = {"_raw": arguments_str, "_parse_error": str(e)}

            return {
                "id": getattr(tool_call, "id", "unknown"),
                "name": tool_name,
                "server": server,
                "arguments": arguments
            }

        except Exception as e:
            logger.warning(f"Error parsing tool call: {e}")
            return None


def create_llm_provider(provider: str, model: str, api_key: Optional[str] = None) -> LLMProvider:
    """
    Factory function to create LLM provider.

    Args:
        provider: Provider name (used for model prefix if needed)
        model: Model identifier
        api_key: API key

    Returns:
        LLMProvider instance
    """
    # LiteLLM model format examples:
    # - Anthropic: "claude-3-opus-20240229" or "anthropic/claude-3-opus-20240229"
    # - OpenAI: "gpt-4" or "openai/gpt-4"
    # - Gemini: "gemini/gemini-pro"
    # - Bedrock: "bedrock/anthropic.claude-v2"
    # - Ollama: "ollama/llama2"

    # If provider is specified and model doesn't have provider prefix, add it
    if provider and "/" not in model:
        # Special cases where we don't need prefix
        if provider == "anthropic" and model.startswith("claude"):
            pass  # Anthropic models work without prefix
        elif provider == "openai" and model.startswith("gpt"):
            pass  # OpenAI models work without prefix
        else:
            model = f"{provider}/{model}"

    return LLMProvider(model, api_key)
