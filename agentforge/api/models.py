"""
AgentForge FastAPI – Pydantic API Models.

Request/response schemas for all API endpoints.
Separate from SQLAlchemy ORM models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserLoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str
    role: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Projects ────────────────────────────────────────────────────────────────

class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    idea: str = Field(..., min_length=10, max_length=5000)
    project_type: str = Field(default="full_stack")
    tech_stack: str = Field(default="fastapi_react")
    budget_usd: float = Field(default=5.0, ge=0.5, le=50.0)
    priority: int = Field(default=5, ge=1, le=10)

    @field_validator("project_type")
    @classmethod
    def validate_project_type(cls, v: str) -> str:
        valid = {
            "web_app", "mobile_app", "api_service", "cli_tool",
            "data_pipeline", "ml_model", "microservice", "full_stack",
            "saas_platform", "ecommerce"
        }
        if v not in valid:
            raise ValueError(f"project_type must be one of {valid}")
        return v

class ProjectSummaryResponse(BaseModel):
    id: str
    name: str
    idea: str
    project_type: str
    tech_stack: str
    status: str
    current_agent: Optional[str] = None
    progress_pct: int
    total_tokens: int
    total_cost_usd: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ProjectDetailResponse(ProjectSummaryResponse):
    description: Optional[str] = None
    error_message: Optional[str] = None
    agent_runs: List["AgentRunResponse"] = []
    generated_files: List["GeneratedFileResponse"] = []
    status_history: List["StatusHistoryResponse"] = []

class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    agent_role: str
    action_name: str
    status: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    duration_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class GeneratedFileResponse(BaseModel):
    id: str
    agent_role: str
    filename: str
    file_type: str
    language: Optional[str] = None
    size_bytes: int
    version: int
    created_at: datetime

    model_config = {"from_attributes": True}

class GeneratedFileWithContent(GeneratedFileResponse):
    content: str

class StatusHistoryResponse(BaseModel):
    from_status: str
    to_status: str
    reason: Optional[str] = None
    agent_name: Optional[str] = None
    transitioned_at: datetime

    model_config = {"from_attributes": True}

class ProjectListResponse(BaseModel):
    items: List[ProjectSummaryResponse]
    total: int
    page: int
    page_size: int


# ─── Agents ──────────────────────────────────────────────────────────────────

class AgentStatusResponse(BaseModel):
    agent_role: str
    agent_name: str
    status: str  # idle | running | completed | failed
    current_action: Optional[str] = None
    progress_pct: int = 0

class AgentMetricsResponse(BaseModel):
    agent_role: str
    run_count: int
    total_tokens: int
    total_cost_usd: float
    avg_duration_ms: float

class PlatformMetricsResponse(BaseModel):
    total_projects: int
    completed_projects: int
    total_tokens_used: int
    total_cost_usd: float
    active_runs: int
    queue_size: int


# ─── Monitoring ──────────────────────────────────────────────────────────────

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    agent_name: Optional[str] = None
    project_id: Optional[str] = None
    module: Optional[str] = None

class MonitoringLogsResponse(BaseModel):
    logs: List[LogEntry]
    total: int
    page: int

class CostBreakdownResponse(BaseModel):
    project_id: str
    project_name: str
    total_cost_usd: float
    total_tokens: int
    cost_by_agent: Dict[str, float]
    created_at: datetime

class PerformanceResponse(BaseModel):
    agent_metrics: List[AgentMetricsResponse]
    platform_metrics: PlatformMetricsResponse


# ─── WebSocket ───────────────────────────────────────────────────────────────

class WSProgressEvent(BaseModel):
    event: str
    agent_role: Optional[str] = None
    agent: Optional[str] = None
    step: Optional[str] = None
    percentage: int = 0
    message: str = ""
    project_id: str
    timestamp: Optional[str] = None


# ─── Common ──────────────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[Any] = None


# Allow forward references
ProjectDetailResponse.model_rebuild()
