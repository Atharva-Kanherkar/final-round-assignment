"""Custom exception hierarchy for interview system."""


class InterviewSystemError(Exception):
    """Base exception for all interview system errors."""
    def __init__(self, message: str, recoverable: bool = True, user_message: str = None):
        """
        Initialize exception.

        Args:
            message: Technical error message for logging
            recoverable: Whether the system can continue after this error
            user_message: User-friendly message to display
        """
        super().__init__(message)
        self.recoverable = recoverable
        self.user_message = user_message or message


# Agent Errors
class AgentError(InterviewSystemError):
    """Base class for agent-related errors."""
    pass


class AgentTimeoutError(AgentError):
    """Agent operation exceeded timeout."""
    def __init__(self, agent_name: str, timeout: int):
        super().__init__(
            f"Agent {agent_name} timed out after {timeout}s",
            recoverable=True,
            user_message=f"Operation took too long. Please try again."
        )
        self.agent_name = agent_name
        self.timeout = timeout


class AgentExecutionError(AgentError):
    """Agent failed during execution."""
    def __init__(self, agent_name: str, original_error: Exception):
        super().__init__(
            f"Agent {agent_name} failed: {str(original_error)}",
            recoverable=True,
            user_message="An error occurred while processing. Trying fallback approach."
        )
        self.agent_name = agent_name
        self.original_error = original_error


class AgentValidationError(AgentError):
    """Agent output failed validation."""
    def __init__(self, agent_name: str, validation_error: str):
        super().__init__(
            f"Agent {agent_name} output invalid: {validation_error}",
            recoverable=True,
            user_message="Response validation failed. Retrying..."
        )
        self.agent_name = agent_name
        self.validation_error = validation_error


# LLM Errors
class LLMError(InterviewSystemError):
    """Base class for LLM-related errors."""
    pass


class LLMAPIError(LLMError):
    """LLM API call failed."""
    def __init__(self, error_type: str, message: str, retry_count: int = 0):
        super().__init__(
            f"LLM API error ({error_type}): {message} (retry {retry_count})",
            recoverable=retry_count < 3,
            user_message="API is experiencing issues. Retrying..." if retry_count < 3 else "API unavailable. Please try again later."
        )
        self.error_type = error_type
        self.retry_count = retry_count


class LLMRateLimitError(LLMError):
    """LLM API rate limit exceeded."""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded. Retry after {retry_after}s",
            recoverable=True,
            user_message=f"API rate limit reached. Please wait {retry_after} seconds."
        )
        self.retry_after = retry_after


class LLMInvalidResponseError(LLMError):
    """LLM returned invalid response."""
    def __init__(self, message: str, response_preview: str = ""):
        super().__init__(
            f"Invalid LLM response: {message}. Preview: {response_preview[:100]}",
            recoverable=True,
            user_message="Received invalid response. Retrying with different approach."
        )
        self.response_preview = response_preview


class LLMContentFilterError(LLMError):
    """Content was filtered by LLM."""
    def __init__(self, reason: str):
        super().__init__(
            f"Content filtered: {reason}",
            recoverable=False,
            user_message="Content was flagged as inappropriate. Please rephrase your response."
        )
        self.reason = reason


# Input Validation Errors
class ValidationError(InterviewSystemError):
    """Base class for validation errors."""
    pass


class InvalidResumeError(ValidationError):
    """Resume is invalid or unparseable."""
    def __init__(self, reason: str):
        super().__init__(
            f"Invalid resume: {reason}",
            recoverable=False,
            user_message=f"Resume error: {reason}. Please check the file."
        )
        self.reason = reason


class InvalidJobDescriptionError(ValidationError):
    """Job description is invalid."""
    def __init__(self, reason: str):
        super().__init__(
            f"Invalid job description: {reason}",
            recoverable=False,
            user_message=f"Job description error: {reason}. Please check the file."
        )
        self.reason = reason


class InvalidInputError(ValidationError):
    """User input is invalid."""
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Invalid {field}: {reason}",
            recoverable=True,
            user_message=f"Invalid input for {field}. {reason}"
        )
        self.field = field
        self.reason = reason


# Session Errors
class SessionError(InterviewSystemError):
    """Base class for session-related errors."""
    pass


class SessionStateError(SessionError):
    """Session state is corrupted or invalid."""
    def __init__(self, reason: str):
        super().__init__(
            f"Session state error: {reason}",
            recoverable=True,
            user_message="Session encountered an error. Attempting recovery..."
        )
        self.reason = reason


class SessionNotFoundError(SessionError):
    """Session file not found."""
    def __init__(self, session_id: str):
        super().__init__(
            f"Session {session_id} not found",
            recoverable=False,
            user_message=f"Session not found. Please start a new interview."
        )
        self.session_id = session_id


class SessionSaveError(SessionError):
    """Failed to save session."""
    def __init__(self, reason: str):
        super().__init__(
            f"Failed to save session: {reason}",
            recoverable=True,
            user_message="Could not save session. Data may be lost."
        )
        self.reason = reason


# Topic Management Errors
class TopicError(InterviewSystemError):
    """Base class for topic-related errors."""
    pass


class NoTopicsError(TopicError):
    """No topics could be generated."""
    def __init__(self, reason: str):
        super().__init__(
            f"No topics generated: {reason}",
            recoverable=True,
            user_message="Could not generate interview topics. Using default topics."
        )
        self.reason = reason


class TopicTransitionError(TopicError):
    """Topic transition failed."""
    def __init__(self, from_topic: str, reason: str):
        super().__init__(
            f"Failed to transition from {from_topic}: {reason}",
            recoverable=True,
            user_message="Could not transition topics. Continuing with current topic."
        )
        self.from_topic = from_topic
        self.reason = reason


# Configuration Errors
class ConfigurationError(InterviewSystemError):
    """Configuration is invalid."""
    def __init__(self, field: str, reason: str):
        super().__init__(
            f"Configuration error in {field}: {reason}",
            recoverable=False,
            user_message=f"Configuration error: {reason}. Please check your .env file."
        )
        self.field = field
        self.reason = reason


# File I/O Errors
class FileOperationError(InterviewSystemError):
    """File operation failed."""
    def __init__(self, operation: str, filepath: str, reason: str):
        super().__init__(
            f"Failed to {operation} {filepath}: {reason}",
            recoverable=False,
            user_message=f"File error: Could not {operation} file. {reason}"
        )
        self.operation = operation
        self.filepath = filepath
        self.reason = reason


# Circuit Breaker Errors
class CircuitBreakerOpenError(InterviewSystemError):
    """Circuit breaker is open, rejecting requests."""
    def __init__(self, service: str, failure_count: int):
        super().__init__(
            f"Circuit breaker open for {service} after {failure_count} failures",
            recoverable=True,
            user_message=f"{service} is currently unavailable. Please try again in a moment."
        )
        self.service = service
        self.failure_count = failure_count
