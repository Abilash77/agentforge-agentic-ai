"""
AgentForge QA Agent.

Creates comprehensive quality assurance artifacts:
  - Test plan and coverage strategy
  - Unit tests (pytest / Jest)
  - Integration tests
  - Code quality report
"""

from __future__ import annotations

from metagpt.actions import Action
from metagpt.schema import Message

from agentforge.agents.base_agent import AgentForgeRole
from agentforge.constants import AgentRole, OutputType
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class CreateTestPlan(Action):
    name: str = "CreateTestPlan"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior QA Engineer and Test Architect.

## Project: {idea}
## Tech Stack: {tech_stack}
## Requirements: {requirements_summary}

Create a comprehensive Test Plan document.

### 1. Test Strategy
- Testing levels (unit, integration, e2e, performance, security)
- Testing approach (TDD/BDD/traditional)
- Coverage targets (minimum 80% unit test coverage)

### 2. Test Scope
| Feature | Unit Tests | Integration Tests | E2E Tests | Priority |
|---------|------------|------------------|-----------|----------|

### 3. Test Environment Setup
- Environment requirements
- Test data strategy
- Mock/stub strategy for external services
- CI/CD integration approach

### 4. Test Cases Table
| Test ID | Test Name | Category | Preconditions | Steps | Expected Result | Priority |
|---------|-----------|----------|---------------|-------|-----------------|----------|

Include at least 30 test cases covering:
- Happy path scenarios
- Edge cases
- Error scenarios
- Security test cases
- Performance test scenarios

### 5. Test Automation Strategy
- Tools and frameworks
- Page object model (for E2E)
- Test fixtures and factories
- Reporting strategy

### 6. Performance Testing Plan
- Load testing scenarios
- Stress testing thresholds
- Benchmark metrics

### 7. Security Testing
- OWASP Top 10 coverage
- Authentication/authorization testing
- Input validation testing

Format as professional Markdown with proper tables.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            requirements_summary=kwargs.get("requirements_summary", "")[:2000],
        )
        return await self._aask(prompt)


class GenerateUnitTests(Action):
    name: str = "GenerateUnitTests"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior QA Engineer expert in test-driven development.

## Project: {idea}
## Tech Stack: {tech_stack}
## Source Code Context: {code_summary}

Generate comprehensive unit tests for the project.

Write REAL, COMPLETE, RUNNABLE test code.

### Backend Unit Tests (pytest)
- Test all service/business logic functions
- Test all repository/data access functions
- Test all API endpoint handlers
- Test utility functions and validators
- Use pytest fixtures, factories, and mocks
- Include parametrized tests for edge cases
- Minimum 80% coverage target

### Frontend Unit Tests (Jest + React Testing Library)
- Test all components render correctly
- Test user interactions
- Test API integration hooks
- Test state management
- Test form validation

For each test file, start with:
```python
# === test_module_name.py ===
```

Include:
- Import statements
- Fixtures
- At least 5-8 test functions per module
- Edge cases and error scenarios
- Mocking of external dependencies

Write REAL test code, not pseudocode.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            tech_stack=kwargs.get("tech_stack", ""),
            code_summary=kwargs.get("code_summary", "")[:3000],
        )
        return await self._aask(prompt)


class GenerateIntegrationTests(Action):
    name: str = "GenerateIntegrationTests"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior QA Engineer specializing in integration and API testing.

## Project: {idea}
## API Spec: {api_spec_summary}
## Tech Stack: {tech_stack}

Generate comprehensive integration tests.

### 1. API Integration Tests (pytest + httpx or Postman collection)
For each API endpoint:
- Auth flow tests
- CRUD operation tests
- Pagination tests
- Error response tests
- Rate limiting tests

### 2. Database Integration Tests
- Test actual database operations
- Test transaction handling
- Test cascade deletes
- Test unique constraint violations

### 3. End-to-End Test Scenarios
Using Playwright or Cypress:
- User registration and login flow
- Core feature workflows
- Error state handling

### 4. Contract Tests
- API contract tests between frontend and backend
- Schema validation tests

Write complete, working test code with proper setup/teardown.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            api_spec_summary=kwargs.get("api_spec_summary", "")[:2000],
            tech_stack=kwargs.get("tech_stack", ""),
        )
        return await self._aask(prompt)


class DetectCodeQuality(Action):
    name: str = "DetectCodeQuality"

    PROMPT_TEMPLATE: ClassVar[str] = """\
You are a Senior Code Reviewer and Quality Engineer.

## Project: {idea}
## Generated Code Sample: {code_sample}

Perform a comprehensive code quality analysis.

### 1. Code Quality Report

#### SOLID Principles Compliance
For each principle (SRP, OCP, LSP, ISP, DIP):
- Compliance level (High/Medium/Low)
- Evidence from the code
- Recommendations

#### Code Metrics (Estimated)
- Cyclomatic complexity assessment
- Coupling and cohesion analysis
- Code duplication risk
- Documentation coverage

#### Security Analysis
- Input validation completeness
- SQL injection risks
- Authentication implementation review
- Secrets/credential handling

#### Performance Analysis
- N+1 query risks
- Missing indexes
- Inefficient algorithms
- Memory leak risks

### 2. Issue Report
| Issue ID | Category | Severity | File/Component | Description | Recommendation |
|----------|----------|----------|----------------|-------------|----------------|

Include at least 15 issues (mix of Critical, High, Medium, Low severity).

### 3. Best Practices Checklist
- [ ] Type hints used throughout
- [ ] Error handling in all functions
- [ ] Logging in appropriate places
- [ ] Input validation at API boundaries
- [ ] No hardcoded secrets
- [ ] Proper async/await usage
- etc.

### 4. Refactoring Recommendations
Top 5 refactoring opportunities with before/after code examples.

### 5. Overall Quality Score
Rate 1-10 with detailed justification.
"""

    async def run(self, messages: list[Message], **kwargs) -> str:
        prompt = self.PROMPT_TEMPLATE.format(
            idea=kwargs.get("idea", ""),
            code_sample=kwargs.get("code_sample", "")[:3000],
        )
        return await self._aask(prompt)


class QAAgent(AgentForgeRole):
    """
    QA Engineer Agent for AgentForge.

    Creates test plans, generates unit and integration tests,
    and produces code quality reports.
    """

    name: str = "Priya"
    profile: str = "QA Engineer"
    goal: str = (
        "Ensure software quality through comprehensive test planning, "
        "automated test generation, and code quality analysis."
    )
    constraints: str = (
        "Write real, runnable tests. Never write pseudocode. "
        "Aim for 80%+ code coverage. Cover all edge cases and error scenarios."
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_actions([
            CreateTestPlan,
            GenerateUnitTests,
            GenerateIntegrationTests,
            DetectCodeQuality,
        ])

    async def run_full_qa(
        self,
        idea: str,
        tech_stack: str,
        pm_outputs: dict,
        arch_outputs: dict,
        dev_outputs: dict,
    ) -> dict[str, str]:
        """Execute the full QA workflow."""
        await self.emit_progress("test_plan", 5, "Creating test plan...")
        await self._start_run_tracking("CreateTestPlan")
        test_plan_action = CreateTestPlan(context=self.context)
        test_plan = await test_plan_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            requirements_summary=pm_outputs.get("srs", "")[:2000],
        )
        await self.save_output(test_plan, "TEST_PLAN.md", OutputType.TEST_PLAN)
        await self.emit_progress("test_plan_complete", 25, "Test plan created ✓")

        await self._start_run_tracking("GenerateUnitTests")
        unit_action = GenerateUnitTests(context=self.context)
        unit_tests = await unit_action.run(
            [],
            idea=idea,
            tech_stack=tech_stack,
            code_summary=dev_outputs.get("backend_code", "")[:3000],
        )
        await self.save_output(unit_tests, "unit_tests.md", OutputType.UNIT_TESTS)
        await self.emit_progress("unit_tests_complete", 55, "Unit tests generated ✓")

        await self._start_run_tracking("GenerateIntegrationTests")
        int_action = GenerateIntegrationTests(context=self.context)
        integration_tests = await int_action.run(
            [],
            idea=idea,
            api_spec_summary=arch_outputs.get("api_spec", "")[:2000],
            tech_stack=tech_stack,
        )
        await self.save_output(integration_tests, "integration_tests.md", OutputType.INTEGRATION_TESTS)
        await self.emit_progress("integration_tests_complete", 80, "Integration tests generated ✓")

        await self._start_run_tracking("DetectCodeQuality")
        quality_action = DetectCodeQuality(context=self.context)
        quality_report = await quality_action.run(
            [],
            idea=idea,
            code_sample=dev_outputs.get("backend_code", "")[:3000],
        )
        await self.save_output(quality_report, "CODE_QUALITY_REPORT.md", OutputType.CODE_QUALITY)
        await self.emit_progress("quality_complete", 100, "Code quality report generated ✓")

        return {
            "test_plan": test_plan,
            "unit_tests": unit_tests,
            "integration_tests": integration_tests,
            "quality_report": quality_report,
        }
