"""Server metrics collection and logging."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import ServerState

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Metrics collector for tracking server statistics."""

    def __init__(self):
        self.total_clients = 0
        self.total_messages = 0

    def update_client_count(self, count: int) -> None:
        """Update the current client count."""
        self.total_clients = count

    def increment_messages(self, count: int = 1) -> None:
        """Increment the message counter.

        Args:
            count: Number of messages to increment by (default: 1)
        """
        self.total_messages += count

    def get_metrics(self) -> dict:
        """Get current metrics as a dictionary."""
        return {
            "clients": self.total_clients,
            "messages": self.total_messages,
        }

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.total_clients = 0
        self.total_messages = 0

    def get(self, key: str, default=None):
        """Get a specific metric value."""
        return self.get_metrics().get(key, default)


async def metrics_loop(state: ServerState, stop_event: asyncio.Event, interval: int) -> None:
    """Emit lightweight server metrics at a fixed cadence."""
    logger.info(f"metrics_loop starting with {interval}s interval")

    metrics = getattr(state, 'metrics', {})

    while not stop_event.is_set():
        try:
            await asyncio.sleep(interval)

            if isinstance(metrics, MetricsCollector):
                metrics_dict = metrics.get_metrics()
            else:
                metrics_dict = dict(metrics) if metrics else {}

            if "CMDCHAT_METRICS_JSON" in os.environ:
                import json
                print(json.dumps(metrics_dict), flush=True)
            else:
                clients = metrics_dict.get("clients", 0)
                messages = metrics_dict.get("messages", 0)
                logger.info(f"Metrics: clients={clients}, messages={messages}")

        except asyncio.CancelledError:
            logger.info("metrics_loop cancelled")
            break
        except Exception as e:
            logger.error(f"metrics_loop error: {e}")

    logger.info("metrics_loop exited")
