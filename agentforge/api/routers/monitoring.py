"""AgentForge Monitoring Router"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from agentforge.database.database import get_db_session
from agentforge.database.models import AgentRun, Project, ProjectMetric
from agentforge.database.repository import MetricsRepository

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/costs")
async def get_cost_analytics(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
):
    """Get cost breakdown per project."""
    result = await session.execute(
        select(Project).order_by(desc(Project.total_cost_usd)).limit(limit)
    )
    projects = result.scalars().all()
    return [
        {
            "project_id": p.id,
            "project_name": p.name,
            "total_cost_usd": round(p.total_cost_usd, 4),
            "total_tokens": p.total_tokens,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in projects
    ]


@router.get("/performance")
async def get_performance_analytics(session: AsyncSession = Depends(get_db_session)):
    """Get agent performance analytics."""
    result = await session.execute(
        select(AgentRun).where(AgentRun.status == "completed")
        .order_by(desc(AgentRun.created_at)).limit(200)
    )
    runs = result.scalars().all()

    # Aggregate by agent role
    by_role: dict = {}
    for run in runs:
        role = run.agent_role
        if role not in by_role:
            by_role[role] = {"total_tokens": 0, "total_cost": 0.0, "count": 0, "total_duration_ms": 0}
        by_role[role]["total_tokens"] += run.total_tokens
        by_role[role]["total_cost"] += run.cost_usd
        by_role[role]["count"] += 1
        by_role[role]["total_duration_ms"] += run.duration_ms or 0

    analytics = []
    for role, data in by_role.items():
        count = max(data["count"], 1)
        analytics.append({
            "agent_role": role,
            "run_count": data["count"],
            "avg_tokens": data["total_tokens"] // count,
            "avg_cost_usd": round(data["total_cost"] / count, 4),
            "avg_duration_ms": data["total_duration_ms"] // count,
            "total_cost_usd": round(data["total_cost"], 4),
        })

    return {"agents": analytics, "total_runs": len(runs)}


@router.get("/projects/{project_id}/metrics")
async def get_project_metrics(project_id: str, session: AsyncSession = Depends(get_db_session)):
    """Get all metrics for a specific project."""
    result = await session.execute(
        select(ProjectMetric).where(ProjectMetric.project_id == project_id)
        .order_by(ProjectMetric.recorded_at)
    )
    metrics = result.scalars().all()
    return [
        {
            "metric_name": m.metric_name,
            "value": m.metric_value,
            "agent_role": m.agent_role,
            "recorded_at": m.recorded_at.isoformat(),
        }
        for m in metrics
    ]


@router.get("/summary")
async def get_monitoring_summary(session: AsyncSession = Depends(get_db_session)):
    """Get platform monitoring summary."""
    repo = MetricsRepository(session)
    return await repo.get_platform_summary()
