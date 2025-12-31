"""LLM provider abstraction layer using LiteLLM."""

import logging
import os
from typing import Dict, List, Any, Optional
from litellm import completion

logger = logging.getLogger(__name__)


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
        # We'll set them if provided
        if api_key:
            # Determine provider from model name and set appropriate env var
            if model.startswith("claude") or model.startswith("anthropic"):
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif model.startswith("gpt") or model.startswith("openai"):
                os.environ["OPENAI_API_KEY"] = api_key
            elif model.startswith("gemini") or model.startswith("google"):
                os.environ["GEMINI_API_KEY"] = api_key
            elif model.startswith("bedrock"):
                # Bedrock uses AWS credentials
                pass
            elif model.startswith("ollama"):
                # Ollama typically doesn't need API key
                pass

    def format_messages(self, system_prompt: str, user_prompt: str, history: List[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """
        Format messages for the LLM.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            history: Conversation history

        Returns:
            Formatted messages
        """
        messages = []

        if history:
            messages.extend(history)

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
            openai_tool = {
                "type": "function",
                "function": {
                    "name": f"{tool['server']}_{tool['name']}",
                    "description": tool['description'] or f"Tool {tool['name']} from {tool['server']} MCP server",
                    "parameters": tool['input_schema']
                }
            }
            openai_tools.append(openai_tool)

        return openai_tools

    def chat(self, messages: List[Dict[str, str]], system_prompt: str, tools: List[Dict[str, Any]] = None, temperature: float = 0.7, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        Send chat request to LLM via LiteLLM.

        Args:
            messages: List of messages
            system_prompt: System prompt
            tools: Available MCP tools
            temperature: Temperature for response generation
            max_tokens: Maximum tokens for response

        Returns:
            Dict containing response and any tool calls
        """
        try:
            logger.debug(f"Sending request to {self.model} via LiteLLM")

            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": [{"role": "system", "content": system_prompt}] + messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            # Add tools if provided
            if tools:
                openai_tools = self._convert_tools_to_openai_format(tools)
                request_params["tools"] = openai_tools
                request_params["tool_choice"] = "auto"
                logger.debug(f"Including {len(openai_tools)} tools in request")

            # Make API call via LiteLLM
            response = completion(**request_params)

            logger.debug(f"Received response: {response.choices[0].finish_reason}")

            # Parse response
            choice = response.choices[0]
            message = choice.message

            result = {
                "id": response.id,
                "model": response.model,
                "stop_reason": choice.finish_reason,
                "content": [],
                "tool_calls": [],
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
            }

            # Extract content
            if message.content:
                result["content"].append({
                    "type": "text",
                    "text": message.content
                })

            # Extract tool calls
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    # Parse server and tool name
                    full_name = tool_call.function.name
                    if "_" in full_name:
                        server, tool_name = full_name.split("_", 1)
                    else:
                        server = "unknown"
                        tool_name = full_name

                    # Parse arguments (they come as JSON string)
                    import json
                    arguments = json.loads(tool_call.function.arguments)

                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_name,
                        "server": server,
                        "arguments": arguments
                    })

            return result

        except Exception as e:
            logger.error(f"Error calling LLM via LiteLLM: {e}")
            raise


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
