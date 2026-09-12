"""
AgentForge DevOps Agent.

Generates complete DevOps and infrastructure configuration:
  - Multi-stage Dockerfiles
  - docker-compose.yml
  - GitHub Actions CI/CD pipeline
  - Kubernetes manifests
  - Deployment scripts
"""

from __future__ import annotations

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class GenerateDockerfile(Action):
    name: str = "GenerateDockerfile"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior DevOps Engineer and Docker expert.

## Project: {idea}
## Tech Stack: {tech_stack}
## Folder Structure: {folder_structure}

Generate production-grade Dockerfiles with multi-stage builds.

### 1. Backend Dockerfile
```dockerfile
# Multi-stage build
# Stage 1: Builder
# Stage 2: Production image
# - Non-root user
# - Health check
# - Minimal image size
# - Security hardening
```

### 2. Frontend Dockerfile
```dockerfile
# Multi-stage build
# Stage 1: Node build
# Stage 2: Nginx serve
```

### 3. .dockerignore
```
# Comprehensive .dockerignore
```

### 4. Nginx Configuration (for frontend)
```nginx
# Production-ready nginx.conf
```

Requirements:
- Use specific, pinned base image versions (not :latest)
- Non-root user in production stage
- COPY only what's needed
- Health check directive
- Optimize layer caching (dependencies before source code)
- ARG for build-time variables, ENV for runtime
- Proper EXPOSE directives
- CMD vs ENTRYPOINT usage

Output each file clearly labeled.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            folder_structure=kwargs.get("folder_structure", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateDockerCompose(Action):
    name: str = "GenerateDockerCompose"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior DevOps Engineer.

## Project: {idea}
## Tech Stack: {tech_stack}
## Architecture: {architecture_summary}

Generate complete Docker Compose configurations.

### 1. docker-compose.yml (Production)
```yaml
# Full production stack with:
# - Backend API service
# - Frontend service
# - Database (PostgreSQL/MySQL/MongoDB)
# - Cache (Redis)
# - Reverse proxy (Nginx/Traefik)
# - Message queue (if needed)
# Proper:
# - Networks (frontend, backend)
# - Volumes (named, for persistence)
# - Environment variables (from .env)
# - Health checks with depends_on conditions
# - Restart policies
# - Resource limits
# - Logging configuration
```

### 2. docker-compose.dev.yml (Development override)
```yaml
# Development overrides:
# - Volume mounts for hot reload
# - Debug ports exposed
# - Development environment variables
# - Reduced resource limits
```

### 3. docker-compose.test.yml (Testing)
```yaml
# Test environment with:
# - In-memory or separate test databases
# - Test-specific configuration
```

Include complete, valid YAML for all three files.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            architecture_summary=kwargs.get("architecture_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateCICDPipeline(Action):
    name: str = "GenerateCICDPipeline"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior DevOps Engineer and CI/CD specialist.

## Project: {idea}
## Tech Stack: {tech_stack}

Generate complete CI/CD pipeline configurations.

### 1. GitHub Actions — Main Pipeline (.github/workflows/main.yml)
```yaml
# Trigger on: push to main, PR to main
# Jobs:
# 1. lint — Code linting and formatting check
# 2. test — Run all tests with coverage report
# 3. security — SAST scan (Bandit/ESLint security)
# 4. build — Docker build and push to registry
# 5. deploy-staging — Deploy to staging (on main push)
# 6. integration-test — Run E2E tests on staging
# 7. deploy-production — Deploy to production (on tag)
```

### 2. GitHub Actions — PR Check (.github/workflows/pr-check.yml)
```yaml
# Lightweight checks for PRs:
# - Lint
# - Unit tests
# - Security scan
# - Size check
```

### 3. GitLab CI (.gitlab-ci.yml)
```yaml
# Equivalent pipeline for GitLab CI
```

### 4. Makefile
```makefile
# Common development commands:
# make lint, make test, make build, make deploy
```

Include complete YAML with all steps, environment variables, and deployment commands.
Use GitHub Environments for secrets management.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
        )
        return await self._aask(prompt)


class GenerateKubernetesManifests(Action):
    name: str = "GenerateKubernetesManifests"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Kubernetes and Cloud Native engineer.

## Project: {idea}
## Tech Stack: {tech_stack}
## Architecture: {architecture_summary}

Generate production-grade Kubernetes manifests.

### Files to generate:

#### k8s/namespace.yaml
```yaml
# Namespace definition
```

#### k8s/configmap.yaml
```yaml
# Application configuration
```

#### k8s/secret.yaml
```yaml
# Secret template (base64 encoded placeholders)
```

#### k8s/backend-deployment.yaml
```yaml
# Deployment with:
# - Rolling update strategy
# - Resource requests and limits
# - Liveness and readiness probes
# - Environment from ConfigMap and Secret
# - Pod disruption budget
```

#### k8s/backend-service.yaml
```yaml
# ClusterIP service
```

#### k8s/frontend-deployment.yaml
```yaml
# Frontend deployment
```

#### k8s/frontend-service.yaml
```yaml
```

#### k8s/ingress.yaml
```yaml
# Nginx Ingress with TLS (cert-manager)
# Path-based routing
```

#### k8s/hpa.yaml
```yaml
# Horizontal Pod Autoscaler
# Scale on CPU and memory
```

#### k8s/pdb.yaml
```yaml
# Pod Disruption Budget
```

#### k8s/network-policy.yaml
```yaml
# Network policies for security
```

Output complete, valid YAML for each file.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            architecture_summary=kwargs.get("architecture_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateDeploymentScripts(Action):
    name: str = "GenerateDeploymentScripts"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior DevOps Engineer.

## Project: {idea}
## Tech Stack: {tech_stack}

Generate comprehensive deployment shell scripts.

### 1. deploy.sh — Main deployment script
```bash
#!/bin/bash
# Production deployment script
# Usage: ./deploy.sh [environment] [version]
# Features:
# - Pre-deployment checks
# - Database backup
# - Health check before deployment
# - Blue-green deployment
# - Health check after deployment
# - Automatic rollback on failure
# - Slack notification
```

### 2. setup-server.sh — New server setup
```bash
#!/bin/bash
# Initial server setup script
# - Install Docker and Docker Compose
# - Configure firewall
# - Setup SSL with Let's Encrypt
# - Configure system limits
# - Setup monitoring agents
```

### 3. backup.sh — Database backup script
```bash
#!/bin/bash
# Automated backup script
# - PostgreSQL/MySQL dump
# - Compress and encrypt
# - Upload to S3
# - Cleanup old backups
# - Notification on failure
```

### 4. rollback.sh — Emergency rollback
```bash
#!/bin/bash
# Rollback to previous version
# - Identify last stable version
# - Deploy previous container
# - Verify rollback success
```

Write complete, production-ready bash scripts with proper error handling.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
        )
        return await self._aask(prompt)


class DevOpsAgent(AgentForgeRole):
    """
    DevOps Agent for AgentForge.

    Generates Docker configuration, CI/CD pipelines,
    Kubernetes manifests, and deployment scripts.
    """

    name: str = "Jordan"
    profile: str = "DevOps Engineer"
    goal: str = (
        "Create complete containerization, CI/CD, and infrastructure-as-code "
        "configuration to make the project deployment-ready."
    )
    constraints: str = (
        "Generate real, working configuration files. "
        "Use specific version pins, not :latest. "
        "Include health checks, rollback, and monitoring in all deployments."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([
            GenerateDockerfile,
            GenerateDockerCompose,
            GenerateCICDPipeline,
            GenerateKubernetesManifests,
            GenerateDeploymentScripts,
        ])

    async def run_full_devops(
        self,
        idea: str,
        tech_stack: str,
        arch_outputs: dict,
        dev_outputs: dict,
    ) -> dict[str, str]:
        """Execute the full DevOps workflow."""
        architecture = arch_outputs.get("architecture", "")
        folder_structure = dev_outputs.get("folder_structure", "")

        await self.emit_progress("dockerfile", 5, "Generating Dockerfiles...")
        await self._start_run_tracking("GenerateDockerfile")
        docker_action = GenerateDockerfile(context=self.context)
        dockerfiles = await docker_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            folder_structure=folder_structure[:2000],
        )
        await self.save_output(dockerfiles, "Dockerfiles.md", OutputType.DOCKERFILE)
        await self.emit_progress("dockerfile_complete", 20, "Dockerfiles generated ✓")

        await self._start_run_tracking("GenerateDockerCompose")
        compose_action = GenerateDockerCompose(context=self.context)
        docker_compose = await compose_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            architecture_summary=architecture[:2000],
        )
        await self.save_output(docker_compose, "docker-compose.yml.md", OutputType.DOCKER_COMPOSE)
        await self.emit_progress("compose_complete", 40, "Docker Compose generated ✓")

        await self._start_run_tracking("GenerateCICDPipeline")
        cicd_action = GenerateCICDPipeline(context=self.context)
        cicd = await cicd_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
        )
        await self.save_output(cicd, "CI_CD_PIPELINE.md", OutputType.CICD_PIPELINE)
        await self.emit_progress("cicd_complete", 60, "CI/CD pipeline generated ✓")

        await self._start_run_tracking("GenerateKubernetesManifests")
        k8s_action = GenerateKubernetesManifests(context=self.context)
        k8s = await k8s_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            architecture_summary=architecture[:2000],
        )
        await self.save_output(k8s, "KUBERNETES_MANIFESTS.md", OutputType.K8S_MANIFESTS)
        await self.emit_progress("k8s_complete", 80, "Kubernetes manifests generated ✓")

        await self._start_run_tracking("GenerateDeploymentScripts")
        scripts_action = GenerateDeploymentScripts(context=self.context)
        scripts = await scripts_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
        )
        await self.save_output(scripts, "DEPLOYMENT_SCRIPTS.md", OutputType.DEPLOY_SCRIPTS)
        await self.emit_progress("scripts_complete", 100, "Deployment scripts generated ✓")

        return {
            "dockerfiles": dockerfiles,
            "docker_compose": docker_compose,
            "cicd": cicd,
            "k8s": k8s,
            "scripts": scripts,
        }
