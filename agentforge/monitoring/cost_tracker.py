"""
AgentForge Cost Tracker.

Wraps MetaGPT's CostManager with extended functionality:
  - Per-model pricing table
  - SQLite cost event persistence
  - Real-time cost accumulation
  - Budget enforcement
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from agentforge.constants import DEFAULT_BUDGET_USD, MODEL_PRICING
from agentforge.database.database import get_session
from agentforge.database.repository import MetricsRepository, ProjectRepository
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)


class CostTracker:
    """
    Tracks token usage and estimated costs for a project pipeline.

    Uses per-model pricing from MODEL_PRICING constant.
    Persists cost events to SQLite for the monitoring dashboard.
    """

    def __init__(self, project_id: str, budget_usd: float = DEFAULT_BUDGET_USD) -> None:
        self.project_id = project_id
        self.budget_usd = budget_usd
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_cost_usd = 0.0
        self._cost_events: list[dict] = []

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4o",
    ) -> float:
        """
        Calculate the cost for a given token usage.

        Args:
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            model: Model name for pricing lookup

        Returns:
            Estimated cost in USD
        """
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost

    async def record_usage(
        self,
        agent_role: str,
        action_name: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "gpt-4o",
    ) -> float:
        """
        Record token usage and calculate cost.

        Returns:
            Cost in USD for this usage event
        """
        cost = self.calculate_cost(input_tokens, output_tokens, model)

        self._total_input_tokens += input_tokens
        self._total_output_tokens += output_tokens
        self._total_cost_usd += cost

        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_role": agent_role,
            "action_name": action_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model": model,
            "cost_usd": round(cost, 6),
        }
        self._cost_events.append(event)

        # Persist to SQLite
        try:
            async with get_session() as session:
                metrics_repo = MetricsRepository(session)
                await metrics_repo.record_project_metric(
                    project_id=self.project_id,
                    metric_name="cost.event_usd",
                    value=cost,
                    agent_role=agent_role,
                )
                proj_repo = ProjectRepository(session)
                await proj_repo.update_costs(
                    project_id=self.project_id,
                    tokens=input_tokens + output_tokens,
                    cost_usd=cost,
                )
        except Exception as e:
            logger.warning(f"Failed to persist cost event: {e}")

        logger.debug(
            f"Cost event: {agent_role}/{action_name} | "
            f"{input_tokens}+{output_tokens} tokens | ${cost:.4f}"
        )

        # Budget check
        if self._total_cost_usd > self.budget_usd:
            logger.warning(
                f"Budget exceeded! Spent ${self._total_cost_usd:.4f} / ${self.budget_usd:.2f}"
            )

        return cost

    def is_over_budget(self) -> bool:
        return self._total_cost_usd >= self.budget_usd

    def remaining_budget(self) -> float:
        return max(0.0, self.budget_usd - self._total_cost_usd)

    @property
    def total_tokens(self) -> int:
        return self._total_input_tokens + self._total_output_tokens

    @property
    def total_cost_usd(self) -> float:
        return self._total_cost_usd

    def get_report(self) -> dict:
        """Return a cost report summary."""
        by_agent: dict = {}
        for event in self._cost_events:
            role = event["agent_role"]
            if role not in by_agent:
                by_agent[role] = {"tokens": 0, "cost_usd": 0.0, "calls": 0}
            by_agent[role]["tokens"] += event["input_tokens"] + event["output_tokens"]
            by_agent[role]["cost_usd"] += event["cost_usd"]
            by_agent[role]["calls"] += 1

        return {
            "project_id": self.project_id,
            "budget_usd": self.budget_usd,
            "total_cost_usd": round(self._total_cost_usd, 4),
            "remaining_budget_usd": round(self.remaining_budget(), 4),
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "total_tokens": self.total_tokens,
            "cost_by_agent": by_agent,
            "event_count": len(self._cost_events),
        }
