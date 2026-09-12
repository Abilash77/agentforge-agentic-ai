"""
AgentForge – Autonomous Multi-Agent Software Engineering Platform
Built on top of MetaGPT framework.
"""

__version__ = "1.0.0"
__author__ = "AgentForge Team"
__description__ = "Transform ideas into production-ready software using autonomous AI agents"

from agentforge.config import AgentForgeConfig, get_config
from agentforge.constants import AgentRole, ProjectStatus, ProjectType, TechStack

__all__ = [
    "AgentForgeConfig",
    "get_config",
    "AgentRole",
    "ProjectStatus",
    "ProjectType",
    "TechStack",
]
