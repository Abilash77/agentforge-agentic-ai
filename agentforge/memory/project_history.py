"""
AgentForge Project History Tracker.

Tracks project lifecycle transitions and agent contribution summaries.
Provides a timeline view of the project's evolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from agentforge.database.database import get_session
from agentforge.database.repository import ProjectRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HistoryEvent:
    """A single project history event."""
    event_type: str           # "status_change" | "agent_start" | "agent_complete" | "file_generated"
    description: str
    agent_role: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "description": self.description,
            "agent_role": self.agent_role,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class ProjectHistory:
    """
    In-memory project history timeline with async persistence to SQLite.
    Used by the pipeline to track agent progress and build audit trails.
    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self._events: list[HistoryEvent] = []

    def record(
        self,
        event_type: str,
        description: str,
        agent_role: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> HistoryEvent:
        """Record a new history event."""
        event = HistoryEvent(
            event_type=event_type,
            description=description,
            agent_role=agent_role,
            metadata=metadata or {},
        )
        self._events.append(event)
        logger.info(f"[Project:{self.project_id}] {event_type}: {description}")
        return event

    def record_agent_start(self, agent_role: str, agent_name: str) -> HistoryEvent:
        return self.record(
            event_type="agent_start",
            description=f"{agent_name} ({agent_role}) started processing",
            agent_role=agent_role,
        )

    def record_agent_complete(
        self,
        agent_role: str,
        agent_name: str,
        files_generated: int = 0,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        duration_ms: int = 0,
    ) -> HistoryEvent:
        return self.record(
            event_type="agent_complete",
            description=f"{agent_name} ({agent_role}) completed",
            agent_role=agent_role,
            metadata={
                "files_generated": files_generated,
                "tokens_used": tokens_used,
                "cost_usd": cost_usd,
                "duration_ms": duration_ms,
            },
        )

    def record_file_generated(
        self, agent_role: str, filename: str, file_type: str
    ) -> HistoryEvent:
        return self.record(
            event_type="file_generated",
            description=f"Generated {filename} ({file_type})",
            agent_role=agent_role,
            metadata={"filename": filename, "file_type": file_type},
        )

    def record_status_change(self, from_status: str, to_status: str) -> HistoryEvent:
        return self.record(
            event_type="status_change",
            description=f"Status changed: {from_status} → {to_status}",
            metadata={"from": from_status, "to": to_status},
        )

    async def persist_status_change(self, status: str, agent_name: Optional[str] = None) -> None:
        """Persist status change to the database."""
        try:
            async with get_session() as session:
                repo = ProjectRepository(session)
                await repo.update_status(self.project_id, status, current_agent=agent_name)
        except Exception as e:
            logger.warning(f"Failed to persist status change: {e}")

    def get_timeline(self) -> list[dict]:
        """Return full event timeline as list of dicts."""
        return [e.to_dict() for e in self._events]

    def get_agent_events(self, agent_role: str) -> list[HistoryEvent]:
        """Get all events for a specific agent role."""
        return [e for e in self._events if e.agent_role == agent_role]

    def get_summary(self) -> dict:
        """Return a high-level summary of the project history."""
        agents_completed = [
            e.agent_role for e in self._events if e.event_type == "agent_complete"
        ]
        files_generated = [
            e.metadata.get("filename", "")
            for e in self._events
            if e.event_type == "file_generated"
        ]
        total_tokens = sum(
            e.metadata.get("tokens_used", 0)
            for e in self._events
            if e.event_type == "agent_complete"
        )
        total_cost = sum(
            e.metadata.get("cost_usd", 0.0)
            for e in self._events
            if e.event_type == "agent_complete"
        )
        return {
            "project_id": self.project_id,
            "total_events": len(self._events),
            "agents_completed": list(set(agents_completed)),
            "files_generated": files_generated,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "start_time": self._events[0].timestamp.isoformat() if self._events else None,
            "last_event_time": self._events[-1].timestamp.isoformat() if self._events else None,
        }

    def __len__(self) -> int:
        return len(self._events)

    def __repr__(self) -> str:
        return f"ProjectHistory(project_id={self.project_id}, events={len(self._events)})"
