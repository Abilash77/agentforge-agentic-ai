"""
AgentForge SQLite-Backed Persistent Memory.

Extends MetaGPT's in-memory Memory class with SQLite persistence.
Messages survive process restarts and can be retrieved across sessions.
"""

from __future__ import annotations

import asyncio
from typing import Optional

from metagpt.memory import Memory
from metagpt.schema import Message

from agentforge.database.database import get_session
from agentforge.database.repository import ConversationRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class SQLiteMemory(Memory):
    """
    Persistent memory that stores MetaGPT Message objects in SQLite.

    Drop-in replacement for metagpt.memory.Memory with persistence.
    In-memory list is kept for fast access; SQLite is the source of truth.
    """

    def __init__(self, project_id: str, agent_name: str, agent_role: str) -> None:
        super().__init__()
        self.project_id = project_id
        self.agent_name = agent_name
        self.agent_role = agent_role
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        """Lazy-load conversation history from SQLite on first access."""
        if self._loaded:
            return
        try:
            async with get_session() as session:
                repo = ConversationRepository(session)
                messages = await repo.list_for_project(self.project_id, limit=200)
                for msg in messages:
                    # Reconstruct MetaGPT Message objects from DB records
                    m = Message(
                        content=msg.content,
                        role=msg.role,
                        cause_by=msg.cause_by or "",
                    )
                    # Add to in-memory list without re-persisting
                    if m not in self.storage:
                        self.storage.append(m)
            self._loaded = True
            logger.debug(
                f"Loaded {len(self.storage)} messages from SQLite for project={self.project_id} agent={self.agent_name}"
            )
        except Exception as e:
            logger.warning(f"Could not load memory from SQLite: {e}")
            self._loaded = True  # Don't retry on every call

    def add(self, message: Message) -> None:
        """Add message to in-memory store and persist to SQLite."""
        super().add(message)
        # Fire-and-forget async persist
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._persist_message(message))
            else:
                loop.run_until_complete(self._persist_message(message))
        except RuntimeError:
            pass  # No event loop — in sync context, skip persistence

    async def _persist_message(self, message: Message) -> None:
        """Persist a single message to SQLite."""
        try:
            async with get_session() as session:
                repo = ConversationRepository(session)
                await repo.add_message(
                    project_id=self.project_id,
                    role=message.role or "assistant",
                    content=message.content,
                    agent_name=self.agent_name,
                    agent_role=self.agent_role,
                    cause_by=str(message.cause_by) if message.cause_by else None,
                )
        except Exception as e:
            logger.warning(f"Failed to persist message to SQLite: {e}")

    def get(self, k: int = 0) -> list[Message]:
        """Get the most recent k messages (0 = all)."""
        return super().get(k=k)

    def clear(self) -> None:
        """Clear in-memory storage (does NOT delete from SQLite)."""
        super().clear()
        self._loaded = False
