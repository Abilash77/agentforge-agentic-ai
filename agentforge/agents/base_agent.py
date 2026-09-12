"""
AgentForge Base Agent.

Abstract base class that all 7 specialized agents inherit from.
Extends MetaGPT's Role with:
  - Auto-logging of every action to SQLite
  - Token usage tracking
  - RAG context injection
  - WebSocket progress broadcasting
  - Persistent file output saving
  - Long-term memory support
"""

from __future__ import annotations

import asyncio
import time
from abc import abstractmethod
from typing import Any, Callable, Optional

from metagpt.roles import Role
from metagpt.schema import Message

from agentforge.constants import AgentRole, OutputType, WS_EVENT_AGENT_PROGRESS
from agentforge.database.database import get_session
from agentforge.database.repository import (
    AgentRunRepository,
    ConversationRepository,
    FileRepository,
    MetricsRepository,
    ProjectRepository,
)
from agentforge.memory.agent_memory import AgentMemory
from agentforge.memory.project_history import ProjectHistory
from agentforge.monitoring.logger import AgentLogger
from agentforge.rag.context_injector import ContextInjector
from agentforge.rag.document_indexer import DocumentIndexer


class AgentForgeRole(Role):
    """
    Extended MetaGPT Role with AgentForge production capabilities.

    All 7 specialized agents inherit from this class.
    MetaGPT's core ReAct loop is preserved and extended.
    """

    # AgentForge-specific fields (not Pydantic model fields to avoid conflict)
    _project_id: Optional[str] = None
    _agent_role_enum: Optional[AgentRole] = None
    _history: Optional[ProjectHistory] = None
    _agent_memory: Optional[AgentMemory] = None
    _progress_callback: Optional[Callable] = None
    _current_run_id: Optional[str] = None
    _run_start_time: Optional[float] = None
    _total_input_tokens: int = 0
    _total_output_tokens: int = 0
    _total_cost_usd: float = 0.0
    _files_generated: int = 0

    def initialize_agentforge(
        self,
        project_id: str,
        agent_role: AgentRole,
        history: ProjectHistory,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """
        Initialize AgentForge capabilities for a project run.
        Called by the pipeline before each agent executes.

        Args:
            project_id: The project this agent is working on
            agent_role: This agent's role enum value
            history: Shared project history tracker
            progress_callback: Async callback to broadcast WebSocket events
        """
        self._project_id = project_id
        self._agent_role_enum = agent_role
        self._history = history
        self._progress_callback = progress_callback
        self._agent_memory = AgentMemory(
            agent_role=agent_role.value,
            agent_name=self.name,
        )
        self._agent_memory.set_project(project_id)
        self._af_logger = AgentLogger(
            agent_name=self.name,
            agent_role=agent_role.value,
            project_id=project_id,
        )
        self._context_injector = ContextInjector()
        self._document_indexer = DocumentIndexer()
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._files_generated = 0
        
        # Sync AgentForge LLM config to MetaGPT config
        from agentforge.config import get_config
        from metagpt.config2 import config as mg_config
        from metagpt.configs.llm_config import LLMConfig, LLMType
        
        cfg = get_config()
        llm_type_map = {
            "openai": LLMType.OPENAI,
            "ollama": LLMType.OLLAMA,
            "anthropic": LLMType.ANTHROPIC,
            "gemini": LLMType.GEMINI,
        }
        
        if mg_config.llm is None:
            mg_config.llm = LLMConfig()
            
        mg_config.llm.api_type = llm_type_map.get(cfg.llm.api_type.lower(), LLMType.OPENAI)
        mg_config.llm.model = cfg.llm.model
        if cfg.llm.api_key:
            mg_config.llm.api_key = cfg.llm.api_key
        if cfg.llm.base_url:
            mg_config.llm.base_url = cfg.llm.base_url

    async def emit_progress(
        self,
        step: str,
        percentage: int,
        message: str = "",
        event_type: str = WS_EVENT_AGENT_PROGRESS,
    ) -> None:
        """Broadcast progress update via WebSocket callback."""
        if self._progress_callback:
            try:
                payload = {
                    "event": event_type,
                    "agent": self.name,
                    "agent_role": self._agent_role_enum.value if self._agent_role_enum else "",
                    "step": step,
                    "percentage": percentage,
                    "message": message,
                    "project_id": self._project_id,
                }
                await self._progress_callback(payload)
            except Exception:
                pass  # Never fail due to WebSocket errors

    async def save_output(
        self,
        content: str,
        filename: str,
        file_type: OutputType,
        language: Optional[str] = None,
        index_in_rag: bool = True,
    ) -> None:
        """
        Persist generated file to SQLite and optionally index in ChromaDB.

        Args:
            content: File content
            filename: Target filename
            file_type: Type of output (from OutputType enum)
            language: Programming language (optional)
            index_in_rag: Whether to index this document in ChromaDB
        """
        if not self._project_id or not content:
            return

        # Save to SQLite
        try:
            async with get_session() as session:
                repo = FileRepository(session)
                await repo.create(
                    project_id=self._project_id,
                    agent_role=self._agent_role_enum.value if self._agent_role_enum else "unknown",
                    filename=filename,
                    file_type=file_type.value,
                    content=content,
                    language=language,
                )
            self._files_generated += 1
        except Exception as e:
            self._af_logger.error(f"Failed to save output {filename}: {e}")

        # Index in ChromaDB
        if index_in_rag:
            try:
                self._document_indexer.index_document(
                    project_id=self._project_id,
                    agent_role=self._agent_role_enum.value if self._agent_role_enum else "unknown",
                    filename=filename,
                    content=content,
                    output_type=file_type,
                )
            except Exception as e:
                self._af_logger.warning(f"RAG indexing failed for {filename}: {e}")

        # Record in project history
        if self._history:
            self._history.record_file_generated(
                agent_role=self._agent_role_enum.value if self._agent_role_enum else "unknown",
                filename=filename,
                file_type=file_type.value,
            )

    async def _start_run_tracking(self, action_name: str) -> None:
        """Create an AgentRun record in SQLite."""
        if not self._project_id:
            return
        self._run_start_time = time.time()
        try:
            async with get_session() as session:
                repo = AgentRunRepository(session)
                run = await repo.create(
                    project_id=self._project_id,
                    agent_name=self.name,
                    agent_role=self._agent_role_enum.value if self._agent_role_enum else "unknown",
                    action_name=action_name,
                )
                self._current_run_id = run.id
        except Exception as e:
            self._af_logger.warning(f"Failed to start run tracking: {e}")

    async def _complete_run_tracking(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        error: Optional[Exception] = None,
    ) -> None:
        """Complete the AgentRun record with final stats."""
        if not self._current_run_id or not self._project_id:
            return

        duration_ms = int((time.time() - self._run_start_time) * 1000) if self._run_start_time else None

        # Accumulate totals
        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost_usd += cost_usd

        try:
            async with get_session() as session:
                run_repo = AgentRunRepository(session)
                await run_repo.complete(
                    run_id=self._current_run_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    duration_ms=duration_ms,
                    error_message=str(error) if error else None,
                )
                # Update project cost totals
                proj_repo = ProjectRepository(session)
                await proj_repo.update_costs(
                    project_id=self._project_id,
                    tokens=input_tokens + output_tokens,
                    cost_usd=cost_usd,
                )
        except Exception as e:
            self._af_logger.warning(f"Failed to complete run tracking: {e}")

    def get_rag_context(self, task_description: str) -> str:
        """Get RAG context for the current task."""
        if not self._project_id or not self._agent_role_enum:
            return ""
        return self._context_injector.get_context_for_agent(
            agent_role=self._agent_role_enum.value,
            project_id=self._project_id,
            task_description=task_description,
        )

    def remember(self, content: str, memory_type: str = "observation") -> None:
        """Store a long-term memory entry."""
        if self._agent_memory:
            self._agent_memory.remember(content, memory_type=memory_type)

    def recall_decisions(self, limit: int = 3) -> list[str]:
        """Retrieve recent decisions from long-term memory."""
        if self._agent_memory:
            return self._agent_memory.recall_decisions(limit=limit)
        return []

    @property
    def agent_stats(self) -> dict:
        """Return aggregate stats for this agent's current run."""
        return {
            "agent_name": self.name,
            "agent_role": self._agent_role_enum.value if self._agent_role_enum else "unknown",
            "project_id": self._project_id,
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self._total_input_tokens + self._total_output_tokens,
            "total_cost_usd": self._total_cost_usd,
            "files_generated": self._files_generated,
        }
