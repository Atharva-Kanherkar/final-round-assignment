"""Input validation and sanitization utilities."""
import re
from typing import Any, Dict, Optional
from pathlib import Path

from .exceptions import (
    InvalidResumeError,
    InvalidJobDescriptionError,
    InvalidInputError,
    ConfigurationError
)


class InputValidator:
    """Validate and sanitize user inputs."""

    # Security patterns
    DANGEROUS_PATTERNS = [
        r'<script',  # XSS
        r'javascript:',  # XSS
        r'\.\./',  # Path traversal
        r'\$\{',  # Template injection
        r'exec\(',  # Code execution
        r'eval\(',  # Code execution
        r'__import__',  # Import injection
    ]

    # Limits
    MAX_RESUME_SIZE = 500_000  # 500KB
    MAX_JD_SIZE = 100_000  # 100KB
    MAX_RESPONSE_LENGTH = 50_000  # 50K chars
    MAX_INPUT_LENGTH = 10_000  # 10K chars
    MIN_RESUME_LENGTH = 50  # Minimum meaningful resume
    MIN_JD_LENGTH = 50  # Minimum meaningful JD

    @classmethod
    def validate_resume(cls, text: str) -> str:
        """
        Validate and sanitize resume text.

        Args:
            text: Raw resume text

        Returns:
            Sanitized resume text

        Raises:
            InvalidResumeError: If resume is invalid
        """
        if not text or not text.strip():
            raise InvalidResumeError("Resume is empty")

        # Check size
        if len(text) > cls.MAX_RESUME_SIZE:
            raise InvalidResumeError(f"Resume too large (max {cls.MAX_RESUME_SIZE} bytes)")

        if len(text.strip()) < cls.MIN_RESUME_LENGTH:
            raise InvalidResumeError(f"Resume too short (min {cls.MIN_RESUME_LENGTH} characters)")

        # Check for binary/non-text data
        if cls._is_binary(text):
            raise InvalidResumeError("Resume appears to be binary data")

        # Security check
        if cls._contains_dangerous_content(text):
            raise InvalidResumeError("Resume contains potentially malicious content")

        # Sanitize
        sanitized = cls._sanitize_text(text)

        # Check if sanitization removed too much
        if len(sanitized.strip()) < cls.MIN_RESUME_LENGTH:
            raise InvalidResumeError("Resume contains insufficient valid text")

        return sanitized

    @classmethod
    def validate_job_description(cls, text: str) -> str:
        """
        Validate and sanitize job description.

        Args:
            text: Raw job description text

        Returns:
            Sanitized job description

        Raises:
            InvalidJobDescriptionError: If JD is invalid
        """
        if not text or not text.strip():
            raise InvalidJobDescriptionError("Job description is empty")

        # Check size
        if len(text) > cls.MAX_JD_SIZE:
            raise InvalidJobDescriptionError(f"Job description too large (max {cls.MAX_JD_SIZE} bytes)")

        if len(text.strip()) < cls.MIN_JD_LENGTH:
            raise InvalidJobDescriptionError(f"Job description too short (min {cls.MIN_JD_LENGTH} characters)")

        # Check for binary/non-text data
        if cls._is_binary(text):
            raise InvalidJobDescriptionError("Job description appears to be binary data")

        # Security check
        if cls._contains_dangerous_content(text):
            raise InvalidJobDescriptionError("Job description contains potentially malicious content")

        # Sanitize
        sanitized = cls._sanitize_text(text)

        if len(sanitized.strip()) < cls.MIN_JD_LENGTH:
            raise InvalidJobDescriptionError("Job description contains insufficient valid text")

        return sanitized

    @classmethod
    def validate_user_response(cls, text: str) -> str:
        """
        Validate and sanitize user response.

        Args:
            text: User's response

        Returns:
            Sanitized response

        Raises:
            InvalidInputError: If response is invalid
        """
        if not text:
            # Empty is allowed (user might skip)
            return ""

        # Check length
        if len(text) > cls.MAX_RESPONSE_LENGTH:
            # Truncate with warning
            text = text[:cls.MAX_RESPONSE_LENGTH]

        # Security check
        if cls._contains_dangerous_content(text):
            raise InvalidInputError("response", "Contains potentially malicious content")

        # Sanitize
        return cls._sanitize_text(text)

    @classmethod
    def validate_file_path(cls, filepath: str, must_exist: bool = True) -> Path:
        """
        Validate file path for security.

        Args:
            filepath: Path to validate
            must_exist: Whether file must exist

        Returns:
            Validated Path object

        Raises:
            InvalidInputError: If path is invalid
        """
        try:
            path = Path(filepath).resolve()
        except Exception as e:
            raise InvalidInputError("filepath", f"Invalid path: {str(e)}")

        # Check for path traversal
        if '..' in filepath:
            raise InvalidInputError("filepath", "Path traversal detected")

        # Check if exists
        if must_exist and not path.exists():
            raise InvalidInputError("filepath", f"File not found: {filepath}")

        # Check if it's actually a file
        if must_exist and not path.is_file():
            raise InvalidInputError("filepath", f"Not a file: {filepath}")

        return path

    @classmethod
    def validate_config_value(cls, key: str, value: Any, value_type: type, min_val: Optional[Any] = None, max_val: Optional[Any] = None) -> Any:
        """
        Validate configuration value.

        Args:
            key: Configuration key
            value: Value to validate
            value_type: Expected type
            min_val: Minimum value (for numbers)
            max_val: Maximum value (for numbers)

        Returns:
            Validated value

        Raises:
            ConfigurationError: If value is invalid
        """
        # Type check
        if not isinstance(value, value_type):
            try:
                value = value_type(value)
            except (ValueError, TypeError):
                raise ConfigurationError(key, f"Expected {value_type.__name__}, got {type(value).__name__}")

        # Range check for numbers
        if isinstance(value, (int, float)):
            if min_val is not None and value < min_val:
                raise ConfigurationError(key, f"Value {value} below minimum {min_val}")
            if max_val is not None and value > max_val:
                raise ConfigurationError(key, f"Value {value} above maximum {max_val}")

        return value

    @classmethod
    def _is_binary(cls, text: str) -> bool:
        """Check if text appears to be binary data."""
        # Check for high ratio of non-printable characters
        non_printable = sum(1 for c in text[:1000] if ord(c) < 32 and c not in '\n\r\t')
        ratio = non_printable / len(text[:1000])
        return ratio > 0.3

    @classmethod
    def _contains_dangerous_content(cls, text: str) -> bool:
        """Check for potentially dangerous content."""
        text_lower = text.lower()
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False

    @classmethod
    def _sanitize_text(cls, text: str) -> str:
        """Sanitize text input."""
        # Remove null bytes
        text = text.replace('\x00', '')

        # Remove control characters except newlines, tabs, and carriage returns
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\n\r\t')

        # Normalize horizontal whitespace (collapse multiple spaces/tabs)
        # but preserve newlines
        lines = text.split('\n')
        lines = [re.sub(r'[ \t]+', ' ', line) for line in lines]
        text = '\n'.join(lines)

        return text.strip()


class AgentOutputValidator:
    """Validate agent outputs."""

    @classmethod
    def validate_question(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate question generation output.

        Args:
            data: Agent output

        Returns:
            Validated data

        Raises:
            AgentValidationError: If output is invalid
        """
        from .exceptions import AgentValidationError

        required_fields = ["question", "reasoning", "expected_elements"]

        # Check all fields present
        for field in required_fields:
            if field not in data:
                raise AgentValidationError("InterviewerAgent", f"Missing field: {field}")

        # Validate question
        if not isinstance(data["question"], str) or not data["question"].strip():
            raise AgentValidationError("InterviewerAgent", "Question is empty")

        if len(data["question"]) < 10:
            raise AgentValidationError("InterviewerAgent", "Question too short")

        if len(data["question"]) > 1000:
            raise AgentValidationError("InterviewerAgent", "Question too long")

        # Validate expected_elements
        if not isinstance(data["expected_elements"], list):
            raise AgentValidationError("InterviewerAgent", "expected_elements must be a list")

        if len(data["expected_elements"]) == 0:
            # Add default
            data["expected_elements"] = ["Relevant answer", "Specific examples"]

        return data

    @classmethod
    def validate_evaluation(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate evaluation output.

        Args:
            data: Agent output

        Returns:
            Validated data with clamped scores

        Raises:
            AgentValidationError: If output is invalid
        """
        from .exceptions import AgentValidationError

        required_fields = ["technical_accuracy", "depth", "clarity", "relevance", "strengths", "gaps", "feedback"]

        # Check all fields present
        for field in required_fields:
            if field not in data:
                raise AgentValidationError("EvaluatorAgent", f"Missing field: {field}")

        # Validate and clamp scores
        score_fields = ["technical_accuracy", "depth", "clarity", "relevance"]
        for field in score_fields:
            try:
                score = float(data[field])
                # Clamp to 0-5 range
                data[field] = max(0.0, min(5.0, score))
            except (ValueError, TypeError):
                raise AgentValidationError("EvaluatorAgent", f"Invalid score for {field}")

        # Validate lists
        if not isinstance(data["strengths"], list):
            data["strengths"] = []

        if not isinstance(data["gaps"], list):
            data["gaps"] = []

        # Validate feedback
        if not isinstance(data["feedback"], str):
            data["feedback"] = "Thank you for your response."

        return data

    @classmethod
    def validate_topic_transition(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate topic transition decision.

        Args:
            data: Agent output

        Returns:
            Validated data

        Raises:
            AgentValidationError: If output is invalid
        """
        from .exceptions import AgentValidationError

        required_fields = ["should_transition", "reasoning"]

        for field in required_fields:
            if field not in data:
                raise AgentValidationError("TopicManagerAgent", f"Missing field: {field}")

        # Validate boolean
        if not isinstance(data["should_transition"], bool):
            raise AgentValidationError("TopicManagerAgent", "should_transition must be boolean")

        # If transitioning, need next_topic
        if data["should_transition"] and not data.get("next_topic"):
            raise AgentValidationError("TopicManagerAgent", "next_topic required when transitioning")

        return data
