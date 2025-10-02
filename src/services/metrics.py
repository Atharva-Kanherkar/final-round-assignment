"""Metrics collection and tracking for interview system."""
import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass, field


@dataclass
class MetricData:
    """Container for a single metric."""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collect and track performance metrics."""

    def __init__(self, logger: logging.Logger):
        """
        Initialize metrics collector.

        Args:
            logger: Logger instance
        """
        self.logger = logger
        self.metrics: Dict[str, list] = {}
        self.timers: Dict[str, float] = {}

    def record(self, name: str, value: float, unit: str = "", labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            unit: Unit of measurement (e.g., "ms", "count", "score")
            labels: Additional labels for the metric
        """
        metric = MetricData(
            name=name,
            value=value,
            unit=unit,
            labels=labels or {}
        )

        if name not in self.metrics:
            self.metrics[name] = []

        self.metrics[name].append(metric)

        self.logger.debug(
            f"Metric recorded: {name}={value}{unit}",
            extra={"metric": name, "value": value, "unit": unit, "labels": labels}
        )

    def start_timer(self, name: str) -> None:
        """
        Start a timer for measuring duration.

        Args:
            name: Timer name
        """
        self.timers[name] = time.time()

    def stop_timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Stop a timer and record the duration.

        Args:
            name: Timer name
            labels: Additional labels for the metric

        Returns:
            Duration in seconds
        """
        if name not in self.timers:
            self.logger.warning(f"Timer {name} was not started")
            return 0.0

        duration = time.time() - self.timers[name]
        del self.timers[name]

        # Record as milliseconds
        self.record(f"{name}_duration", duration * 1000, "ms", labels)

        return duration

    def increment(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Increment a counter metric.

        Args:
            name: Counter name
            value: Increment value
            labels: Additional labels
        """
        self.record(name, value, "count", labels)

    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """
        Get summary statistics for a metric.

        Args:
            name: Metric name

        Returns:
            Dictionary with min, max, avg, count
        """
        if name not in self.metrics or not self.metrics[name]:
            return {"count": 0}

        values = [m.value for m in self.metrics[name]]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }

    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summaries for all metrics.

        Returns:
            Dictionary mapping metric names to summaries
        """
        return {
            name: self.get_metric_summary(name)
            for name in self.metrics.keys()
        }

    def log_summary(self) -> None:
        """Log summary of all collected metrics."""
        summaries = self.get_all_summaries()

        self.logger.info("=== Metrics Summary ===")
        for name, summary in summaries.items():
            if summary["count"] > 0:
                unit = self.metrics[name][0].unit
                if "avg" in summary:
                    self.logger.info(
                        f"{name}: avg={summary['avg']:.2f}{unit}, "
                        f"min={summary['min']:.2f}{unit}, "
                        f"max={summary['max']:.2f}{unit}, "
                        f"count={summary['count']}"
                    )
                else:
                    self.logger.info(f"{name}: count={summary['count']}")

    def reset(self) -> None:
        """Clear all collected metrics."""
        self.metrics.clear()
        self.timers.clear()
        self.logger.debug("Metrics reset")
