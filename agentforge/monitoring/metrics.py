"""
AgentForge Metrics Collector.

In-memory + SQLite metrics store.
Tracks platform-wide and per-project performance analytics.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from agentforge.database.database import get_session
from agentforge.database.repository import MetricsRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentMetricEntry:
    """Snapshot of metrics for one agent execution."""
    agent_role: str
    project_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    files_generated: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class MetricsCollector:
    """
    Per-project metrics collector.

    Stores agent performance data in SQLite and provides
    analytics queries for the monitoring dashboard.
    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self._entries: list[AgentMetricEntry] = []
        self._pipeline_start: Optional[float] = None

    def start_pipeline(self) -> None:
        self._pipeline_start = time.time()

    async def record_agent_metrics(
        self,
        agent_role: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        duration_ms: int,
        files_generated: int = 0,
    ) -> None:
        entry = AgentMetricEntry(
            agent_role=agent_role,
            project_id=self.project_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            files_generated=files_generated,
        )
        self._entries.append(entry)

        # Persist to SQLite
        try:
            async with get_session() as session:
                repo = MetricsRepository(session)
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name=f"{agent_role}.total_tokens",
                    value=entry.total_tokens,
                    agent_role=agent_role,
                )
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name=f"{agent_role}.cost_usd",
                    value=cost_usd,
                    agent_role=agent_role,
                )
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name=f"{agent_role}.duration_ms",
                    value=duration_ms,
                    agent_role=agent_role,
                )
        except Exception as e:
            logger.warning(f"Failed to persist metrics: {e}")

    async def record_pipeline_completion(
        self,
        duration_seconds: float,
        total_tokens: int,
        total_cost_usd: float,
        agents_completed: int,
        files_generated: int,
    ) -> None:
        try:
            async with get_session() as session:
                repo = MetricsRepository(session)
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name="pipeline.duration_seconds",
                    value=duration_seconds,
                )
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name="pipeline.total_tokens",
                    value=total_tokens,
                )
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name="pipeline.total_cost_usd",
                    value=total_cost_usd,
                )
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name="pipeline.agents_completed",
                    value=agents_completed,
                )
                await repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name="pipeline.files_generated",
                    value=files_generated,
                )
                # System-wide metric
                await repo.record_system_metric(
                    metric_name="platform.pipeline_completed",
                    value=1.0,
                    tags={"project_id": self.project_id},
                )
        except Exception as e:
            logger.warning(f"Failed to persist pipeline completion metrics: {e}")

    def get_summary(self) -> dict:
        """Return aggregated metrics summary."""
        if not self._entries:
            return {"project_id": self.project_id, "agents": {}}

        agents = {}
        for entry in self._entries:
            agents[entry.agent_role] = {
                "total_tokens": entry.total_tokens,
                "cost_usd": round(entry.cost_usd, 4),
                "duration_ms": entry.duration_ms,
                "files_generated": entry.files_generated,
            }

        total_tokens = sum(e.total_tokens for e in self._entries)
        total_cost = sum(e.cost_usd for e in self._entries)
        total_files = sum(e.files_generated for e in self._entries)

        return {
            "project_id": self.project_id,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "total_files_generated": total_files,
            "agents": agents,
        }
