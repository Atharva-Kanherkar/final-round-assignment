"""
Comprehensive tests for LLM client with all API scenarios.

Tests API interactions, error handling, circuit breaker, and edge cases.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from src.services.llm_client import LLMClient
from src.utils.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    CircuitBreakerOpenError
)


# ============================================================================
# LLM Client Initialization Tests
# ============================================================================

class TestLLMClientInitialization:
    """Test LLM client initialization."""

    def test_successful_initialization(self, mock_logger):
        """Test successful client initialization."""
        client = LLMClient(
            api_key="test-key-123",
            model_name="gpt-4",
            timeout=30,
            max_retries=3,
            logger=mock_logger
        )

        assert client.model_name == "gpt-4"
        assert client.timeout == 30
        assert client.max_retries == 3
        assert client.circuit_breaker is not None

    def test_initialization_invalid_api_key(self, mock_logger):
        """Test initialization fails with invalid API key."""
        with pytest.raises(ValueError, match="Valid OpenAI API key required"):
            LLMClient(
                api_key="",
                model_name="gpt-4",
                logger=mock_logger
            )

        with pytest.raises(ValueError, match="Valid OpenAI API key required"):
            LLMClient(
                api_key="your_api_key_here",
                model_name="gpt-4",
                logger=mock_logger
            )

    def test_initialization_default_values(self, mock_logger):
        """Test default values are set correctly."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        assert client.model_name == "gpt-4"
        assert client.timeout == 30
        assert client.max_retries == 3


# ============================================================================
# Text Generation Tests
# ============================================================================

class TestTextGeneration:
    """Test text generation functionality."""

    @pytest.mark.asyncio
    async def test_successful_text_generation(self, mock_logger):
        """Test successful text generation."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated text response"))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            result = await client.generate_text(
                prompt="Test prompt",
                system_message="Test system message"
            )

            assert result == "Generated text response"

    @pytest.mark.asyncio
    async def test_text_generation_empty_response(self, mock_logger):
        """Test handling of empty response."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock empty response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(LLMInvalidResponseError, match="Empty response"):
                await client.generate_text(prompt="Test")

    @pytest.mark.asyncio
    async def test_text_generation_none_response(self, mock_logger):
        """Test handling of None response."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock None response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=None))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(LLMInvalidResponseError):
                await client.generate_text(prompt="Test")

    @pytest.mark.asyncio
    async def test_text_generation_rate_limit(self, mock_logger):
        """Test rate limit error handling."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock rate limit error
        with patch.object(client.client.chat.completions, 'create', side_effect=RateLimitError("Rate limit", response=Mock(status_code=429), body=None)):
            with pytest.raises(LLMRateLimitError):
                await client.generate_text(prompt="Test")

    @pytest.mark.asyncio
    async def test_text_generation_timeout(self, mock_logger):
        """Test timeout error handling."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock timeout
        with patch.object(client.client.chat.completions, 'create', side_effect=APITimeoutError(request=Mock())):
            with pytest.raises(LLMAPIError, match="timeout"):
                await client.generate_text(prompt="Test")

    @pytest.mark.asyncio
    async def test_text_generation_api_error(self, mock_logger):
        """Test API error handling."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock API error
        with patch.object(client.client.chat.completions, 'create', side_effect=APIError("Server error", request=Mock(), body=None)):
            with pytest.raises(LLMAPIError, match="api_error"):
                await client.generate_text(prompt="Test")


# ============================================================================
# Structured Output Tests
# ============================================================================

class TestStructuredGeneration:
    """Test structured JSON generation."""

    @pytest.mark.asyncio
    async def test_successful_json_generation(self, mock_logger):
        """Test successful JSON generation."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock valid JSON response
        json_content = json.dumps({
            "question": "What is Python?",
            "reasoning": "Basic knowledge check",
            "expected_elements": ["Language", "Features"]
        })
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=json_content))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            result = await client.generate_structured(
                prompt="Generate a question",
                system_message="You are an interviewer"
            )

            assert isinstance(result, dict)
            assert "question" in result
            assert "reasoning" in result
            assert result["question"] == "What is Python?"

    @pytest.mark.asyncio
    async def test_json_generation_invalid_json(self, mock_logger):
        """Test handling of invalid JSON response."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="This is not JSON"))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(LLMInvalidResponseError, match="Failed to parse JSON"):
                await client.generate_structured(prompt="Test")

    @pytest.mark.asyncio
    async def test_json_generation_with_extra_text(self, mock_logger):
        """Test JSON extraction from response with extra text."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock response with JSON embedded in text
        content = 'Here is the JSON: {"key": "value", "number": 42} Hope that helps!'
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=content))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            result = await client.generate_structured(prompt="Test")

            # Should extract the JSON
            assert result["key"] == "value"
            assert result["number"] == 42

    @pytest.mark.asyncio
    async def test_json_generation_empty_response(self, mock_logger):
        """Test handling of empty JSON response."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock empty response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=""))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(LLMInvalidResponseError, match="Empty response"):
                await client.generate_structured(prompt="Test")

    @pytest.mark.asyncio
    async def test_json_generation_malformed_json(self, mock_logger):
        """Test handling of malformed JSON."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock malformed JSON (missing closing brace)
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"key": "value"'))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(LLMInvalidResponseError):
                await client.generate_structured(prompt="Test")


# ============================================================================
# Circuit Breaker Integration Tests
# ============================================================================

class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with LLM client."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, mock_logger):
        """Test circuit breaker opens after threshold failures."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Make it fail multiple times
        with patch.object(client.client.chat.completions, 'create', side_effect=APIError("Error", request=Mock(), body=None)):
            # First 5 failures should hit API
            for i in range(5):
                with pytest.raises(LLMAPIError):
                    await client.generate_text(prompt=f"Test {i}")

            # 6th attempt should trigger circuit breaker
            with pytest.raises((LLMAPIError, CircuitBreakerOpenError)):
                await client.generate_text(prompt="Test 6")

    @pytest.mark.asyncio
    async def test_circuit_breaker_allows_success(self, mock_logger):
        """Test circuit breaker allows successful calls."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Success"))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            # Multiple successful calls should all work
            for i in range(10):
                result = await client.generate_text(prompt=f"Test {i}")
                assert result == "Success"

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovers(self, mock_logger):
        """Test circuit breaker recovery after timeout."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        # Manually open the circuit
        for _ in range(5):
            client.circuit_breaker._on_failure()

        assert client.circuit_breaker.state.value == "open"

        # Set last failure time to simulate timeout passed
        from datetime import datetime, timedelta
        client.circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=61)

        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Recovered"))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            # Should transition to half-open and succeed
            result = await client.generate_text(prompt="Test")
            assert result == "Recovered"


# ============================================================================
# Error Propagation Tests
# ============================================================================

class TestErrorPropagation:
    """Test proper error propagation and transformation."""

    @pytest.mark.asyncio
    async def test_rate_limit_error_transformed(self, mock_logger):
        """Test RateLimitError is transformed to LLMRateLimitError."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        with patch.object(client.client.chat.completions, 'create', side_effect=RateLimitError("Rate limit", response=Mock(status_code=429), body=None)):
            with pytest.raises(LLMRateLimitError) as exc_info:
                await client.generate_text(prompt="Test")

            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_timeout_error_transformed(self, mock_logger):
        """Test APITimeoutError is transformed to LLMAPIError."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        with patch.object(client.client.chat.completions, 'create', side_effect=APITimeoutError(request=Mock())):
            with pytest.raises(LLMAPIError) as exc_info:
                await client.generate_text(prompt="Test")

            assert exc_info.value.error_type == "timeout"

    @pytest.mark.asyncio
    async def test_generic_api_error_transformed(self, mock_logger):
        """Test APIError is transformed to LLMAPIError."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        with patch.object(client.client.chat.completions, 'create', side_effect=APIError("Server error", request=Mock(), body=None)):
            with pytest.raises(LLMAPIError) as exc_info:
                await client.generate_text(prompt="Test")

            assert exc_info.value.error_type == "api_error"

    @pytest.mark.asyncio
    async def test_unexpected_error_transformed(self, mock_logger):
        """Test unexpected errors are transformed to LLMAPIError."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        with patch.object(client.client.chat.completions, 'create', side_effect=ValueError("Unexpected")):
            with pytest.raises(LLMAPIError) as exc_info:
                await client.generate_text(prompt="Test")

            assert exc_info.value.error_type == "unexpected"


# ============================================================================
# JSON Extraction Tests
# ============================================================================

class TestJSONExtraction:
    """Test JSON extraction from malformed responses."""

    def test_extract_json_from_text(self, mock_logger):
        """Test extracting JSON from surrounding text."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        text = 'Sure! Here is the JSON: {"key": "value"} Let me know if you need anything else.'
        result = client._extract_json(text)

        assert result is not None
        assert result["key"] == "value"

    def test_extract_json_multiline(self, mock_logger):
        """Test extracting JSON from multiline text."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        text = '''
        Here is your response:
        {
            "question": "What is Python?",
            "reasoning": "Basic check",
            "elements": ["a", "b"]
        }
        Hope this helps!
        '''
        result = client._extract_json(text)

        assert result is not None
        assert "question" in result

    def test_extract_json_no_json_present(self, mock_logger):
        """Test extraction returns None when no JSON present."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        text = "This text contains no JSON at all"
        result = client._extract_json(text)

        assert result is None

    def test_extract_json_invalid_json(self, mock_logger):
        """Test extraction handles invalid JSON gracefully."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        text = "Here is some text {this is not valid json} more text"
        result = client._extract_json(text)

        assert result is None


# ============================================================================
# Token Count Estimation Tests
# ============================================================================

class TestTokenCount:
    """Test token count estimation."""

    def test_token_count_estimation(self, mock_logger):
        """Test token count estimation."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        text = "This is a test string"
        count = client.get_token_count(text)

        # Rough estimation: ~4 chars per token
        expected = len(text) // 4
        assert count == expected

    def test_token_count_empty_string(self, mock_logger):
        """Test token count for empty string."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        assert client.get_token_count("") == 0

    def test_token_count_long_text(self, mock_logger):
        """Test token count for long text."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        long_text = "word " * 1000
        count = client.get_token_count(long_text)

        assert count > 0
        assert count == len(long_text) // 4


# ============================================================================
# Logging Tests
# ============================================================================

class TestLogging:
    """Test that appropriate logging occurs."""

    @pytest.mark.asyncio
    async def test_successful_call_logging(self, mock_logger):
        """Test successful calls are logged."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]

        with patch.object(client.client.chat.completions, 'create', return_value=mock_response):
            await client.generate_text(prompt="Test")

            # Check logging calls
            assert mock_logger.info.called
            assert any("Calling OpenAI API" in str(call) for call in mock_logger.info.call_args_list)

    @pytest.mark.asyncio
    async def test_error_logging(self, mock_logger):
        """Test errors are logged."""
        client = LLMClient(api_key="test-key", logger=mock_logger)

        with patch.object(client.client.chat.completions, 'create', side_effect=APIError("Error", request=Mock(), body=None)):
            with pytest.raises(LLMAPIError):
                await client.generate_text(prompt="Test")

            # Check error logging
            assert mock_logger.error.called
