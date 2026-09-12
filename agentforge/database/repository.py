"""
AgentForge Database Repository Layer.

Repository pattern — abstracts all database operations.
Each repository handles CRUD for a specific domain model.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agentforge.database.models import (
    AgentRun,
    ConversationMessage,
    GeneratedFile,
    Project,
    ProjectMetric,
    ProjectStatusHistory,
    SystemMetric,
    User,
)


class UserRepository:
    """CRUD operations for User model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, email: str, hashed_password: str, role: str = "user") -> User:
        user = User(username=username, email=email, hashed_password=hashed_password, role=role)
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[User]:
        result = await self._session.execute(select(User).order_by(desc(User.created_at)))
        return list(result.scalars().all())


class ProjectRepository:
    """CRUD operations for Project model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        name: str,
        idea: str,
        project_type: str,
        tech_stack: str,
        owner_id: Optional[str] = None,
    ) -> Project:
        project = Project(
            name=name,
            idea=idea,
            project_type=project_type,
            tech_stack=tech_stack,
            owner_id=owner_id,
        )
        self._session.add(project)
        await self._session.flush()
        return project

    async def get_by_id(self, project_id: str) -> Optional[Project]:
        result = await self._session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Project]:
        result = await self._session.execute(
            select(Project).order_by(desc(Project.created_at)).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_owner(self, owner_id: str) -> list[Project]:
        result = await self._session.execute(
            select(Project).where(Project.owner_id == owner_id).order_by(desc(Project.created_at))
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        project_id: str,
        status: str,
        current_agent: Optional[str] = None,
        progress_pct: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Project]:
        project = await self.get_by_id(project_id)
        if not project:
            return None
        old_status = project.status
        project.status = status
        if current_agent is not None:
            project.current_agent = current_agent
        if progress_pct is not None:
            project.progress_pct = progress_pct
        if error_message is not None:
            project.error_message = error_message
        if status == "completed":
            project.completed_at = datetime.utcnow()
            project.progress_pct = 100
        # Record status transition
        history = ProjectStatusHistory(
            project_id=project_id,
            from_status=old_status,
            to_status=status,
            agent_name=current_agent,
        )
        self._session.add(history)
        await self._session.flush()
        return project

    async def update_costs(self, project_id: str, tokens: int, cost_usd: float) -> None:
        project = await self.get_by_id(project_id)
        if project:
            project.total_tokens += tokens
            project.total_cost_usd += cost_usd
            await self._session.flush()

    async def delete(self, project_id: str) -> bool:
        project = await self.get_by_id(project_id)
        if not project:
            return False
        await self._session.delete(project)
        await self._session.flush()
        return True

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Project))
        return result.scalar_one()

    async def count_by_status(self, status: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Project).where(Project.status == status)
        )
        return result.scalar_one()


class AgentRunRepository:
    """CRUD operations for AgentRun model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        project_id: str,
        agent_name: str,
        agent_role: str,
        action_name: str,
    ) -> AgentRun:
        run = AgentRun(
            project_id=project_id,
            agent_name=agent_name,
            agent_role=agent_role,
            action_name=action_name,
            status="running",
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def complete(
        self,
        run_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AgentRun]:
        result = await self._session.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            return None
        run.status = "failed" if error_message else "completed"
        run.input_tokens = input_tokens
        run.output_tokens = output_tokens
        run.total_tokens = input_tokens + output_tokens
        run.cost_usd = cost_usd
        run.duration_ms = duration_ms
        run.error_message = error_message
        run.completed_at = datetime.utcnow()
        await self._session.flush()
        return run

    async def list_for_project(self, project_id: str) -> list[AgentRun]:
        result = await self._session.execute(
            select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at)
        )
        return list(result.scalars().all())

    async def get_agent_stats(self, agent_role: str) -> dict:
        """Aggregate stats for a specific agent role across all projects."""
        result = await self._session.execute(
            select(
                func.count(AgentRun.id).label("run_count"),
                func.sum(AgentRun.total_tokens).label("total_tokens"),
                func.sum(AgentRun.cost_usd).label("total_cost"),
                func.avg(AgentRun.duration_ms).label("avg_duration_ms"),
            ).where(AgentRun.agent_role == agent_role, AgentRun.status == "completed")
        )
        row = result.one()
        return {
            "agent_role": agent_role,
            "run_count": row.run_count or 0,
            "total_tokens": row.total_tokens or 0,
            "total_cost_usd": float(row.total_cost or 0),
            "avg_duration_ms": float(row.avg_duration_ms or 0),
        }


class FileRepository:
    """CRUD operations for GeneratedFile model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        project_id: str,
        agent_role: str,
        filename: str,
        file_type: str,
        content: str,
        language: Optional[str] = None,
    ) -> GeneratedFile:
        file = GeneratedFile(
            project_id=project_id,
            agent_role=agent_role,
            filename=filename,
            file_type=file_type,
            content=content,
            language=language,
            size_bytes=len(content.encode("utf-8")),
        )
        self._session.add(file)
        await self._session.flush()
        return file

    async def list_for_project(self, project_id: str) -> list[GeneratedFile]:
        result = await self._session.execute(
            select(GeneratedFile)
            .where(GeneratedFile.project_id == project_id)
            .order_by(GeneratedFile.agent_role, GeneratedFile.filename)
        )
        return list(result.scalars().all())

    async def get_by_filename(self, project_id: str, filename: str) -> Optional[GeneratedFile]:
        result = await self._session.execute(
            select(GeneratedFile).where(
                GeneratedFile.project_id == project_id,
                GeneratedFile.filename == filename,
            )
        )
        return result.scalar_one_or_none()


class ConversationRepository:
    """CRUD operations for ConversationMessage model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_message(
        self,
        project_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None,
        agent_role: Optional[str] = None,
        cause_by: Optional[str] = None,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            project_id=project_id,
            role=role,
            content=content,
            agent_name=agent_name,
            agent_role=agent_role,
            cause_by=cause_by,
        )
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def list_for_project(self, project_id: str, limit: int = 100) -> list[ConversationMessage]:
        result = await self._session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.project_id == project_id)
            .order_by(ConversationMessage.timestamp)
            .limit(limit)
        )
        return list(result.scalars().all())


class MetricsRepository:
    """Metrics storage and aggregation."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_project_metric(
        self,
        project_id: str,
        metric_name: str,
        value: float,
        agent_role: Optional[str] = None,
    ) -> ProjectMetric:
        metric = ProjectMetric(
            project_id=project_id,
            metric_name=metric_name,
            metric_value=value,
            agent_role=agent_role,
        )
        self._session.add(metric)
        await self._session.flush()
        return metric

    async def record_system_metric(self, metric_name: str, value: float, tags: Optional[dict] = None) -> SystemMetric:
        metric = SystemMetric(metric_name=metric_name, metric_value=value, tags=tags)
        self._session.add(metric)
        await self._session.flush()
        return metric

    async def get_platform_summary(self) -> dict:
        """Get platform-wide aggregate statistics."""
        total_projects = await self._session.execute(select(func.count()).select_from(Project))
        total_tokens = await self._session.execute(select(func.sum(Project.total_tokens)).select_from(Project))
        total_cost = await self._session.execute(select(func.sum(Project.total_cost_usd)).select_from(Project))
        completed = await self._session.execute(
            select(func.count()).select_from(Project).where(Project.status == "completed")
        )
        return {
            "total_projects": total_projects.scalar_one() or 0,
            "completed_projects": completed.scalar_one() or 0,
            "total_tokens_used": total_tokens.scalar_one() or 0,
            "total_cost_usd": float(total_cost.scalar_one() or 0),
        }
