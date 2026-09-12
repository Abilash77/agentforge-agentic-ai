"""
AgentForge RAG Context Injector.

Builds augmented prompts by prepending retrieved RAG context.
Respects LLM token budget to avoid exceeding context window limits.
"""

from __future__ import annotations

from typing import Optional

import tiktoken

from agentforge.config import get_config
from agentforge.constants import MAX_CONTEXT_TOKENS
from agentforge.monitoring.logger import get_logger
from agentforge.rag.retriever import RAGRetriever, RetrievedChunk

logger = get_logger(__name__)

# Tiktoken encoder for token counting (cl100k_base works for GPT-4 and GPT-3.5)
_ENCODER = None


def _get_encoder():
    global _ENCODER
    if _ENCODER is None:
        try:
            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENCODER = None
    return _ENCODER


def count_tokens(text: str) -> int:
    """Count tokens in a text string."""
    encoder = _get_encoder()
    if encoder:
        return len(encoder.encode(text))
    # Fallback: approximate 4 chars per token
    return len(text) // 4


class ContextInjector:
    """
    Builds RAG-augmented prompts for agent actions.

    Retrieves relevant context from ChromaDB and injects it
    into prompts while respecting the configured token budget.
    """

    def __init__(self, retriever: Optional[RAGRetriever] = None) -> None:
        self._retriever = retriever or RAGRetriever()
        self._cfg = get_config()
        self._max_context_tokens = MAX_CONTEXT_TOKENS

    def build_context_prompt(
        self,
        base_prompt: str,
        query: str,
        project_id: Optional[str] = None,
        top_k: int = 5,
        include_cross_project: bool = False,
    ) -> str:
        """
        Retrieve relevant context and prepend it to the base prompt.

        Args:
            base_prompt: The original agent prompt
            query: Search query to retrieve relevant context
            project_id: Restrict context to this project (None = cross-project)
            top_k: Max chunks to retrieve
            include_cross_project: Also search across other projects

        Returns:
            Augmented prompt with retrieved context prepended
        """
        if not self._cfg.enable_rag_context:
            return base_prompt

        chunks: list[RetrievedChunk] = []

        # 1. Project-scoped search (highest priority)
        if project_id:
            project_chunks = self._retriever.search_project(
                query=query, project_id=project_id, top_k=top_k
            )
            chunks.extend(project_chunks)

        # 2. Cross-project search (secondary context)
        if include_cross_project:
            cross_chunks = self._retriever.search_cross_project(query=query, top_k=top_k // 2)
            # Exclude chunks already found from project search
            existing_ids = {(c.filename, c.project_id) for c in chunks}
            cross_chunks = [
                c for c in cross_chunks if (c.filename, c.project_id) not in existing_ids
            ]
            chunks.extend(cross_chunks)

        if not chunks:
            return base_prompt

        # 3. Build context block respecting token budget
        context_block = self._build_context_block(chunks)
        if not context_block:
            return base_prompt

        augmented = f"{context_block}\n\n---\n\n{base_prompt}"
        logger.debug(
            f"Context injected: {len(chunks)} chunks, "
            f"~{count_tokens(context_block)} context tokens"
        )
        return augmented

    def _build_context_block(self, chunks: list[RetrievedChunk]) -> str:
        """
        Build a formatted context block from retrieved chunks.
        Stops adding chunks when the token budget is exceeded.
        """
        if not chunks:
            return ""

        header = "## Relevant Context from Project Knowledge Base\n\n"
        token_budget = self._max_context_tokens - count_tokens(header)

        selected_content = []
        total_tokens = 0

        for chunk in chunks:
            # Only include chunks with meaningful similarity
            if chunk.similarity_score < 0.3:
                continue
            chunk_text = chunk.to_context_string()
            chunk_tokens = count_tokens(chunk_text)
            if total_tokens + chunk_tokens > token_budget:
                break
            selected_content.append(chunk_text)
            total_tokens += chunk_tokens

        if not selected_content:
            return ""

        return header + "\n".join(selected_content)

    def get_context_for_agent(
        self,
        agent_role: str,
        project_id: str,
        task_description: str,
    ) -> str:
        """
        Get a ready-to-use context string for a specific agent.

        Args:
            agent_role: The role of the agent requesting context
            project_id: Current project ID
            task_description: Description of the current task

        Returns:
            Context string ready to prepend to the agent's prompt
        """
        # Build a targeted query based on agent role
        role_queries = {
            "product_manager": f"requirements specifications user stories {task_description}",
            "solution_architect": f"architecture design patterns technology stack {task_description}",
            "developer": f"source code implementation {task_description}",
            "qa_engineer": f"test cases unit tests integration tests {task_description}",
            "documentation": f"documentation readme API reference {task_description}",
            "devops": f"docker deployment CI/CD kubernetes {task_description}",
            "ppt": f"project summary features business value {task_description}",
        }
        query = role_queries.get(agent_role, task_description)

        chunks = self._retriever.search_project(
            query=query, project_id=project_id, top_k=5
        )
        return self._build_context_block(chunks)
