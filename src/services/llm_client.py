"""LLM client with retry logic and structured output support."""
import json
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from ..utils.circuit_breaker import CircuitBreaker
from ..utils.exceptions import (
    LLMAPIError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    CircuitBreakerOpenError
)


class LLMClient:
    """Wrapper for LLM API calls with retry logic and error handling."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-4",
        timeout: int = 30,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key
            model_name: Model to use (e.g., "gpt-4", "gpt-3.5-turbo")
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            logger: Logger instance
        """
        if not api_key or api_key == "your_api_key_here":
            raise ValueError("Valid OpenAI API key required")

        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)

        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            name="OpenAI_API",
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=(APIError, APITimeoutError, RateLimitError),
            logger=self.logger
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        reraise=True
    )
    async def generate_text(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            system_message: System message for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text

        Raises:
            LLMAPIError: If API call fails
            CircuitBreakerOpenError: If circuit breaker is open
        """
        def _api_call():
            self.logger.info(f"🤖 Calling OpenAI API ({self.model_name})...")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = response.choices[0].message.content

            if not result or not result.strip():
                raise LLMInvalidResponseError("Empty response from API", "")

            self.logger.info(f"✓ OpenAI API response received ({len(result)} characters)")
            return result

        try:
            # Use circuit breaker to protect against cascading failures
            return self.circuit_breaker.call(_api_call)

        except RateLimitError as e:
            self.logger.error(f"❌ Rate limit exceeded: {str(e)}")
            raise LLMRateLimitError(retry_after=60)

        except APITimeoutError as e:
            self.logger.error(f"❌ API timeout: {str(e)}")
            raise LLMAPIError("timeout", str(e), 0)

        except APIError as e:
            self.logger.error(f"❌ API error: {str(e)}")
            raise LLMAPIError("api_error", str(e), 0)

        except CircuitBreakerOpenError:
            # Re-raise circuit breaker errors
            raise

        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {str(e)}")
            raise LLMAPIError("unexpected", str(e), 0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((APITimeoutError, RateLimitError, APIError)),
        reraise=True
    )
    async def generate_structured(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        response_format: Optional[Dict[str, str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.

        Args:
            prompt: User prompt requesting JSON output
            system_message: System message for context
            response_format: Expected format description (for documentation)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON dictionary

        Raises:
            LLMAPIError: If API call fails
            LLMInvalidResponseError: If response is not valid JSON
            CircuitBreakerOpenError: If circuit breaker is open
        """
        def _api_call():
            self.logger.info(f"🤖 Calling OpenAI API ({self.model_name}) for structured output...")

            # Enhance prompt to request JSON
            json_prompt = f"""{prompt}

IMPORTANT: Return your response as a valid JSON object. Do not include any text before or after the JSON."""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": json_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}  # Enable JSON mode
            )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise LLMInvalidResponseError("Empty response from API", "")

            self.logger.info(f"✓ OpenAI API response received")

            # Parse JSON
            try:
                result = json.loads(content)
                self.logger.info(f"✓ JSON parsed successfully with keys: {list(result.keys())}")
                return result
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Failed to parse JSON: {e}")
                # Try to extract JSON from text
                result = self._extract_json(content)
                if result:
                    self.logger.info(f"✓ Extracted JSON from response")
                    return result
                raise LLMInvalidResponseError(
                    f"Failed to parse JSON: {str(e)}",
                    content[:200]
                )

        try:
            # Use circuit breaker
            return self.circuit_breaker.call(_api_call)

        except RateLimitError as e:
            self.logger.error(f"❌ Rate limit exceeded: {str(e)}")
            raise LLMRateLimitError(retry_after=60)

        except APITimeoutError as e:
            self.logger.error(f"❌ API timeout: {str(e)}")
            raise LLMAPIError("timeout", str(e), 0)

        except APIError as e:
            self.logger.error(f"❌ API error: {str(e)}")
            raise LLMAPIError("api_error", str(e), 0)

        except LLMInvalidResponseError:
            # Re-raise our custom errors
            raise

        except CircuitBreakerOpenError:
            raise

        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {str(e)}")
            raise LLMAPIError("unexpected", str(e), 0)

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to extract JSON from text that may contain extra content."""
        import re

        # Try to find JSON object in text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return None

    def get_token_count(self, text: str) -> int:
        """
        Estimate token count for text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token
        return len(text) // 4
