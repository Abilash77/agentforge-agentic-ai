"""agentforge/workflows package"""
from agentforge.workflows.output_collector import OutputCollector
from agentforge.workflows.pipeline import AgentForgePipeline, PipelineResult
from agentforge.workflows.task_manager import TaskManager, get_task_manager

__all__ = [
    "AgentForgePipeline",
    "PipelineResult",
    "TaskManager",
    "get_task_manager",
    "OutputCollector",
]
