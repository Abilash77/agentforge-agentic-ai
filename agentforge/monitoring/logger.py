"""
AgentForge Structured Logger.

Uses loguru for structured JSON logging with context enrichment.
Every log entry includes: timestamp, level, module, project_id, agent_name.
"""

from __future__ import annotations

import sys
from typing import Optional

from loguru import logger as _loguru_logger

from agentforge.config import get_config

_configured = False


def _configure_logger() -> None:
    global _configured
    if _configured:
        return

    cfg = get_config()

    # Remove default handler
    _loguru_logger.remove()

    # Console handler — pretty format for development
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    _loguru_logger.add(
        sys.stderr,
        format=log_format,
        level=cfg.log_level,
        colorize=True,
        backtrace=True,
        diagnose=cfg.is_debug,
    )

    # File handler — JSON format for production/monitoring
    if cfg.log_to_file:
        _loguru_logger.add(
            cfg.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{line} | {message}",
            level=cfg.log_level,
            rotation="50 MB",
            retention="14 days",
            compression="gz",
            backtrace=True,
            diagnose=False,
            serialize=True,  # JSON output
        )

    _configured = True


def get_logger(name: str):
    """Return a loguru logger bound to a module name."""
    _configure_logger()
    return _loguru_logger.bind(module=name)


class AgentLogger:
    """
    Context-enriched logger for agent actions.
    Automatically includes project_id and agent metadata in every log call.
    """

    def __init__(
        self,
        agent_name: str,
        agent_role: str,
        project_id: Optional[str] = None,
    ) -> None:
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.project_id = project_id or "global"
        _configure_logger()
        self._logger = _loguru_logger.bind(
            agent_name=agent_name,
            agent_role=agent_role,
            project_id=self.project_id,
        )

    def set_project(self, project_id: str) -> None:
        self.project_id = project_id
        self._logger = _loguru_logger.bind(
            agent_name=self.agent_name,
            agent_role=self.agent_role,
            project_id=project_id,
        )

    def info(self, msg: str, **kwargs) -> None:
        self._logger.info(msg, **kwargs)

    def debug(self, msg: str, **kwargs) -> None:
        self._logger.debug(msg, **kwargs)

    def warning(self, msg: str, **kwargs) -> None:
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs) -> None:
        self._logger.error(msg, **kwargs)

    def success(self, msg: str, **kwargs) -> None:
        self._logger.success(msg, **kwargs)

    def log_action_start(self, action_name: str) -> None:
        self._logger.info(f"▶ ACTION START: {action_name}")

    def log_action_complete(
        self, action_name: str, duration_ms: int, tokens: int, cost_usd: float
    ) -> None:
        self._logger.success(
            f"✓ ACTION COMPLETE: {action_name} | "
            f"duration={duration_ms}ms | tokens={tokens} | cost=${cost_usd:.4f}"
        )

    def log_action_error(self, action_name: str, error: Exception) -> None:
        self._logger.error(f"✗ ACTION ERROR: {action_name} | {type(error).__name__}: {error}")
