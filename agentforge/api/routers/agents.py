"""AgentForge Agents Router"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agentforge.api.models import AgentMetricsResponse, PlatformMetricsResponse
from agentforge.database.database import get_db_session
from agentforge.database.repository import AgentRunRepository, MetricsRepository
from agentforge.constants import AgentRole
from agentforge.workflows.task_manager import get_task_manager

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("/status")
async def get_agents_status():
    """Get current status of all agents and the task queue."""
    task_manager = get_task_manager()
    return {
        "queue_size": task_manager.get_queue_size(),
        "running_count": task_manager.get_running_count(),
        "tasks": task_manager.get_all_tasks(),
    }


@router.get("/metrics", response_model=list[AgentMetricsResponse])
async def get_agent_metrics(session: AsyncSession = Depends(get_db_session)):
    """Get aggregate performance metrics for each agent role."""
    repo = AgentRunRepository(session)
    metrics = []
    for role in AgentRole:
        stats = await repo.get_agent_stats(role.value)
        metrics.append(AgentMetricsResponse(
            agent_role=stats["agent_role"],
            run_count=stats["run_count"],
            total_tokens=stats["total_tokens"],
            total_cost_usd=stats["total_cost_usd"],
            avg_duration_ms=stats["avg_duration_ms"],
        ))
    return metrics


@router.get("/platform", response_model=PlatformMetricsResponse)
async def get_platform_metrics(session: AsyncSession = Depends(get_db_session)):
    """Get platform-wide aggregate metrics."""
    repo = MetricsRepository(session)
    summary = await repo.get_platform_summary()
    task_manager = get_task_manager()
    return PlatformMetricsResponse(
        total_projects=summary["total_projects"],
        completed_projects=summary["completed_projects"],
        total_tokens_used=summary["total_tokens_used"],
        total_cost_usd=summary["total_cost_usd"],
        active_runs=task_manager.get_running_count(),
        queue_size=task_manager.get_queue_size(),
    )
