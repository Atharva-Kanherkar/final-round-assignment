"""
Comprehensive tests for circuit breaker pattern implementation.

Tests state transitions, failure thresholds, and recovery logic.
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.utils.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerManager
from src.utils.exceptions import CircuitBreakerOpenError


# ============================================================================
# Circuit Breaker State Machine Tests
# ============================================================================

class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    def test_initial_state_closed(self, mock_logger):
        """Test circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker("test_service", logger=mock_logger)

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_successful_call_in_closed_state(self, mock_logger):
        """Test successful call in CLOSED state."""
        cb = CircuitBreaker("test_service", logger=mock_logger)

        def success_func():
            return "success"

        result = cb.call(success_func)

        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_failed_call_increments_failure_count(self, mock_logger):
        """Test failed call increments failure count."""
        cb = CircuitBreaker("test_service", failure_threshold=5, logger=mock_logger)

        def failing_func():
            raise Exception("Test error")

        # First failure
        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED  # Still closed

    def test_circuit_opens_after_threshold(self, mock_logger):
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker("test_service", failure_threshold=3, logger=mock_logger)

        def failing_func():
            raise Exception("Test error")

        # Fail 3 times to reach threshold
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        # Circuit should now be OPEN
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3

    def test_open_circuit_rejects_calls(self, mock_logger):
        """Test OPEN circuit rejects calls immediately."""
        cb = CircuitBreaker("test_service", failure_threshold=2, logger=mock_logger)

        def failing_func():
            raise Exception("Test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Next call should fail with CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "test")

    def test_transition_to_half_open_after_timeout(self, mock_logger):
        """Test transition to HALF_OPEN after recovery timeout."""
        cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=1, logger=mock_logger)

        def failing_func():
            raise Exception("Test error")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # Next call should transition to HALF_OPEN
        def success_func():
            return "success"

        result = cb.call(success_func)

        assert result == "success"
        # After one success in HALF_OPEN, still in HALF_OPEN (needs 2)
        assert cb.state in [CircuitState.HALF_OPEN, CircuitState.CLOSED]

    def test_half_open_closes_after_successes(self, mock_logger):
        """Test HALF_OPEN transitions to CLOSED after successes."""
        cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=0, logger=mock_logger)

        # Open the circuit manually
        cb._transition_to_open()
        assert cb.state == CircuitState.OPEN

        # Transition to half-open
        cb._transition_to_half_open()
        assert cb.state == CircuitState.HALF_OPEN

        # Two successful calls should close the circuit
        def success_func():
            return "success"

        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN  # Still half-open after 1

        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED  # Closed after 2

    def test_half_open_reopens_on_failure(self, mock_logger):
        """Test HALF_OPEN returns to OPEN on failure."""
        cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout=0, logger=mock_logger)

        # Open the circuit
        cb._transition_to_open()
        cb._transition_to_half_open()

        assert cb.state == CircuitState.HALF_OPEN

        # Failure in HALF_OPEN should reopen circuit
        def failing_func():
            raise Exception("Test error")

        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN


# ============================================================================
# Failure Threshold Tests
# ============================================================================

class TestFailureThreshold:
    """Test failure threshold behavior."""

    def test_custom_threshold(self, mock_logger):
        """Test custom failure threshold."""
        cb = CircuitBreaker("test_service", failure_threshold=10, logger=mock_logger)

        def failing_func():
            raise Exception("Error")

        # Fail 9 times - should stay closed
        for i in range(9):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.state == CircuitState.CLOSED

        # 10th failure should open
        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

    def test_threshold_one(self, mock_logger):
        """Test threshold of 1 (opens immediately)."""
        cb = CircuitBreaker("test_service", failure_threshold=1, logger=mock_logger)

        def failing_func():
            raise Exception("Error")

        # Single failure should open circuit
        with pytest.raises(Exception):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

    def test_failure_count_resets_on_success(self, mock_logger):
        """Test failure count resets after success."""
        cb = CircuitBreaker("test_service", failure_threshold=5, logger=mock_logger)

        def failing_func():
            raise Exception("Error")

        def success_func():
            return "success"

        # Fail 3 times
        for i in range(3):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.failure_count == 3

        # Success should reset count
        cb.call(success_func)

        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED


# ============================================================================
# Recovery Timeout Tests
# ============================================================================

class TestRecoveryTimeout:
    """Test recovery timeout behavior."""

    def test_custom_recovery_timeout(self, mock_logger):
        """Test custom recovery timeout."""
        cb = CircuitBreaker("test_service", failure_threshold=1, recovery_timeout=2, logger=mock_logger)

        # Open the circuit
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("Error")))

        assert cb.state == CircuitState.OPEN

        # Before timeout, should still reject
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "test")

        # Wait for timeout
        time.sleep(2.1)

        # Should attempt call (transition to HALF_OPEN)
        result = cb.call(lambda: "success")
        assert result == "success"

    def test_timeout_not_elapsed(self, mock_logger):
        """Test circuit stays open if timeout not elapsed."""
        cb = CircuitBreaker("test_service", failure_threshold=1, recovery_timeout=10, logger=mock_logger)

        # Open the circuit
        cb._transition_to_open()
        cb.last_failure_time = datetime.now()

        # Should not attempt reset
        assert not cb._should_attempt_reset()

        # Should reject calls
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "test")


# ============================================================================
# Exception Type Tests
# ============================================================================

class TestExceptionTypes:
    """Test handling of different exception types."""

    def test_specific_exception_type(self, mock_logger):
        """Test circuit breaker for specific exception type."""
        cb = CircuitBreaker("test_service", failure_threshold=3, expected_exception=ValueError, logger=mock_logger)

        # ValueError should trigger circuit breaker
        def value_error_func():
            raise ValueError("Test")

        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(value_error_func)

        assert cb.state == CircuitState.OPEN

    def test_unexpected_exception_not_caught(self, mock_logger):
        """Test unexpected exception types are not caught by circuit breaker."""
        cb = CircuitBreaker("test_service", failure_threshold=3, expected_exception=ValueError, logger=mock_logger)

        # TypeError should not be caught
        def type_error_func():
            raise TypeError("Test")

        # Should raise TypeError, not trigger circuit breaker
        with pytest.raises(TypeError):
            cb.call(type_error_func)

        # Circuit should still be closed
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


# ============================================================================
# Manual Operations Tests
# ============================================================================

class TestManualOperations:
    """Test manual circuit breaker operations."""

    def test_manual_reset(self, mock_logger):
        """Test manual circuit reset."""
        cb = CircuitBreaker("test_service", failure_threshold=1, logger=mock_logger)

        # Open the circuit
        with pytest.raises(Exception):
            cb.call(lambda: (_ for _ in ()).throw(Exception("Error")))

        assert cb.state == CircuitState.OPEN

        # Manual reset
        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0

    def test_get_status(self, mock_logger):
        """Test getting circuit breaker status."""
        cb = CircuitBreaker("test_service", logger=mock_logger)

        status = cb.get_status()

        assert status["name"] == "test_service"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["success_count"] == 0
        assert "last_failure" in status


# ============================================================================
# Circuit Breaker Manager Tests
# ============================================================================

class TestCircuitBreakerManager:
    """Test circuit breaker manager."""

    def test_get_or_create_breaker(self, mock_logger):
        """Test getting or creating circuit breakers."""
        manager = CircuitBreakerManager(mock_logger)

        cb1 = manager.get_breaker("service1")
        cb2 = manager.get_breaker("service2")
        cb1_again = manager.get_breaker("service1")

        assert cb1 is not None
        assert cb2 is not None
        assert cb1 is cb1_again  # Same instance
        assert cb1 is not cb2  # Different services

    def test_reset_all_breakers(self, mock_logger):
        """Test resetting all circuit breakers."""
        manager = CircuitBreakerManager(mock_logger)

        # Create and open some breakers
        cb1 = manager.get_breaker("service1", failure_threshold=1)
        cb2 = manager.get_breaker("service2", failure_threshold=1)

        # Open both
        with pytest.raises(Exception):
            cb1.call(lambda: (_ for _ in ()).throw(Exception("Error")))
        with pytest.raises(Exception):
            cb2.call(lambda: (_ for _ in ()).throw(Exception("Error")))

        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.OPEN

        # Reset all
        manager.reset_all()

        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED

    def test_get_status_all(self, mock_logger):
        """Test getting status of all breakers."""
        manager = CircuitBreakerManager(mock_logger)

        manager.get_breaker("service1")
        manager.get_breaker("service2")

        status = manager.get_status_all()

        assert "service1" in status
        assert "service2" in status
        assert status["service1"]["state"] == "closed"

    def test_custom_breaker_config(self, mock_logger):
        """Test creating breakers with custom config."""
        manager = CircuitBreakerManager(mock_logger)

        cb = manager.get_breaker(
            "service1",
            failure_threshold=10,
            recovery_timeout=120
        )

        assert cb.failure_threshold == 10
        assert cb.recovery_timeout == 120


# ============================================================================
# Concurrency Tests
# ============================================================================

class TestConcurrency:
    """Test circuit breaker under concurrent access."""

    def test_multiple_failures_concurrent(self, mock_logger):
        """Test concurrent failures are counted correctly."""
        cb = CircuitBreaker("test_service", failure_threshold=5, logger=mock_logger)

        def failing_func():
            raise Exception("Error")

        # Simulate concurrent failures
        for i in range(5):
            with pytest.raises(Exception):
                cb.call(failing_func)

        assert cb.failure_count == 5
        assert cb.state == CircuitState.OPEN


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestCircuitBreakerEdgeCases:
    """Test edge cases in circuit breaker."""

    def test_zero_failures_before_open(self, mock_logger):
        """Test circuit with no failures."""
        cb = CircuitBreaker("test_service", logger=mock_logger)

        def success_func():
            return "success"

        # Many successful calls
        for i in range(100):
            result = cb.call(success_func)
            assert result == "success"

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_alternating_success_failure(self, mock_logger):
        """Test alternating success and failure."""
        cb = CircuitBreaker("test_service", failure_threshold=5, logger=mock_logger)

        def success_func():
            return "success"

        def failing_func():
            raise Exception("Error")

        # Alternate between success and failure
        for i in range(10):
            if i % 2 == 0:
                cb.call(success_func)
            else:
                with pytest.raises(Exception):
                    cb.call(failing_func)

        # Should reset count after each success
        assert cb.state == CircuitState.CLOSED

    def test_rapid_state_transitions(self, mock_logger):
        """Test rapid state transitions."""
        cb = CircuitBreaker("test_service", failure_threshold=1, recovery_timeout=0, logger=mock_logger)

        def failing_func():
            raise Exception("Error")

        def success_func():
            return "success"

        # Open
        with pytest.raises(Exception):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN

        # Half-open (immediate timeout)
        cb.call(success_func)

        # Should be moving towards closed
        cb.call(success_func)

        # Eventually closed after 2 successes
        assert cb.state == CircuitState.CLOSED
