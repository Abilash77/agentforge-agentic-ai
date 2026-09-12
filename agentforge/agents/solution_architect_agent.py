"""
AgentForge Solution Architect Agent.

Designs the complete technical architecture:
  - System architecture (C4 model with Mermaid diagrams)
  - Database schema (SQL DDL + ER diagram)
  - API specification (OpenAPI 3.0)
  - Technology stack recommendations
  - Architecture diagrams (Mermaid format)
"""

from __future__ import annotations

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class DesignArchitecture(Action):
    """Design system architecture with C4 model Mermaid diagrams."""

    name: str = "DesignArchitecture"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Principal Solution Architect with 15+ years of experience in distributed systems.

## Project
**Idea:** {idea}
**Type:** {project_type}
**Tech Stack:** {tech_stack}

## Requirements Summary
{requirements_summary}

{rag_context}

## Your Task
Design a comprehensive system architecture using the C4 model.

### 1. Architecture Overview
- Architectural style (microservices / monolith / serverless / event-driven)
- Key design principles applied (SOLID, DRY, CQRS, Event Sourcing, etc.)
- Scalability strategy

### 2. C4 Context Diagram (Mermaid)
```mermaid
graph TB
    %% Show the system in context with users and external systems
```

### 3. C4 Container Diagram (Mermaid)
```mermaid
graph TB
    %% Show containers (applications, data stores, microservices)
```

### 4. C4 Component Diagram (Mermaid)
```mermaid
graph TB
    %% Major components within each container
```

### 5. Data Flow Diagram (Mermaid)
```mermaid
sequenceDiagram
    %% Show key data flows between components
```

### 6. Component Descriptions
For each major component:
- Purpose and responsibilities
- Technology choice with rationale
- Interfaces (APIs it exposes)
- Dependencies

### 7. Infrastructure Architecture
- Cloud provider and services
- Containerization strategy
- Load balancing
- Caching strategy
- Message queue / event bus

### 8. Security Architecture
- Authentication/authorization model
- Network security
- Data encryption at rest and in transit
- Secret management

### 9. Scalability & High Availability
- Horizontal vs vertical scaling points
- Failover strategy
- Disaster recovery approach

Format everything as professional Markdown with valid Mermaid syntax.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            project_type=kwargs.get("project_type", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            requirements_summary=kwargs.get("requirements_summary", "")[:2000],
            rag_context=kwargs.get("rag_context", ""),
        )
        return await self._aask(prompt)


class GenerateDatabaseSchema(Action):
    """Generate complete database schema with SQL DDL and ER diagram."""

    name: str = "GenerateDatabaseSchema"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Database Architect.

## Project
{idea}

## Tech Stack
{tech_stack}

## Requirements
{requirements_summary}

## Your Task
Design a complete, production-ready database schema.

### 1. ER Diagram (Mermaid)
```mermaid
erDiagram
    %% Complete entity-relationship diagram
```

### 2. SQL DDL Script
Provide complete CREATE TABLE statements with:
- Proper data types for the chosen database
- Primary keys (UUID preferred)
- Foreign key constraints with ON DELETE/UPDATE actions
- Indexes on frequently queried columns
- Check constraints where applicable
- Comments on each table and important columns

### 3. Table Descriptions
For each table:
- Purpose
- Key columns and their semantics
- Relationships and cardinality
- Indexing strategy

### 4. Database Design Decisions
- Normalization level (3NF, BCNF) and rationale
- Denormalization choices with justification
- Partitioning strategy (if applicable)
- Archiving and retention strategy

### 5. Migration Strategy
- Initial migration file structure
- Seeding strategy for reference data

Include at least 8-10 tables appropriate for the project.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            requirements_summary=kwargs.get("requirements_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateAPISpec(Action):
    """Generate OpenAPI 3.0 specification."""

    name: str = "GenerateAPISpec"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior API Architect and Backend Engineer.

## Project
{idea}

## Tech Stack
{tech_stack}

## Architecture
{architecture_summary}

## Your Task
Generate a complete OpenAPI 3.0 specification in YAML format.

Requirements:
- At least 20 API endpoints across all major features
- RESTful design following best practices
- Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Request/response schemas with proper types
- Authentication (JWT Bearer token)
- Error response schemas
- Pagination for list endpoints
- Versioning (/api/v1/)
- Proper status codes and descriptions

The YAML must be valid and complete, starting with:
```yaml
openapi: "3.0.3"
info:
  title: "{project_name} API"
  version: "1.0.0"
  ...
```

Include all paths, components/schemas, and security definitions.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            architecture_summary=kwargs.get("architecture_summary", "")[:2000],
            project_name=kwargs.get("project_name", "Project"),
        )
        return await self._aask(prompt)


class RecommendTechStack(Action):
    """Generate detailed technology stack recommendation."""

    name: str = "RecommendTechStack"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Principal Architect and Technology Strategist.

## Project
{idea}

## Requested Stack
{tech_stack}

## Requirements
{requirements_summary}

## Your Task
Produce a comprehensive technology stack analysis and recommendation.

### 1. Recommended Stack Overview
A table comparing the chosen stack with alternatives:

| Layer | Chosen | Alternative 1 | Alternative 2 | Decision Rationale |
|-------|--------|--------------|--------------|-------------------|

### 2. Detailed Layer Analysis
For each layer (Frontend, Backend, Database, Cache, Message Queue, Search, Storage, CI/CD, Monitoring):
- Selected technology with version
- Key features utilized
- Configuration highlights
- Known limitations / watch-outs

### 3. Development Tooling
- Package managers
- Code formatters and linters
- Testing frameworks
- IDE recommendations

### 4. Infrastructure Stack
- Container orchestration
- Cloud provider services
- CDN strategy
- Monitoring and alerting stack

### 5. Third-Party Services & APIs
- Payment processing (if needed)
- Email service
- File storage
- Analytics
- Error tracking

### 6. Total Cost of Ownership Estimate
Monthly cloud cost estimate for different traffic levels (MVP / 10K users / 100K users)

Format as professional Markdown with tables and clear sections.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            requirements_summary=kwargs.get("requirements_summary", "")[:2000],
        )
        return await self._aask(prompt)


class SolutionArchitectAgent(AgentForgeRole):
    """
    Solution Architect Agent for AgentForge.

    Designs the complete technical architecture, database schema,
    API specification, and technology stack for the project.
    """

    name: str = "Victor"
    profile: str = "Solution Architect"
    goal: str = (
        "Design the complete technical architecture including system design, "
        "database schema, API specifications, and technology stack recommendations."
    )
    constraints: str = (
        "Use production-grade design patterns. Include valid Mermaid diagrams. "
        "Justify every technical decision. Design for scalability from day one."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([
            DesignArchitecture,
            GenerateDatabaseSchema,
            GenerateAPISpec,
            RecommendTechStack,
        ])

    async def run_full_design(
        self,
        idea: str,
        project_type: str,
        tech_stack: str,
        pm_outputs: dict,
    ) -> dict[str, str]:
        """Execute the full Solution Architect workflow."""
        requirements_summary = pm_outputs.get("srs", pm_outputs.get("brd", ""))[:3000]
        rag_ctx = self.get_rag_context(f"system architecture {idea} {tech_stack}")

        await self.emit_progress("design_architecture", 5, "Designing system architecture...")
        await self._start_run_tracking("DesignArchitecture")
        arch_action = DesignArchitecture(context=self.context)
        architecture = await arch_action.run(
            [],
            idea=idea,
            project_type=project_type,
            tech_stack=tech_stack,
            requirements_summary=requirements_summary,
            rag_context=rag_ctx,
        )
        await self.save_output(architecture, "ARCHITECTURE.md", OutputType.ARCHITECTURE)
        await self.emit_progress("architecture_complete", 25, "Architecture designed ✓")

        await self._start_run_tracking("GenerateDatabaseSchema")
        db_action = GenerateDatabaseSchema(context=self.context)
        db_schema = await db_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            requirements_summary=requirements_summary,
        )
        await self.save_output(db_schema, "DATABASE_SCHEMA.md", OutputType.DATABASE_SCHEMA)
        await self.emit_progress("schema_complete", 50, "Database schema generated ✓")

        await self._start_run_tracking("GenerateAPISpec")
        api_action = GenerateAPISpec(context=self.context)
        api_spec = await api_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            architecture_summary=architecture[:2000],
            project_name=idea[:50],
        )
        await self.save_output(api_spec, "openapi.yaml", OutputType.API_SPEC)
        await self.emit_progress("api_spec_complete", 75, "API specification generated ✓")

        await self._start_run_tracking("RecommendTechStack")
        stack_action = RecommendTechStack(context=self.context)
        tech_stack_doc = await stack_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            requirements_summary=requirements_summary,
        )
        await self.save_output(tech_stack_doc, "TECH_STACK.md", OutputType.TECH_STACK)
        await self.emit_progress("tech_stack_complete", 100, "Tech stack documented ✓")

        return {
            "architecture": architecture,
            "db_schema": db_schema,
            "api_spec": api_spec,
            "tech_stack_doc": tech_stack_doc,
        }
