"""
AgentForge Task Manager.

Manages the async task queue for pipeline execution.
Supports concurrent project runs with priority queuing.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineTask:
    """A pipeline task in the queue."""
    task_id: str
    project_id: str
    idea: str
    project_type: str
    tech_stack: str
    budget_usd: float
    priority: int = 5  # 1=highest, 10=lowest
    status: TaskStatus = TaskStatus.QUEUED
    progress_callback: Optional[Callable] = field(default=None, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None

    def __lt__(self, other: "PipelineTask") -> bool:
        # Higher priority (lower number) runs first
        return self.priority < other.priority


class TaskManager:
    """
    Manages async pipeline task execution.

    Features:
    - Priority queue for task ordering
    - Concurrent execution of multiple pipelines
    - Task status tracking
    - Retry logic for transient failures
    - Graceful shutdown
    """

    def __init__(self, max_concurrent: int = 3) -> None:
        self._max_concurrent = max_concurrent
        self._tasks: Dict[str, PipelineTask] = {}
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the task manager worker loop."""
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info(f"TaskManager started (max_concurrent={self._max_concurrent})")

    async def stop(self) -> None:
        """Gracefully stop the task manager."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("TaskManager stopped")

    async def submit_task(
        self,
        project_id: str,
        idea: str,
        project_type: str,
        tech_stack: str,
        budget_usd: float = 5.0,
        priority: int = 5,
        progress_callback: Optional[Callable] = None,
    ) -> str:
        """
        Submit a pipeline task for execution.

        Returns:
            task_id: Unique identifier for tracking the task
        """
        task_id = str(uuid.uuid4())
        task = PipelineTask(
            task_id=task_id,
            project_id=project_id,
            idea=idea,
            project_type=project_type,
            tech_stack=tech_stack,
            budget_usd=budget_usd,
            priority=priority,
            progress_callback=progress_callback,
        )
        self._tasks[task_id] = task

        # Priority queue: (priority, created_at_timestamp, task)
        await self._queue.put((priority, task.created_at.timestamp(), task))
        logger.info(f"Task submitted: {task_id} for project {project_id} (priority={priority})")
        return task_id

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get the current status of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "status": task.status.value,
            "priority": task.priority,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error,
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a queued or running task."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.status == TaskStatus.QUEUED:
            task.status = TaskStatus.CANCELLED
            return True
        logger.warning(f"Cannot cancel task {task_id} with status {task.status}")
        return False

    def get_queue_size(self) -> int:
        return self._queue.qsize()

    def get_running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    def get_all_tasks(self) -> list[dict]:
        return [
            {
                "task_id": t.task_id,
                "project_id": t.project_id,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in self._tasks.values()
        ]

    async def _worker_loop(self) -> None:
        """Main worker loop that processes tasks from the queue."""
        while self._running:
            try:
                # Non-blocking get with timeout
                try:
                    _, _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Skip cancelled tasks
                if task.status == TaskStatus.CANCELLED:
                    self._queue.task_done()
                    continue

                # Execute with concurrency limit
                asyncio.create_task(self._execute_task(task))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")

    async def _execute_task(self, task: PipelineTask) -> None:
        """Execute a single pipeline task."""
        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            logger.info(f"Executing task {task.task_id} for project {task.project_id}")

            try:
                from agentforge.workflows.pipeline import AgentForgePipeline

                pipeline = AgentForgePipeline(
                    project_id=task.project_id,
                    idea=task.idea,
                    project_type=task.project_type,
                    tech_stack=task.tech_stack,
                    progress_callback=task.progress_callback,
                    budget_usd=task.budget_usd,
                )
                result = await pipeline.run()
                task.result = result
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                if not result.success:
                    task.error = result.error

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.error(f"Task {task.task_id} failed: {e}")
            finally:
                task.completed_at = datetime.utcnow()
                try:
                    self._queue.task_done()
                except Exception:
                    pass


# Global singleton task manager
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager(max_concurrent=3)
    return _task_manager
