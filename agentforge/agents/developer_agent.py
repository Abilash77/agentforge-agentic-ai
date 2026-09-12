"""
AgentForge Developer Agent.

Generates complete, production-ready source code:
  - Annotated folder structure
  - Backend (FastAPI/Django/Express)
  - Frontend (React/Vue/Next.js)
  - REST APIs
  - Component integration
"""

from __future__ import annotations

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class GenerateFolderStructure(Action):
    name: str = "GenerateFolderStructure"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Software Engineer and Tech Lead.

## Project: {idea}
## Tech Stack: {tech_stack}
## Architecture: {architecture_summary}

Generate a complete, annotated folder structure for this project.

Requirements:
- Production-grade structure following industry standards
- Include ALL directories and key files
- Annotate each file/folder with its purpose
- Include configuration files (eslint, prettier, jest, pytest, etc.)
- Include environment files (.env.example)
- Include Docker files

Format as a tree structure with comments:
```
project-name/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app factory
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── routes/
...
```

After the tree, provide a brief description of each major directory's purpose.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            architecture_summary=kwargs.get("architecture_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateBackendCode(Action):
    name: str = "GenerateBackendCode"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Backend Engineer. Generate production-ready backend code.

## Project: {idea}
## Tech Stack: {tech_stack}
## Database Schema: {db_schema}
## API Specification: {api_spec}

Generate complete backend code. Include the following files:

### 1. main.py / app.py — Application entry point
- App factory with all middleware
- CORS, authentication, rate limiting
- Startup/shutdown events
- Exception handlers

### 2. Models (ORM)
- All database models from the schema
- Relationships and validators
- Proper typing

### 3. Schemas (Pydantic/Validation)
- Request/response schemas for all endpoints
- Input validation with detailed error messages

### 4. Repositories / Services
- Data access layer
- Business logic layer
- Separation of concerns

### 5. API Routes
- All endpoints from the OpenAPI spec
- Proper error handling
- Authentication decorators
- Response models

### 6. Authentication
- JWT token generation and validation
- Password hashing
- Middleware

### 7. Configuration
- Settings management from environment variables
- Database connection setup

### 8. Utils / Helpers
- Common utility functions
- Custom exceptions

For each file, start with a clear comment header:
```
# === filename.py ===
# [description]
```

Write REAL, COMPLETE, WORKING code. No placeholders or TODO comments.
Use proper type hints throughout.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            db_schema=kwargs.get("db_schema", "")[:2000],
            api_spec=kwargs.get("api_spec", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateFrontendCode(Action):
    name: str = "GenerateFrontendCode"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Frontend Engineer. Generate production-ready frontend code.

## Project: {idea}
## Tech Stack: {tech_stack}
## API Endpoints: {api_summary}

Generate complete frontend code. Include:

### 1. App Entry Point
- Router setup
- Global state management
- Theme/styling setup

### 2. Layout Components
- Main layout with navigation
- Sidebar component
- Header/footer

### 3. Page Components (minimum 5 pages)
For each page:
- Complete JSX/TSX with hooks
- API integration
- Loading/error states
- Form validation

### 4. Reusable UI Components
- Data table with sorting/filtering/pagination
- Form components with validation
- Modal/dialog components
- Toast notifications
- Loading skeletons

### 5. API Client / Services
- Axios/Fetch wrapper with interceptors
- Authentication handling (JWT refresh)
- Error handling
- TypeScript interfaces matching API schemas

### 6. State Management
- Store definitions
- Actions/reducers or composables
- Auth state handling

### 7. Styling
- CSS modules or styled-components
- Responsive design
- Dark/light theme support

For each file, start with:
```
// === ComponentName.tsx ===
```

Write REAL, COMPLETE code. Modern patterns. TypeScript preferred.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            api_summary=kwargs.get("api_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateAPIs(Action):
    name: str = "GenerateAPIs"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Backend Engineer specializing in API design and implementation.

## Project: {idea}
## OpenAPI Spec Summary: {api_spec_summary}
## Tech Stack: {tech_stack}

Generate complete, working API implementations for all endpoints.

For each endpoint group, provide:
1. Route file with all endpoints implemented
2. Request/response type definitions
3. Input validation
4. Business logic
5. Error handling with proper HTTP status codes
6. Authentication/authorization guards
7. API tests (basic happy-path examples)

Organize by domain:
- Auth APIs (register, login, refresh, logout)
- User APIs (CRUD)
- Core domain APIs (main features)
- Admin APIs

Each endpoint must:
- Handle all edge cases
- Return consistent error responses
- Include logging
- Have proper response typing

Write complete, production-ready code.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            api_spec_summary=kwargs.get("api_spec_summary", "")[:3000],
            tech_stack=kwargs.get("tech_stack", ""),
        )
        return await self._aask(prompt)


class DeveloperAgent(AgentForgeRole):
    """
    Developer Agent for AgentForge.

    Generates production-ready source code including backend,
    frontend, APIs, and folder structure.
    """

    name: str = "Marcus"
    profile: str = "Senior Software Engineer"
    goal: str = (
        "Generate complete, production-ready source code including backend APIs, "
        "frontend components, database models, and project structure."
    )
    constraints: str = (
        "Write real, working code. No placeholders. "
        "Use type hints. Follow SOLID principles. "
        "Include error handling in every function."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([
            GenerateFolderStructure,
            GenerateBackendCode,
            GenerateFrontendCode,
            GenerateAPIs,
        ])

    async def run_full_development(
        self,
        idea: str,
        project_type: str,
        tech_stack: str,
        arch_outputs: dict,
        pm_outputs: dict,
    ) -> dict[str, str]:
        """Execute the full Developer workflow."""
        architecture = arch_outputs.get("architecture", "")
        db_schema = arch_outputs.get("db_schema", "")
        api_spec = arch_outputs.get("api_spec", "")

        rag_ctx = self.get_rag_context(f"source code implementation {idea}")

        await self.emit_progress("folder_structure", 5, "Generating folder structure...")
        await self._start_run_tracking("GenerateFolderStructure")
        folder_action = GenerateFolderStructure(context=self.context)
        folder_structure = await folder_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            architecture_summary=architecture[:2000],
        )
        await self.save_output(folder_structure, "FOLDER_STRUCTURE.md", OutputType.FOLDER_STRUCTURE)
        await self.emit_progress("folder_complete", 20, "Folder structure ✓")

        await self._start_run_tracking("GenerateBackendCode")
        backend_action = GenerateBackendCode(context=self.context)
        backend_code = await backend_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            db_schema=db_schema,
            api_spec=api_spec,
        )
        await self.save_output(backend_code, "backend_code.md", OutputType.SOURCE_CODE, language="python")
        await self.emit_progress("backend_complete", 55, "Backend code generated ✓")

        await self._start_run_tracking("GenerateFrontendCode")
        frontend_action = GenerateFrontendCode(context=self.context)
        frontend_code = await frontend_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            api_summary=api_spec[:2000],
        )
        await self.save_output(frontend_code, "frontend_code.md", OutputType.SOURCE_CODE, language="typescript")
        await self.emit_progress("frontend_complete", 80, "Frontend code generated ✓")

        await self._start_run_tracking("GenerateAPIs")
        api_action = GenerateAPIs(context=self.context)
        api_code = await api_action.run(
            [],
            idea=idea,
            api_spec_summary=api_spec,
            tech_stack=tech_stack,
        )
        await self.save_output(api_code, "api_implementations.md", OutputType.SOURCE_CODE)
        await self.emit_progress("apis_complete", 100, "APIs implemented ✓")

        return {
            "folder_structure": folder_structure,
            "backend_code": backend_code,
            "frontend_code": frontend_code,
            "api_code": api_code,
        }
