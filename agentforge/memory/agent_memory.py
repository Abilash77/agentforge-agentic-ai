"""
AgentForge Agent Long-Term Memory.

Per-agent memory store that persists decisions, context, and outputs
across project runs. Enables agents to learn from past projects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from agentforge.database.database import get_session
from agentforge.database.repository import ConversationRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentMemoryEntry:
    """A single agent memory record."""
    agent_role: str
    project_id: str
    memory_type: str  # "decision" | "context" | "output" | "observation"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "agent_role": self.agent_role,
            "project_id": self.project_id,
            "memory_type": self.memory_type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentMemoryEntry":
        return cls(
            agent_role=data["agent_role"],
            project_id=data["project_id"],
            memory_type=data["memory_type"],
            content=data["content"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


class AgentMemory:
    """
    Long-term memory store for a specific agent instance.

    Stores and retrieves the agent's decisions and observations
    across multiple project runs, enabling context-aware behavior.
    """

    def __init__(self, agent_role: str, agent_name: str) -> None:
        self.agent_role = agent_role
        self.agent_name = agent_name
        self._entries: list[AgentMemoryEntry] = []
        self._current_project_id: Optional[str] = None

    def set_project(self, project_id: str) -> None:
        """Bind this memory to a project context."""
        self._current_project_id = project_id

    def remember(
        self,
        content: str,
        memory_type: str = "observation",
        metadata: Optional[dict] = None,
    ) -> AgentMemoryEntry:
        """Store a new memory entry."""
        entry = AgentMemoryEntry(
            agent_role=self.agent_role,
            project_id=self._current_project_id or "global",
            memory_type=memory_type,
            content=content,
            metadata=metadata or {},
        )
        self._entries.append(entry)
        logger.debug(f"[{self.agent_name}] Remembered: {memory_type} — {content[:80]}...")
        return entry

    def recall(
        self,
        memory_type: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[AgentMemoryEntry]:
        """Retrieve memory entries filtered by type and/or project."""
        entries = self._entries
        if memory_type:
            entries = [e for e in entries if e.memory_type == memory_type]
        if project_id:
            entries = [e for e in entries if e.project_id == project_id]
        return entries[-limit:]

    def recall_decisions(self, limit: int = 5) -> list[str]:
        """Get recent decision summaries as plain strings."""
        decisions = self.recall(memory_type="decision", limit=limit)
        return [d.content for d in decisions]

    def recall_context_for_prompt(self) -> str:
        """Build a context string to inject into the next LLM prompt."""
        recent = self.recall(limit=5)
        if not recent:
            return ""
        lines = ["## Agent Long-Term Memory Context"]
        for entry in recent:
            lines.append(f"- [{entry.memory_type.upper()}] {entry.content[:200]}")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps([e.to_dict() for e in self._entries], indent=2)

    @classmethod
    def from_json(cls, agent_role: str, agent_name: str, data: str) -> "AgentMemory":
        memory = cls(agent_role=agent_role, agent_name=agent_name)
        entries = json.loads(data)
        memory._entries = [AgentMemoryEntry.from_dict(e) for e in entries]
        return memory

    def clear_project_memory(self, project_id: str) -> None:
        """Remove all entries for a specific project."""
        self._entries = [e for e in self._entries if e.project_id != project_id]

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"AgentMemory(role={self.agent_role}, entries={len(self._entries)})"
