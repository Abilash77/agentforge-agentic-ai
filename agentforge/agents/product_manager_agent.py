"""
AgentForge Product Manager Agent.

Analyzes user requirements and generates:
  - Business Requirements Document (BRD)
  - Software Requirements Specification (SRS)
  - Risk Matrix with mitigation strategies
  - Project Milestones and timeline
"""

from __future__ import annotations

from typing import ClassVar, Optional

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


# ─── Actions ────────────────────────────────────────────────────────────────

class AnalyzeRequirements(Action):
    """Analyze user requirements and produce a structured Business Requirements Document."""

    name: str = "AnalyzeRequirements"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Product Manager at a top-tier software company.

## Project Idea
{idea}

## Project Type
{project_type}

## Technology Stack
{tech_stack}

{rag_context}

## Your Task
Create a comprehensive Business Requirements Document (BRD) that includes:

1. **Executive Summary** — 2-3 sentence overview of the project
2. **Business Objectives** — 3-5 clear, measurable business goals
3. **Target Users & Personas** — Define 2-3 user personas with demographics, goals, and pain points
4. **Functional Requirements** — At least 15 detailed functional requirements with priority (HIGH/MED/LOW)
5. **Non-Functional Requirements** — Performance, scalability, security, reliability requirements
6. **User Stories** — At least 10 user stories in "As a [user], I want [goal], so that [benefit]" format
7. **Acceptance Criteria** — For each user story above
8. **Business Rules** — Domain-specific constraints and rules
9. **Assumptions & Dependencies** — List key assumptions and external dependencies
10. **Out of Scope** — Explicitly state what is NOT included in this version

Format the output in clean Markdown with proper headings and tables where appropriate.
Be specific, detailed, and production-grade. Avoid vague requirements.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        idea = kwargs.get("idea", "")
        project_type = kwargs.get("project_type", "full_stack")
        tech_stack = kwargs.get("tech_stack", "fastapi_react")
        rag_context = kwargs.get("rag_context", "")

        prompt = self.PROMPT_TEMPLATE.format(
            idea=idea,
            project_type=project_type,
            tech_stack=tech_stack,
            rag_context=f"## Relevant Context\n{rag_context}" if rag_context else "",
        )
        response = await self._aask(prompt)
        return response


class GenerateSRS(Action):
    """Generate IEEE-style Software Requirements Specification."""

    name: str = "GenerateSRS"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Product Manager and Systems Analyst.

## Project Idea
{idea}

## Business Requirements
{brd_content}

{rag_context}

## Your Task
Create a detailed Software Requirements Specification (SRS) document following IEEE 830 standard.

Include the following sections:
1. **Introduction** — Purpose, scope, definitions, acronyms, overview
2. **Overall Description**
   - Product perspective and system context
   - Product functions summary
   - User characteristics
   - Constraints and assumptions
3. **Specific Requirements**
   - External Interface Requirements (UI, hardware, software, communications)
   - System Features (detailed, numbered)
   - Database Requirements
   - Design Constraints
4. **System Architecture Overview** — High-level description of major components
5. **Data Model** — Key entities and relationships in plain English
6. **API Overview** — Major API endpoints (high-level, not implementation)
7. **Security Requirements** — Authentication, authorization, data protection
8. **Performance Requirements** — Response times, throughput, capacity
9. **Quality Attributes** — Maintainability, testability, portability

Format as professional Markdown with numbered requirements (e.g., SRS-001, SRS-002).
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        idea = kwargs.get("idea", "")
        brd_content = kwargs.get("brd_content", "No BRD provided")
        rag_context = kwargs.get("rag_context", "")

        prompt = self.PROMPT_TEMPLATE.format(
            idea=idea,
            brd_content=brd_content[:3000],  # Truncate to avoid token overflow
            rag_context=f"## Context\n{rag_context}" if rag_context else "",
        )
        response = await self._aask(prompt)
        return response


class IdentifyRisks(Action):
    """Identify project risks and create a risk matrix with mitigation strategies."""

    name: str = "IdentifyRisks"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Product Manager and Risk Analyst.

## Project
{idea}

## Technology Stack
{tech_stack}

## Your Task
Create a comprehensive Risk Matrix for this project.

For each risk, provide:
| Risk ID | Category | Description | Probability (H/M/L) | Impact (H/M/L) | Risk Score | Mitigation Strategy | Owner | Status |
|---------|----------|-------------|---------------------|----------------|------------|---------------------|-------|--------|

Categories to cover:
1. **Technical Risks** — Architecture, scalability, integration issues
2. **Security Risks** — Data breaches, authentication vulnerabilities
3. **Operational Risks** — Deployment, monitoring, SLA
4. **Business Risks** — Market fit, competition, pivots
5. **Resource Risks** — Team, budget, timeline
6. **Compliance Risks** — GDPR, CCPA, industry regulations
7. **Third-party Risks** — API dependencies, vendor lock-in

Identify at least 15 risks total.
After the table, provide a **Risk Summary** with:
- Top 3 critical risks requiring immediate attention
- Risk appetite statement
- Risk monitoring plan

Format as Markdown with proper tables.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        idea = kwargs.get("idea", "")
        tech_stack = kwargs.get("tech_stack", "")
        prompt = self.PROMPT_TEMPLATE.format(idea=idea, tech_stack=tech_stack)
        return await self._aask(prompt)


class DefineMilestones(Action):
    """Define project milestones and delivery timeline."""

    name: str = "DefineMilestones"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Product Manager and Project Planner.

## Project
{idea}

## Requirements Summary
{requirements_summary}

## Your Task
Create a detailed project milestone plan for this software project.

Provide:
1. **Project Timeline Overview** — Total estimated duration and phases
2. **Milestone Table** — For each milestone:
   | Milestone | Phase | Deliverables | Start Week | End Week | Dependencies | Success Criteria |
   |-----------|-------|--------------|------------|----------|--------------|------------------|

3. **Phase Breakdown** — For each phase (Discovery, Design, Development, Testing, Launch):
   - Objectives
   - Key activities
   - Deliverables
   - Definition of Done

4. **Sprint Plan** (2-week sprints) — First 3 sprints with:
   - Sprint goal
   - User stories included
   - Acceptance criteria

5. **Critical Path** — Identify the critical path and potential bottlenecks

6. **MVP Definition** — What constitutes the Minimum Viable Product and timeline

Format as professional Markdown with tables and clear hierarchy.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        idea = kwargs.get("idea", "")
        requirements_summary = kwargs.get("requirements_summary", "")
        prompt = self.PROMPT_TEMPLATE.format(
            idea=idea,
            requirements_summary=requirements_summary[:2000],
        )
        return await self._aask(prompt)


# ─── Agent ──────────────────────────────────────────────────────────────────

class ProductManagerAgent(AgentForgeRole):
    """
    Product Manager Agent for AgentForge.

    Responsible for requirements analysis, BRD/SRS generation,
    risk identification, and milestone planning.
    """

    name: str = "Alexandra"
    profile: str = "Product Manager"
    goal: str = (
        "Analyze user requirements and produce comprehensive product documentation "
        "including BRD, SRS, risk matrix, and project milestones."
    )
    constraints: str = (
        "Be thorough, specific, and production-grade. "
        "Never produce vague or generic requirements. "
        "Always tie requirements back to user needs and business value."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([AnalyzeRequirements, GenerateSRS, IdentifyRisks, DefineMilestones])

    async def run_full_analysis(
        self,
        idea: str,
        project_type: str,
        tech_stack: str,
    ) -> dict[str, str]:
        """
        Execute the full Product Manager workflow for a project.

        Returns dict with keys: brd, srs, risks, milestones
        """
        await self.emit_progress("analyze_requirements", 5, "Analyzing requirements...")
        await self._start_run_tracking("AnalyzeRequirements")

        # Get RAG context
        rag_ctx = self.get_rag_context(f"requirements analysis {idea}")

        # 1. BRD
        brd_action = AnalyzeRequirements(context=self.context)
        brd = await brd_action.run(
            [], idea=idea, project_type=project_type, tech_stack=tech_stack, rag_context=rag_ctx
        )
        await self.save_output(brd, "BRD.md", OutputType.BRD, language="markdown")
        self.remember(f"Generated BRD for: {idea}", memory_type="output")
        await self.emit_progress("brd_complete", 25, "BRD generated ✓")

        # 2. SRS
        await self._start_run_tracking("GenerateSRS")
        srs_action = GenerateSRS(context=self.context)
        srs = await srs_action.run([], idea=idea, brd_content=brd, rag_context=rag_ctx)
        await self.save_output(srs, "SRS.md", OutputType.SRS, language="markdown")
        await self.emit_progress("srs_complete", 50, "SRS generated ✓")

        # 3. Risk Matrix
        await self._start_run_tracking("IdentifyRisks")
        risk_action = IdentifyRisks(context=self.context)
        risks = await risk_action.run([], idea=idea, tech_stack=tech_stack)
        await self.save_output(risks, "RISK_MATRIX.md", OutputType.RISK_MATRIX, language="markdown")
        await self.emit_progress("risks_complete", 75, "Risk matrix generated ✓")

        # 4. Milestones
        await self._start_run_tracking("DefineMilestones")
        milestone_action = DefineMilestones(context=self.context)
        milestones = await milestone_action.run(
            [], idea=idea, requirements_summary=srs[:2000]
        )
        await self.save_output(milestones, "MILESTONES.md", OutputType.MILESTONES, language="markdown")
        await self.emit_progress("milestones_complete", 100, "Milestones defined ✓")

        logger.info(f"ProductManagerAgent completed for project {self._project_id}")
        return {"brd": brd, "srs": srs, "risks": risks, "milestones": milestones}
