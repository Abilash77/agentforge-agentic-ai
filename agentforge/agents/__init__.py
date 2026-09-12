"""agentforge/agents package"""
from agentforge.agents.base_agent import AgentForgeRole
from agentforge.agents.developer_agent import DeveloperAgent
from agentforge.agents.devops_agent import DevOpsAgent
from agentforge.agents.documentation_agent import DocumentationAgent
from agentforge.agents.ppt_agent import PPTAgent
from agentforge.agents.product_manager_agent import ProductManagerAgent
from agentforge.agents.qa_agent import QAAgent
from agentforge.agents.solution_architect_agent import SolutionArchitectAgent

__all__ = [
    "AgentForgeRole",
    "ProductManagerAgent",
    "SolutionArchitectAgent",
    "DeveloperAgent",
    "QAAgent",
    "DocumentationAgent",
    "DevOpsAgent",
    "PPTAgent",
]
