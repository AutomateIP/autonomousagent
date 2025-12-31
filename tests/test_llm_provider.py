"""Unit tests for LLM provider layer."""

import json
import pytest
from unittest.mock import Mock, patch
from src.llm_provider import (
    LLMProvider,
    create_llm_provider,
    encode_tool_name,
    decode_tool_name,
    sanitize_messages
)


class TestToolNameEncoding:
    """Test tool name encoding/decoding roundtrip."""

    def test_encode_decode_roundtrip_simple(self):
        """Test basic roundtrip encoding."""
        server = "filesystem"
        name = "write_file"
        encoded = encode_tool_name(server, name)
        decoded_server, decoded_name = decode_tool_name(encoded)
        assert decoded_server == server
        assert decoded_name == name

    def test_encode_decode_with_delimiter_in_names(self):
        """Test encoding when server/name contain the delimiter."""
        server = "my__server"
        name = "my__tool"
        encoded = encode_tool_name(server, name)
        # Should escape delimiters
        assert "__" in encoded
        decoded_server, decoded_name = decode_tool_name(encoded)
        # Should recover escaped versions
        assert "_" in decoded_server
        assert "_" in decoded_name

    def test_decode_legacy_format(self):
        """Test decoding of legacy server_tool format."""
        legacy_name = "filesystem_write_file"
        server, name = decode_tool_name(legacy_name)
        # Should split on first underscore
        assert server == "filesystem"
        assert name == "write_file"

    def test_decode_malformed_returns_unknown(self):
        """Test decoding malformed names returns unknown server."""
        malformed = "mcp__nodelimiter"
        server, name = decode_tool_name(malformed)
        assert server == "unknown"
        assert name == "nodelimiter"


class TestMessageSanitization:
    """Test message sanitization and validation."""

    def test_sanitize_valid_messages(self):
        """Test sanitizing valid messages."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        result = sanitize_messages(messages)
        assert len(result) == 2
        assert result == messages

    def test_sanitize_removes_invalid_messages(self):
        """Test sanitization removes messages without required keys."""
        messages = [
            {"role": "user", "content": "Valid"},
            {"content": "No role"},  # Missing role
            {"role": "assistant"},  # Missing content and tool_calls
            "not a dict",  # Not a dict
            {"role": "user", "content": "Also valid"}
        ]
        result = sanitize_messages(messages)
        assert len(result) == 2
        assert result[0]["content"] == "Valid"
        assert result[1]["content"] == "Also valid"

    def test_sanitize_allows_tool_calls_without_content(self):
        """Test messages with tool_calls but no content are valid."""
        messages = [
            {"role": "assistant", "tool_calls": [{"id": "1", "name": "test"}]}
        ]
        result = sanitize_messages(messages)
        assert len(result) == 1

    def test_sanitize_empty_or_none(self):
        """Test sanitizing None or empty list."""
        assert sanitize_messages(None) == []
        assert sanitize_messages([]) == []


class TestToolConversion:
    """Test MCP tool to OpenAI format conversion."""

    def test_convert_tools_with_complete_tool(self):
        """Test converting a complete tool definition."""
        provider = LLMProvider("gpt-4")
        tools = [{
            "server": "filesystem",
            "name": "write_file",
            "description": "Write content to a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }]

        result = provider._convert_tools_to_openai_format(tools)
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert "mcp__" in result[0]["function"]["name"]
        assert result[0]["function"]["description"] == "Write content to a file"
        assert result[0]["function"]["parameters"]["type"] == "object"

    def test_convert_tools_missing_fields_does_not_crash(self):
        """Test tool conversion with missing fields uses defaults."""
        provider = LLMProvider("gpt-4")
        tools = [
            {"name": "partial_tool"},  # Missing server, description, input_schema
            {},  # Completely empty
        ]

        result = provider._convert_tools_to_openai_format(tools)
        assert len(result) == 2
        # Should use defaults
        assert result[0]["function"]["name"] == "mcp__unknown__partial_tool"
        assert "unknown" in result[0]["function"]["description"].lower()
        assert result[0]["function"]["parameters"]["type"] == "object"

    def test_convert_tools_handles_exceptions(self):
        """Test tool conversion continues after exceptions."""
        provider = LLMProvider("gpt-4")
        tools = [
            {"server": "good", "name": "tool1", "description": "Valid"},
            None,  # This will cause exception
            {"server": "good", "name": "tool2", "description": "Also valid"}
        ]

        with patch('src.llm_provider.logger'):
            result = provider._convert_tools_to_openai_format(tools)
            # Should skip the None but process others
            assert len(result) == 2


class TestToolCallParsing:
    """Test tool call argument parsing."""

    def test_parse_tool_call_valid_json(self):
        """Test parsing tool call with valid JSON arguments."""
        provider = LLMProvider("gpt-4")

        mock_function = Mock()
        mock_function.name = "mcp__filesystem__write_file"
        mock_function.arguments = '{"path": "/test.txt", "content": "hello"}'

        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function

        result = provider._parse_tool_call(mock_tool_call)

        assert result is not None
        assert result["id"] == "call_123"
        assert result["server"] == "filesystem"
        assert result["name"] == "write_file"
        assert result["arguments"]["path"] == "/test.txt"
        assert result["arguments"]["content"] == "hello"

    def test_parse_tool_call_bad_json_is_handled(self):
        """Test parsing tool call with malformed JSON arguments."""
        provider = LLMProvider("gpt-4")

        mock_function = Mock()
        mock_function.name = "mcp__time__get_time"
        mock_function.arguments = '{invalid json'  # Malformed JSON

        mock_tool_call = Mock()
        mock_tool_call.id = "call_456"
        mock_tool_call.function = mock_function

        with patch('src.llm_provider.logger'):
            result = provider._parse_tool_call(mock_tool_call)

        assert result is not None
        assert result["server"] == "time"
        assert result["name"] == "get_time"
        # Should store raw and error
        assert "_raw" in result["arguments"]
        assert "_parse_error" in result["arguments"]

    def test_parse_tool_call_already_parsed_dict(self):
        """Test parsing when arguments are already a dict."""
        provider = LLMProvider("gpt-4")

        mock_function = Mock()
        mock_function.name = "mcp__test__tool"
        mock_function.arguments = {"key": "value"}  # Already parsed

        mock_tool_call = Mock()
        mock_tool_call.id = "call_789"
        mock_tool_call.function = mock_function

        result = provider._parse_tool_call(mock_tool_call)

        assert result is not None
        assert result["arguments"] == {"key": "value"}


class TestChatResponseParsing:
    """Test chat response parsing with edge cases."""

    def test_parse_response_text_content(self):
        """Test parsing response with text content."""
        provider = LLMProvider("gpt-4")

        mock_message = Mock()
        mock_message.content = "This is a response"
        mock_message.tool_calls = None

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20

        mock_response = Mock()
        mock_response.id = "resp_123"
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        result = provider._parse_response(mock_response)

        assert result["id"] == "resp_123"
        assert result["model"] == "gpt-4"
        assert result["stop_reason"] == "stop"
        assert len(result["content"]) == 1
        assert result["content"][0]["text"] == "This is a response"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 20
        assert len(result["tool_calls"]) == 0

    def test_parse_response_usage_defaults_when_missing(self):
        """Test parsing response when usage is missing."""
        provider = LLMProvider("gpt-4")

        mock_message = Mock()
        mock_message.content = "Response"
        mock_message.tool_calls = None

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_response = Mock()
        mock_response.id = "resp_456"
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice]
        mock_response.usage = None  # Missing usage

        with patch('src.llm_provider.logger'):
            result = provider._parse_response(mock_response)

        # Should default to 0
        assert result["usage"]["input_tokens"] == 0
        assert result["usage"]["output_tokens"] == 0

    def test_parse_response_with_tool_calls(self):
        """Test parsing response with tool calls."""
        provider = LLMProvider("gpt-4")

        mock_function = Mock()
        mock_function.name = "mcp__filesystem__read_file"
        mock_function.arguments = '{"path": "/test.txt"}'

        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = mock_function

        mock_message = Mock()
        mock_message.content = ""
        mock_message.tool_calls = [mock_tool_call]

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "tool_calls"

        mock_usage = Mock()
        mock_usage.prompt_tokens = 15
        mock_usage.completion_tokens = 5

        mock_response = Mock()
        mock_response.id = "resp_789"
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        result = provider._parse_response(mock_response)

        assert result["stop_reason"] == "tool_calls"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["server"] == "filesystem"
        assert result["tool_calls"][0]["name"] == "read_file"


class TestProviderFactory:
    """Test LLM provider factory function."""

    def test_create_provider_anthropic(self):
        """Test creating Anthropic provider."""
        provider = create_llm_provider("anthropic", "claude-sonnet-4-5-20250929")
        assert provider.model == "claude-sonnet-4-5-20250929"

    def test_create_provider_openai(self):
        """Test creating OpenAI provider."""
        provider = create_llm_provider("openai", "gpt-4")
        assert provider.model == "gpt-4"

    def test_create_provider_with_prefix_for_gemini(self):
        """Test creating provider with prefix for Gemini."""
        provider = create_llm_provider("gemini", "gemini-pro")
        assert provider.model == "gemini/gemini-pro"

    def test_create_provider_preserves_existing_prefix(self):
        """Test that existing prefix is preserved."""
        provider = create_llm_provider("gemini", "gemini/gemini-1.5-pro")
        assert provider.model == "gemini/gemini-1.5-pro"


class TestChatRetry:
    """Test retry logic for transient errors."""

    @patch('src.llm_provider.litellm.completion')
    @patch('src.llm_provider.time.sleep')
    def test_chat_retries_on_timeout(self, mock_sleep, mock_completion):
        """Test that chat retries on timeout errors."""
        provider = LLMProvider("gpt-4")

        # First two attempts fail with timeout, third succeeds
        mock_completion.side_effect = [
            Exception("Request timeout"),
            Exception("Request timeout"),
            self._create_mock_response()
        ]

        with patch('src.llm_provider.logger'):
            result = provider.chat(
                messages=[{"role": "user", "content": "test"}],
                system_prompt="You are helpful",
                max_retries=2
            )

        assert mock_completion.call_count == 3
        assert mock_sleep.call_count == 2
        assert result["content"][0]["text"] == "Success"

    @patch('src.llm_provider.litellm.completion')
    def test_chat_raises_after_max_retries(self, mock_completion):
        """Test that chat raises exception after max retries."""
        provider = LLMProvider("gpt-4")

        # All attempts fail
        mock_completion.side_effect = Exception("Request timeout")

        with pytest.raises(Exception, match="Request timeout"):
            with patch('src.llm_provider.logger'):
                provider.chat(
                    messages=[{"role": "user", "content": "test"}],
                    system_prompt="You are helpful",
                    max_retries=2
                )

        assert mock_completion.call_count == 3  # Initial + 2 retries

    @patch('src.llm_provider.litellm.completion')
    def test_chat_no_retry_on_non_retryable_error(self, mock_completion):
        """Test that non-retryable errors don't trigger retries."""
        provider = LLMProvider("gpt-4")

        # Non-retryable error (e.g., validation error)
        mock_completion.side_effect = ValueError("Invalid parameter")

        with pytest.raises(ValueError, match="Invalid parameter"):
            with patch('src.llm_provider.logger'):
                provider.chat(
                    messages=[{"role": "user", "content": "test"}],
                    system_prompt="You are helpful",
                    max_retries=2
                )

        # Should only try once (no retries for non-retryable errors)
        assert mock_completion.call_count == 1

    @staticmethod
    def _create_mock_response():
        """Create a mock successful response."""
        mock_message = Mock()
        mock_message.content = "Success"
        mock_message.tool_calls = None

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_usage = Mock()
        mock_usage.prompt_tokens = 5
        mock_usage.completion_tokens = 10

        mock_response = Mock()
        mock_response.id = "resp_success"
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        return mock_response


class TestAPIKeyHandling:
    """Test API key environment variable handling."""

    @patch.dict('os.environ', {}, clear=True)
    def test_set_api_key_when_not_set(self):
        """Test setting API key when env var not set."""
        import os
        provider = LLMProvider("claude-sonnet-4-5-20250929", api_key="test-key-123")
        assert os.getenv("ANTHROPIC_API_KEY") == "test-key-123"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'existing-key'}, clear=True)
    def test_does_not_overwrite_existing_api_key(self):
        """Test that existing API key is not overwritten."""
        import os
        with patch('src.llm_provider.logger'):
            provider = LLMProvider("claude-sonnet-4-5-20250929", api_key="new-key")
        # Should keep existing key
        assert os.getenv("ANTHROPIC_API_KEY") == "existing-key"

    @patch.dict('os.environ', {}, clear=True)
    def test_gemini_uses_google_api_key(self):
        """Test that Gemini sets GOOGLE_API_KEY."""
        import os
        provider = LLMProvider("gemini/gemini-pro", api_key="gemini-key-123")
        assert os.getenv("GOOGLE_API_KEY") == "gemini-key-123"

    @patch.dict('os.environ', {}, clear=True)
    def test_ollama_does_not_set_api_key(self):
        """Test that Ollama doesn't set any API key."""
        import os
        with patch('src.llm_provider.logger'):
            provider = LLMProvider("ollama/llama2", api_key="should-not-be-used")
        # No API key should be set for Ollama
        assert os.getenv("OLLAMA_API_KEY") is None
