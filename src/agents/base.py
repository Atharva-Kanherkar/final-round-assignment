"""Base agent class for all interview agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging


class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    def __init__(self, llm_client: Any, logger: logging.Logger):
        """
        Initialize the base agent.

        Args:
            llm_client: LLM client for making API calls
            logger: Logger instance for structured logging
        """
        self.llm = llm_client
        self.logger = logger
        self.agent_name = self.__class__.__name__

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main logic.

        Args:
            context: Dictionary containing all necessary context for execution

        Returns:
            Dictionary containing the agent's output
        """
        pass

    def _log_execution(self, context: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Log agent execution for debugging."""
        self.logger.debug(
            f"{self.agent_name} execution",
            extra={
                "agent": self.agent_name,
                "context_keys": list(context.keys()),
                "result_keys": list(result.keys())
            }
        )
