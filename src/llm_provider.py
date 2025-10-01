"""LLM provider abstraction layer."""

import logging
from typing import Dict, List, Any, Optional
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMProvider:
    """Base class for LLM providers."""
    
    def __init__(self, model: str, api_key: str):
        """
        Initialize LLM provider.
        
        Args:
            model: Model identifier
            api_key: API key for authentication
        """
        self.model = model
        self.api_key = api_key
    
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
    
    def chat(self, messages: List[Dict[str, str]], system_prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send chat request to LLM.
        
        Args:
            messages: List of messages
            system_prompt: System prompt
            tools: Available tools
            
        Returns:
            LLM response
        """
        raise NotImplementedError("Subclass must implement chat method")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(self, model: str, api_key: str):
        """
        Initialize Anthropic provider.
        
        Args:
            model: Claude model identifier
            api_key: Anthropic API key
        """
        super().__init__(model, api_key)
        self.client = Anthropic(api_key=api_key)
    
    def _convert_tools_to_anthropic_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert MCP tool definitions to Anthropic tool format.
        
        Args:
            tools: List of MCP tool definitions
            
        Returns:
            List of Anthropic-formatted tools
        """
        anthropic_tools = []
        
        for tool in tools:
            anthropic_tool = {
                "name": f"{tool['server']}_{tool['name']}",
                "description": tool['description'] or f"Tool {tool['name']} from {tool['server']} MCP server",
                "input_schema": tool['input_schema']
            }
            anthropic_tools.append(anthropic_tool)
        
        return anthropic_tools
    
    def chat(self, messages: List[Dict[str, str]], system_prompt: str, tools: List[Dict[str, Any]] = None, temperature: float = 0.7, max_tokens: int = 4096) -> Dict[str, Any]:
        """
        Send chat request to Claude.
        
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
            logger.debug(f"Sending request to Claude {self.model}")
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": messages
            }
            
            # Add tools if provided
            if tools:
                anthropic_tools = self._convert_tools_to_anthropic_format(tools)
                request_params["tools"] = anthropic_tools
                logger.debug(f"Including {len(anthropic_tools)} tools in request")
            
            # Make API call
            response = self.client.messages.create(**request_params)
            
            logger.debug(f"Received response from Claude: {response.stop_reason}")
            
            # Parse response
            result = {
                "id": response.id,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "content": [],
                "tool_calls": [],
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
            # Extract content and tool calls
            for block in response.content:
                if block.type == "text":
                    result["content"].append({
                        "type": "text",
                        "text": block.text
                    })
                elif block.type == "tool_use":
                    # Parse server and tool name
                    full_name = block.name
                    if "_" in full_name:
                        server, tool_name = full_name.split("_", 1)
                    else:
                        server = "unknown"
                        tool_name = full_name
                    
                    result["tool_calls"].append({
                        "id": block.id,
                        "name": tool_name,
                        "server": server,
                        "arguments": block.input
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise


def create_llm_provider(provider: str, model: str, api_key: str) -> LLMProvider:
    """
    Factory function to create appropriate LLM provider.
    
    Args:
        provider: Provider name (anthropic, openai)
        model: Model identifier
        api_key: API key
        
    Returns:
        LLMProvider instance
    """
    if provider == "anthropic":
        return AnthropicProvider(model, api_key)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
