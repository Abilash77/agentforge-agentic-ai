"""
AgentForge Documentation Agent.

Generates comprehensive project documentation:
  - README with badges and examples
  - Setup and installation guide
  - API reference documentation
  - Deployment guide
"""

from __future__ import annotations

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class GenerateREADME(Action):
    name: str = "GenerateREADME"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Technical Writer and Developer Advocate.

## Project: {idea}
## Tech Stack: {tech_stack}
## Project Summary: {project_summary}

Create a world-class README.md for this project.

Include ALL of these sections:

# [Project Name]

> [One-line tagline]

![License](badge) ![Version](badge) ![Build](badge) ![Coverage](badge) ![Docker](badge)

## ✨ Features
[Feature list with emoji icons]

## 📸 Screenshots / Demo
[Placeholder for screenshots with descriptions]

## 🏗️ Architecture
[Brief architecture overview with Mermaid diagram]

## 🚀 Quick Start

### Prerequisites
[List with versions]

### Installation
```bash
[Step-by-step commands]
```

### Configuration
```bash
[Environment setup]
```

### Running Locally
```bash
[Dev server commands]
```

## 📚 API Documentation
[Overview with key endpoints and Swagger link]

## 🐳 Docker
```bash
[Docker commands]
```

## 🧪 Testing
```bash
[Test commands with coverage]
```

## 📦 Project Structure
[Folder tree with annotations]

## 🔐 Environment Variables
[Table: Variable | Description | Default | Required]

## 🤝 Contributing
[Contribution guide]

## 📄 License
[License text]

## 👥 Authors
[Author section]

Make it visually rich with emoji, tables, and code blocks. Production GitHub quality.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            project_summary=kwargs.get("project_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateSetupGuide(Action):
    name: str = "GenerateSetupGuide"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior DevOps Engineer and Technical Writer.

## Project: {idea}
## Tech Stack: {tech_stack}
## Infrastructure: {infrastructure_summary}

Generate a comprehensive Setup and Installation Guide.

## Sections:
1. **Prerequisites** — Exact versions of all required tools
2. **Development Environment Setup**
   - OS-specific instructions (Windows / macOS / Linux)
   - IDE setup (VSCode with recommended extensions)
   - Tool installation steps
3. **Repository Setup**
   - Clone, branch strategy
   - Git hooks setup
4. **Backend Setup**
   - Virtual environment / dependency installation
   - Database setup and migrations
   - Environment variable configuration
5. **Frontend Setup**
   - Node.js / package installation
   - Build configuration
6. **Docker Development Setup**
   - docker-compose for local development
   - Hot-reload configuration
7. **Database Setup**
   - Initial migration
   - Seeding test data
8. **Running the Application**
   - Start all services
   - Verify all is working
   - Useful development commands
9. **Troubleshooting**
   - Common issues and solutions
   - Debug mode setup
   - Log locations

Provide exact, copy-paste commands. Include OS-specific variations.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            infrastructure_summary=kwargs.get("infrastructure_summary", ""),
        )
        return await self._aask(prompt)


class GenerateAPIDocs(Action):
    name: str = "GenerateAPIDocs"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Technical Writer specializing in API documentation.

## Project: {idea}
## OpenAPI Spec: {api_spec}

Generate comprehensive API reference documentation.

Format as Markdown with the following structure:

# API Reference

## Authentication
- How to obtain tokens
- How to use tokens in requests
- Token refresh flow

## Base URL
```
Production: https://api.yourapp.com/v1
Development: http://localhost:8001/api/v1
```

## Response Format
[Standard success and error response formats with examples]

## Endpoints

For EACH endpoint, provide:
### [HTTP METHOD] /endpoint/path
**Description:** What this endpoint does

**Authentication:** Required / Optional / None

**Request:**
```json
{
  "field": "type - description",
  ...
}
```

**Response:**
```json
{
  "field": "type - description",
  ...
}
```

**Error Responses:**
| Status | Code | Description |
|--------|------|-------------|

**Example (curl):**
```bash
curl -X GET ...
```

## Rate Limiting
[Rate limit policy and headers]

## Pagination
[Pagination format and parameters]

## Webhooks (if applicable)
[Webhook documentation]

## SDK / Client Libraries
[Links to SDKs]

Be thorough and include real JSON examples for every endpoint.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            api_spec=kwargs.get("api_spec", "")[:3000],
        )
        return await self._aask(prompt)


class GenerateDeploymentGuide(Action):
    name: str = "GenerateDeploymentGuide"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior DevOps Engineer and Site Reliability Engineer.

## Project: {idea}
## Tech Stack: {tech_stack}
## Infrastructure: {infrastructure_summary}

Generate a comprehensive Deployment Guide covering all environments.

## Sections:

### 1. Deployment Overview
- Deployment strategy (Blue-Green / Rolling / Canary)
- Environment matrix (dev / staging / production)

### 2. Docker Deployment
```bash
# Step-by-step Docker deployment commands
```

### 3. AWS Deployment (EC2 + RDS + S3)
- Infrastructure setup
- EC2 configuration
- RDS setup
- S3 bucket configuration
- CloudFront CDN
- Route 53 DNS

### 4. GCP Deployment (Cloud Run + Cloud SQL)
- Step-by-step GCP deployment

### 5. Azure Deployment (App Service + Azure SQL)
- Step-by-step Azure deployment

### 6. Kubernetes Deployment
```bash
# kubectl commands
```
- Apply all manifests
- Configure secrets and configmaps
- Set up ingress
- Horizontal Pod Autoscaling

### 7. CI/CD Pipeline Setup
- GitHub Actions / GitLab CI setup
- Environment secrets configuration
- Deployment triggers

### 8. Database Migrations in Production
- Zero-downtime migration strategy
- Rollback procedures

### 9. SSL/TLS Configuration
- Let's Encrypt setup
- Certificate renewal

### 10. Monitoring Setup
- Application monitoring (Prometheus + Grafana)
- Log aggregation (ELK stack)
- Alerting rules

### 11. Backup and Disaster Recovery
- Backup schedule and retention
- Recovery procedures
- RTO/RPO targets

### 12. Scaling Guide
- When and how to scale
- Load testing before scaling
- Cost optimization tips

Include exact commands that can be copy-pasted.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            infrastructure_summary=kwargs.get("infrastructure_summary", "")[:2000],
        )
        return await self._aask(prompt)


class DocumentationAgent(AgentForgeRole):
    """
    Documentation Agent for AgentForge.

    Generates README, setup guide, API reference, and deployment guide.
    """

    name: str = "Sophie"
    profile: str = "Technical Writer"
    goal: str = (
        "Create comprehensive, production-grade documentation that enables "
        "developers to understand, set up, and deploy the generated project."
    )
    constraints: str = (
        "Be thorough and specific. Include exact commands. "
        "Write for an audience of senior developers. "
        "Make documentation actionable, not just descriptive."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([
            GenerateREADME,
            GenerateSetupGuide,
            GenerateAPIDocs,
            GenerateDeploymentGuide,
        ])

    async def run_full_documentation(
        self,
        idea: str,
        tech_stack: str,
        pm_outputs: dict,
        arch_outputs: dict,
        dev_outputs: dict,
    ) -> dict[str, str]:
        """Execute the full Documentation workflow."""
        brd = pm_outputs.get("brd", "")
        api_spec = arch_outputs.get("api_spec", "")
        architecture = arch_outputs.get("architecture", "")

        await self.emit_progress("readme", 10, "Writing README...")
        await self._start_run_tracking("GenerateREADME")
        readme_action = GenerateREADME(context=self.context)
        readme = await readme_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            project_summary=brd[:2000],
        )
        await self.save_output(readme, "README.md", OutputType.README, language="markdown")
        await self.emit_progress("readme_complete", 30, "README generated ✓")

        await self._start_run_tracking("GenerateSetupGuide")
        setup_action = GenerateSetupGuide(context=self.context)
        setup_guide = await setup_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            infrastructure_summary=architecture[:2000],
        )
        await self.save_output(setup_guide, "SETUP_GUIDE.md", OutputType.SETUP_GUIDE, language="markdown")
        await self.emit_progress("setup_complete", 55, "Setup guide generated ✓")

        await self._start_run_tracking("GenerateAPIDocs")
        api_docs_action = GenerateAPIDocs(context=self.context)
        api_docs = await api_docs_action.run(
            [],
            idea=idea,
            api_spec=api_spec,
        )
        await self.save_output(api_docs, "API_REFERENCE.md", OutputType.API_DOCS, language="markdown")
        await self.emit_progress("api_docs_complete", 80, "API docs generated ✓")

        await self._start_run_tracking("GenerateDeploymentGuide")
        deploy_action = GenerateDeploymentGuide(context=self.context)
        deployment_guide = await deploy_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            infrastructure_summary=architecture[:2000],
        )
        await self.save_output(deployment_guide, "DEPLOYMENT_GUIDE.md", OutputType.DEPLOYMENT_GUIDE, language="markdown")
        await self.emit_progress("deploy_guide_complete", 100, "Deployment guide generated ✓")

        return {
            "readme": readme,
            "setup_guide": setup_guide,
            "api_docs": api_docs,
            "deployment_guide": deployment_guide,
        }
