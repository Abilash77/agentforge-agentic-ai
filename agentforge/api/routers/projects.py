"""
AgentForge Projects Router.

REST endpoints for project CRUD, file listing, and download.
"""

from __future__ import annotations

import io
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from agentforge.api.auth import get_current_user_or_none
from agentforge.api.models import (
    GeneratedFileWithContent,
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectSummaryResponse,
    SuccessResponse,
)
from agentforge.api.websocket import make_progress_callback
from agentforge.database.database import get_db_session
from agentforge.database.repository import FileRepository, ProjectRepository
from agentforge.monitoring.logger import get_logger
from agentforge.workflows.task_manager import get_task_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user_or_none),
):
    """
    Create a new project and start the AgentForge pipeline asynchronously.
    Returns immediately with project ID; use WebSocket /ws/{id} to track progress.
    """
    owner_id = current_user.id if current_user else None

    # Create project record
    repo = ProjectRepository(session)
    project = await repo.create(
        name=request.name,
        idea=request.idea,
        project_type=request.project_type,
        tech_stack=request.tech_stack,
        owner_id=owner_id,
    )
    await session.commit()

    # Build WebSocket progress callback
    progress_callback = make_progress_callback(project.id)

    # Submit to task manager (runs pipeline in background)
    task_manager = get_task_manager()
    task_id = await task_manager.submit_task(
        project_id=project.id,
        idea=request.idea,
        project_type=request.project_type,
        tech_stack=request.tech_stack,
        budget_usd=request.budget_usd,
        priority=request.priority,
        progress_callback=progress_callback,
    )

    logger.info(f"Project created: {project.id} (task={task_id})")

    return ProjectSummaryResponse(
        id=project.id,
        name=project.name,
        idea=project.idea,
        project_type=project.project_type,
        tech_stack=project.tech_stack,
        status=project.status,
        current_agent=project.current_agent,
        progress_pct=project.progress_pct,
        total_tokens=project.total_tokens,
        total_cost_usd=project.total_cost_usd,
        created_at=project.created_at,
        completed_at=project.completed_at,
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user_or_none),
):
    """List all projects with pagination."""
    offset = (page - 1) * page_size
    repo = ProjectRepository(session)
    projects = await repo.list_all(limit=page_size, offset=offset)
    total = await repo.count()

    items = [
        ProjectSummaryResponse(
            id=p.id, name=p.name, idea=p.idea,
            project_type=p.project_type, tech_stack=p.tech_stack,
            status=p.status, current_agent=p.current_agent,
            progress_pct=p.progress_pct, total_tokens=p.total_tokens,
            total_cost_usd=p.total_cost_usd, created_at=p.created_at,
            completed_at=p.completed_at,
        )
        for p in projects
    ]
    return ProjectListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user_or_none),
):
    """Get full project details including agent runs and generated files."""
    repo = ProjectRepository(session)
    project = await repo.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    return ProjectDetailResponse.model_validate(project)


@router.delete("/{project_id}", response_model=SuccessResponse)
async def delete_project(
    project_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(get_current_user_or_none),
):
    """Delete a project and all its generated files."""
    repo = ProjectRepository(session)
    deleted = await repo.delete(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Also remove from ChromaDB
    try:
        from agentforge.rag.chroma_client import delete_project_documents
        delete_project_documents(project_id)
    except Exception:
        pass

    logger.info(f"Project deleted: {project_id}")
    return SuccessResponse(message=f"Project {project_id} deleted successfully")


@router.get("/{project_id}/files")
async def list_project_files(
    project_id: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
):
    """List all generated files for a project."""
    file_repo = FileRepository(session)
    files = await file_repo.list_for_project(project_id)
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "file_type": f.file_type,
            "agent_role": f.agent_role,
            "language": f.language,
            "size_bytes": f.size_bytes,
            "created_at": f.created_at.isoformat(),
        }
        for f in files
    ]


@router.get("/{project_id}/files/{filename:path}", response_model=GeneratedFileWithContent)
async def get_file_content(
    project_id: str = Path(...),
    filename: str = Path(...),
    session: AsyncSession = Depends(get_db_session),
):
    """Get the content of a specific generated file."""
    file_repo = FileRepository(session)
    file = await file_repo.get_by_filename(project_id, filename)
    if not file:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return GeneratedFileWithContent.model_validate(file)


@router.get("/{project_id}/download")
async def download_project_zip(project_id: str = Path(...)):
    """Download all generated files as a ZIP archive."""
    from agentforge.workflows.output_collector import OutputCollector
    collector = OutputCollector(project_id)
    try:
        zip_bytes = await collector.get_zip_bytes()
        if not zip_bytes:
            raise HTTPException(status_code=404, detail="No files generated yet")

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=project_{project_id}.zip"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ZIP download failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create download package")
