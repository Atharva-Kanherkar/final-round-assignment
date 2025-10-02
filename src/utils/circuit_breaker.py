"""Circuit breaker pattern for API failure resilience."""
import time
from enum import Enum
from typing import Callable, Any, Optional
from datetime import datetime, timedelta
import logging

from .exceptions import CircuitBreakerOpenError


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by failing fast when a service is down.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Service name
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            logger: Logger instance
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.logger = logger or logging.getLogger(__name__)

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if circuit is closed
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                self.logger.warning(f"Circuit breaker OPEN for {self.name}, rejecting request")
                raise CircuitBreakerOpenError(self.name, self.failure_count)

        try:
            # Attempt the call
            result = func(*args, **kwargs)

            # Success - record it
            self._on_success()

            return result

        except self.expected_exception as e:
            # Failure - record it
            self._on_failure()

            # Re-raise the exception
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state to test recovery."""
        self.logger.info(f"Circuit breaker for {self.name} transitioning to HALF_OPEN")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            # After 2 successful calls in half-open, close the circuit
            if self.success_count >= 2:
                self._transition_to_closed()

    def _transition_to_closed(self) -> None:
        """Transition to closed state (normal operation)."""
        self.logger.info(f"Circuit breaker for {self.name} transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        self.logger.warning(
            f"Circuit breaker for {self.name}: Failure {self.failure_count}/{self.failure_threshold}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open means service still down
            self._transition_to_open()

        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open the circuit
            self._transition_to_open()

    def _transition_to_open(self) -> None:
        """Transition to open state (failing fast)."""
        self.logger.error(
            f"Circuit breaker for {self.name} transitioning to OPEN after {self.failure_count} failures"
        )
        self.state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self.logger.info(f"Manually resetting circuit breaker for {self.name}")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class CircuitBreakerManager:
    """Manage multiple circuit breakers."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize manager."""
        self.logger = logger or logging.getLogger(__name__)
        self.breakers: dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Service name
            failure_threshold: Failures before opening
            recovery_timeout: Recovery timeout in seconds
            expected_exception: Exception type to catch

        Returns:
            CircuitBreaker instance
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                expected_exception=expected_exception,
                logger=self.logger
            )

        return self.breakers[name]

    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self.breakers.values():
            breaker.reset()

    def get_status_all(self) -> dict:
        """Get status of all circuit breakers."""
        return {
            name: breaker.get_status()
            for name, breaker in self.breakers.items()
        }
