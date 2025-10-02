"""Structured logging setup for the interview system."""
import logging
import sys
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str = "mock_interview",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up structured logger.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


class InterviewLogger:
    """Specialized logger for interview system with structured logging."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize interview logger.

        Args:
            logger: Base logger instance
        """
        self.logger = logger

    def session_start(self, session_id: str, candidate_name: str, job_title: str) -> None:
        """Log interview session start."""
        self.logger.info(
            f"Interview session started: {session_id}",
            extra={
                "event": "session_start",
                "session_id": session_id,
                "candidate": candidate_name,
                "job_title": job_title,
                "timestamp": datetime.now().isoformat()
            }
        )

    def session_end(self, session_id: str, duration_minutes: float, questions_asked: int) -> None:
        """Log interview session end."""
        self.logger.info(
            f"Interview session completed: {session_id}",
            extra={
                "event": "session_end",
                "session_id": session_id,
                "duration_minutes": duration_minutes,
                "questions_asked": questions_asked,
                "timestamp": datetime.now().isoformat()
            }
        )

    def topic_transition(self, session_id: str, from_topic: str, to_topic: str, reason: str) -> None:
        """Log topic transition."""
        self.logger.info(
            f"Topic transition: {from_topic} -> {to_topic}",
            extra={
                "event": "topic_transition",
                "session_id": session_id,
                "from_topic": from_topic,
                "to_topic": to_topic,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )

    def question_generated(self, session_id: str, topic: str, question_number: int) -> None:
        """Log question generation."""
        self.logger.debug(
            f"Question generated: #{question_number} on {topic}",
            extra={
                "event": "question_generated",
                "session_id": session_id,
                "topic": topic,
                "question_number": question_number,
                "timestamp": datetime.now().isoformat()
            }
        )

    def response_evaluated(self, session_id: str, topic: str, score: float) -> None:
        """Log response evaluation."""
        self.logger.debug(
            f"Response evaluated: {topic} - Score: {score}/5.0",
            extra={
                "event": "response_evaluated",
                "session_id": session_id,
                "topic": topic,
                "score": score,
                "timestamp": datetime.now().isoformat()
            }
        )

    def api_error(self, error_type: str, error_message: str, retry_count: int) -> None:
        """Log API error."""
        self.logger.error(
            f"API Error: {error_type} - {error_message}",
            extra={
                "event": "api_error",
                "error_type": error_type,
                "error_message": error_message,
                "retry_count": retry_count,
                "timestamp": datetime.now().isoformat()
            }
        )

    def metric_recorded(self, metric_name: str, value: float, unit: str) -> None:
        """Log metric recording."""
        self.logger.debug(
            f"Metric: {metric_name} = {value}{unit}",
            extra={
                "event": "metric",
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "timestamp": datetime.now().isoformat()
            }
        )
