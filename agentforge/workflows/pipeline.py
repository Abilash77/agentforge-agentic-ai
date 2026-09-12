"""
AgentForge Pipeline Orchestrator.

The master orchestrator that coordinates all 7 agents in sequence.
Manages state, tracks progress, handles failures, and collects outputs.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Callable, Optional

from agentforge.agents import (
    DeveloperAgent,
    DevOpsAgent,
    DocumentationAgent,
    PPTAgent,
    ProductManagerAgent,
    QAAgent,
    SolutionArchitectAgent,
)
from agentforge.constants import (
    AgentRole,
    PIPELINE_ORDER,
    WS_EVENT_AGENT_COMPLETE,
    WS_EVENT_AGENT_START,
    WS_EVENT_PIPELINE_COMPLETE,
)
from agentforge.database.database import get_session
from agentforge.database.repository import ProjectRepository
from agentforge.memory.project_history import ProjectHistory
from agentforge.monitoring.cost_tracker import CostTracker
from agentforge.monitoring.logger import get_logger
from agentforge.monitoring.metrics import MetricsCollector
from agentforge.workflows.output_collector import OutputCollector

logger = get_logger(__name__)


class PipelineResult:
    """Aggregated result of the entire AgentForge pipeline execution."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self.success = False
        self.error: Optional[str] = None
        self.outputs: dict[str, dict] = {}
        self.total_files_generated: int = 0
        self.total_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.duration_seconds: float = 0.0
        self.zip_path: Optional[str] = None
        self.completed_at: Optional[datetime] = None

    def add_agent_output(self, agent_role: AgentRole, output: dict) -> None:
        self.outputs[agent_role.value] = output

    def to_summary(self) -> dict:
        return {
            "project_id": self.project_id,
            "success": self.success,
            "error": self.error,
            "agents_completed": list(self.outputs.keys()),
            "total_files_generated": self.total_files_generated,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "duration_seconds": round(self.duration_seconds, 2),
            "zip_path": self.zip_path,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AgentForgePipeline:
    """
    Master orchestrator for the AgentForge multi-agent pipeline.

    Executes 7 specialized agents in sequence, passing outputs
    from each agent to the next. Manages:
    - Agent initialization with project context
    - Progress broadcasting via WebSocket
    - Error handling and partial recovery
    - Output aggregation and ZIP packaging
    - SQLite state persistence
    """

    def __init__(
        self,
        project_id: str,
        idea: str,
        project_type: str,
        tech_stack: str,
        progress_callback: Optional[Callable] = None,
        budget_usd: float = 5.0,
    ) -> None:
        self.project_id = project_id
        self.idea = idea
        self.project_type = project_type
        self.tech_stack = tech_stack
        self.progress_callback = progress_callback
        self.budget_usd = budget_usd
        self._history = ProjectHistory(project_id)
        self._cost_tracker = CostTracker(project_id)
        self._metrics = MetricsCollector(project_id)
        self._output_collector = OutputCollector(project_id)
        self._result = PipelineResult(project_id)

    async def _emit(self, event: str, agent_role: str, message: str, pct: int = 0) -> None:
        """Broadcast a WebSocket event."""
        if self.progress_callback:
            try:
                await self.progress_callback({
                    "event": event,
                    "agent_role": agent_role,
                    "message": message,
                    "percentage": pct,
                    "project_id": self.project_id,
                })
            except Exception:
                pass

    async def _update_project_status(self, status: str, agent: Optional[str] = None, pct: Optional[int] = None) -> None:
        """Update project status in SQLite."""
        try:
            async with get_session() as session:
                repo = ProjectRepository(session)
                await repo.update_status(
                    project_id=self.project_id,
                    status=status,
                    current_agent=agent,
                    progress_pct=pct,
                )
        except Exception as e:
            logger.warning(f"Failed to update project status: {e}")

    def _init_agent(self, agent: Any, agent_role: AgentRole) -> Any:
        """Initialize an agent with AgentForge context."""
        agent.initialize_agentforge(
            project_id=self.project_id,
            agent_role=agent_role,
            history=self._history,
            progress_callback=self.progress_callback,
        )
        return agent

    async def run(self) -> PipelineResult:
        """
        Execute the full 7-agent pipeline.

        Returns PipelineResult with aggregated outputs and statistics.
        """
        start_time = asyncio.get_event_loop().time()
        logger.info(f"🚀 AgentForge pipeline starting for project {self.project_id}")
        logger.info(f"   Idea: {self.idea}")
        logger.info(f"   Type: {self.project_type} | Stack: {self.tech_stack}")

        # Update status to in_progress
        await self._update_project_status("in_progress", pct=0)
        self._history.record_status_change("pending", "in_progress")

        pm_outputs: dict = {}
        arch_outputs: dict = {}
        dev_outputs: dict = {}
        qa_outputs: dict = {}
        doc_outputs: dict = {}
        devops_outputs: dict = {}
        ppt_outputs: dict = {}

        # ── Agent 1: Product Manager ─────────────────────────────────────────
        try:
            await self._emit(WS_EVENT_AGENT_START, "product_manager", "Product Manager starting...", 5)
            await self._update_project_status("agent_running", "product_manager", 5)
            self._history.record_agent_start("product_manager", "Alexandra")

            pm_agent = self._init_agent(ProductManagerAgent(), AgentRole.PRODUCT_MANAGER)
            pm_outputs = await pm_agent.run_full_analysis(
                idea=self.idea,
                project_type=self.project_type,
                tech_stack=self.tech_stack,
            )
            self._result.add_agent_output(AgentRole.PRODUCT_MANAGER, pm_outputs)
            self._history.record_agent_complete(
                "product_manager", "Alexandra",
                files_generated=pm_agent._files_generated,
                tokens_used=pm_agent._total_input_tokens + pm_agent._total_output_tokens,
                cost_usd=pm_agent._total_cost_usd,
            )
            await self._emit(WS_EVENT_AGENT_COMPLETE, "product_manager", "Product Manager complete ✓", 14)
            await self._update_project_status("agent_running", "product_manager", 14)
            logger.info("✓ Product Manager Agent complete")

        except Exception as e:
            logger.error(f"Product Manager Agent failed: {e}")
            self._result.error = f"ProductManager failed: {e}"
            await self._finalize(start_time, failed=True)
            return self._result

        # ── Agent 2: Solution Architect ──────────────────────────────────────
        try:
            await self._emit(WS_EVENT_AGENT_START, "solution_architect", "Solution Architect starting...", 15)
            await self._update_project_status("agent_running", "solution_architect", 15)
            self._history.record_agent_start("solution_architect", "Victor")

            arch_agent = self._init_agent(SolutionArchitectAgent(), AgentRole.SOLUTION_ARCHITECT)
            arch_outputs = await arch_agent.run_full_design(
                idea=self.idea,
                project_type=self.project_type,
                tech_stack=self.tech_stack,
                pm_outputs=pm_outputs,
            )
            self._result.add_agent_output(AgentRole.SOLUTION_ARCHITECT, arch_outputs)
            self._history.record_agent_complete(
                "solution_architect", "Victor",
                files_generated=arch_agent._files_generated,
            )
            await self._emit(WS_EVENT_AGENT_COMPLETE, "solution_architect", "Solution Architect complete ✓", 28)
            await self._update_project_status("agent_running", "solution_architect", 28)
            logger.info("✓ Solution Architect Agent complete")

        except Exception as e:
            logger.error(f"Solution Architect Agent failed: {e}")
            # Continue — subsequent agents can work without architecture docs

        # ── Agent 3: Developer ───────────────────────────────────────────────
        try:
            await self._emit(WS_EVENT_AGENT_START, "developer", "Developer starting...", 29)
            await self._update_project_status("agent_running", "developer", 29)
            self._history.record_agent_start("developer", "Marcus")

            dev_agent = self._init_agent(DeveloperAgent(), AgentRole.DEVELOPER)
            dev_outputs = await dev_agent.run_full_development(
                idea=self.idea,
                project_type=self.project_type,
                tech_stack=self.tech_stack,
                arch_outputs=arch_outputs,
                pm_outputs=pm_outputs,
            )
            self._result.add_agent_output(AgentRole.DEVELOPER, dev_outputs)
            self._history.record_agent_complete("developer", "Marcus", files_generated=dev_agent._files_generated)
            await self._emit(WS_EVENT_AGENT_COMPLETE, "developer", "Developer complete ✓", 50)
            await self._update_project_status("agent_running", "developer", 50)
            logger.info("✓ Developer Agent complete")

        except Exception as e:
            logger.error(f"Developer Agent failed: {e}")

        # ── Agents 4-7 run concurrently (independent of each other) ──────────
        async def run_qa():
            try:
                await self._emit(WS_EVENT_AGENT_START, "qa_engineer", "QA Engineer starting...", 52)
                self._history.record_agent_start("qa_engineer", "Priya")
                agent = self._init_agent(QAAgent(), AgentRole.QA_ENGINEER)
                result = await agent.run_full_qa(
                    idea=self.idea,
                    tech_stack=self.tech_stack,
                    pm_outputs=pm_outputs,
                    arch_outputs=arch_outputs,
                    dev_outputs=dev_outputs,
                )
                self._result.add_agent_output(AgentRole.QA_ENGINEER, result)
                self._history.record_agent_complete("qa_engineer", "Priya", files_generated=agent._files_generated)
                await self._emit(WS_EVENT_AGENT_COMPLETE, "qa_engineer", "QA Engineer complete ✓", 65)
                logger.info("✓ QA Agent complete")
            except Exception as e:
                logger.error(f"QA Agent failed: {e}")

        async def run_docs():
            try:
                await self._emit(WS_EVENT_AGENT_START, "documentation", "Documentation Agent starting...", 52)
                self._history.record_agent_start("documentation", "Sophie")
                agent = self._init_agent(DocumentationAgent(), AgentRole.DOCUMENTATION)
                result = await agent.run_full_documentation(
                    idea=self.idea,
                    tech_stack=self.tech_stack,
                    pm_outputs=pm_outputs,
                    arch_outputs=arch_outputs,
                    dev_outputs=dev_outputs,
                )
                self._result.add_agent_output(AgentRole.DOCUMENTATION, result)
                self._history.record_agent_complete("documentation", "Sophie", files_generated=agent._files_generated)
                await self._emit(WS_EVENT_AGENT_COMPLETE, "documentation", "Documentation complete ✓", 65)
                logger.info("✓ Documentation Agent complete")
            except Exception as e:
                logger.error(f"Documentation Agent failed: {e}")

        async def run_ppt():
            try:
                await self._emit(WS_EVENT_AGENT_START, "ppt", "PPT Agent starting...", 52)
                self._history.record_agent_start("ppt", "Isabella")
                agent = self._init_agent(PPTAgent(), AgentRole.PPT)
                result = await agent.run_full_presentations(
                    idea=self.idea,
                    tech_stack=self.tech_stack,
                    pm_outputs=pm_outputs,
                    arch_outputs=arch_outputs,
                )
                self._result.add_agent_output(AgentRole.PPT, result)
                self._history.record_agent_complete("ppt", "Isabella", files_generated=agent._files_generated)
                await self._emit(WS_EVENT_AGENT_COMPLETE, "ppt", "Presentations complete ✓", 65)
                logger.info("✓ PPT Agent complete")
            except Exception as e:
                logger.error(f"PPT Agent failed: {e}")

        # Run QA, Docs, PPT concurrently
        await asyncio.gather(run_qa(), run_docs(), run_ppt(), return_exceptions=True)
        await self._update_project_status("agent_running", "devops", 75)

        # ── Agent 7: DevOps (depends on developer output) ────────────────────
        try:
            await self._emit(WS_EVENT_AGENT_START, "devops", "DevOps Agent starting...", 76)
            self._history.record_agent_start("devops", "Jordan")
            devops_agent = self._init_agent(DevOpsAgent(), AgentRole.DEVOPS)
            devops_outputs = await devops_agent.run_full_devops(
                idea=self.idea,
                tech_stack=self.tech_stack,
                arch_outputs=arch_outputs,
                dev_outputs=dev_outputs,
            )
            self._result.add_agent_output(AgentRole.DEVOPS, devops_outputs)
            self._history.record_agent_complete("devops", "Jordan", files_generated=devops_agent._files_generated)
            await self._emit(WS_EVENT_AGENT_COMPLETE, "devops", "DevOps complete ✓", 90)
            logger.info("✓ DevOps Agent complete")
        except Exception as e:
            logger.error(f"DevOps Agent failed: {e}")

        # ── Finalization ─────────────────────────────────────────────────────
        await self._finalize(start_time, failed=False)
        return self._result

    async def _finalize(self, start_time: float, failed: bool) -> None:
        """Finalize the pipeline run."""
        end_time = asyncio.get_event_loop().time()
        self._result.duration_seconds = end_time - start_time
        self._result.completed_at = datetime.utcnow()

        if not failed:
            # Package all outputs into ZIP
            try:
                zip_path = await self._output_collector.create_zip_package()
                self._result.zip_path = zip_path
            except Exception as e:
                logger.warning(f"ZIP packaging failed: {e}")

            self._result.success = True
            await self._update_project_status("completed", pct=100)
            self._history.record_status_change("in_progress", "completed")
            await self._emit(
                WS_EVENT_PIPELINE_COMPLETE,
                "pipeline",
                f"🎉 All agents completed! {self._result.total_files_generated} files generated.",
                100,
            )
            logger.info(
                f"🎉 Pipeline complete for project {self.project_id} | "
                f"Duration: {self._result.duration_seconds:.1f}s | "
                f"Cost: ${self._result.total_cost_usd:.4f}"
            )
        else:
            await self._update_project_status("failed")
            self._history.record_status_change("in_progress", "failed")
            await self._emit("pipeline_failed", "pipeline", f"Pipeline failed: {self._result.error}", 0)

        # Record final metrics
        summary = self._history.get_summary()
        await self._metrics.record_pipeline_completion(
            duration_seconds=self._result.duration_seconds,
            total_tokens=summary.get("total_tokens", 0),
            total_cost_usd=summary.get("total_cost_usd", 0.0),
            agents_completed=len(summary.get("agents_completed", [])),
            files_generated=len(summary.get("files_generated", [])),
        )
