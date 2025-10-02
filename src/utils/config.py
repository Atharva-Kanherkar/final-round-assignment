"""Configuration management for the interview system."""
import os
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration container for interview system."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load .env file if it exists
        load_dotenv()

        # API Configuration
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.model_name: str = os.getenv("MODEL_NAME", "gpt-4")

        # Interview Configuration
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "30"))
        self.questions_per_topic_min: int = int(os.getenv("QUESTIONS_PER_TOPIC_MIN", "2"))
        self.questions_per_topic_max: int = int(os.getenv("QUESTIONS_PER_TOPIC_MAX", "4"))
        self.total_topics_target: int = int(os.getenv("TOTAL_TOPICS_TARGET", "5"))

        # Logging Configuration
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        # File paths
        self.data_dir: str = os.getenv("DATA_DIR", "data")
        self.sessions_dir: str = os.getenv("SESSIONS_DIR", "sessions")

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.openai_api_key:
            print("ERROR: OPENAI_API_KEY not set. Please set it in .env file or environment.")
            return False

        if self.questions_per_topic_min > self.questions_per_topic_max:
            print("ERROR: QUESTIONS_PER_TOPIC_MIN cannot be greater than QUESTIONS_PER_TOPIC_MAX")
            return False

        return True

    def to_dict(self) -> dict:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation (excluding sensitive data)
        """
        return {
            "model_name": self.model_name,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "questions_per_topic_min": self.questions_per_topic_min,
            "questions_per_topic_max": self.questions_per_topic_max,
            "total_topics_target": self.total_topics_target,
            "log_level": self.log_level
        }


def load_config() -> Config:
    """
    Load and validate configuration.

    Returns:
        Config object

    Raises:
        ValueError: If configuration is invalid
    """
    config = Config()
    if not config.validate():
        raise ValueError("Invalid configuration")
    return config
