"""
AgentForge RAG Retriever.

Semantic similarity search across ChromaDB collections.
Supports cross-project search and collection-scoped queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from agentforge.config import get_config
from agentforge.monitoring.logger import get_logger
from agentforge.rag.chroma_client import (
    ALL_COLLECTIONS,
    get_architecture_collection,
    get_chroma_client,
    get_code_collection,
    get_or_create_collection,
    get_project_knowledge_collection,
    get_tests_collection,
)

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """A single retrieved document chunk with metadata."""
    content: str
    filename: str
    project_id: str
    agent_role: str
    output_type: str
    similarity_score: float
    collection_name: str
    chunk_index: int = 0

    def to_context_string(self) -> str:
        """Format as a context block for LLM prompt injection."""
        return (
            f"### {self.filename} [{self.agent_role}] (similarity: {self.similarity_score:.2f})\n"
            f"{self.content}\n"
        )


class RAGRetriever:
    """
    Semantic similarity search across AgentForge ChromaDB collections.

    Supports:
    - Project-scoped search (within one project)
    - Cross-project search (across all projects)
    - Collection-specific search
    - Combined multi-collection search
    """

    def __init__(self) -> None:
        self._cfg = get_config()
        self._top_k = self._cfg.chroma.top_k

    def search_project(
        self,
        query: str,
        project_id: str,
        top_k: Optional[int] = None,
    ) -> list[RetrievedChunk]:
        """
        Search all collections filtered to a specific project.

        Args:
            query: Natural language search query
            project_id: Restrict results to this project
            top_k: Number of results to return

        Returns:
            List of RetrievedChunk sorted by similarity
        """
        k = top_k or self._top_k
        results: list[RetrievedChunk] = []

        for collection_name in ALL_COLLECTIONS:
            chunks = self._search_collection(
                query=query,
                collection_name=collection_name,
                where={"project_id": project_id},
                top_k=k,
            )
            results.extend(chunks)

        # Sort by similarity score and return top-k across all collections
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:k]

    def search_cross_project(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> list[RetrievedChunk]:
        """Search across all projects and all collections."""
        k = top_k or self._top_k
        results: list[RetrievedChunk] = []

        for collection_name in ALL_COLLECTIONS:
            chunks = self._search_collection(
                query=query,
                collection_name=collection_name,
                top_k=k,
            )
            results.extend(chunks)

        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:k]

    def search_architecture(
        self, query: str, project_id: Optional[str] = None, top_k: Optional[int] = None
    ) -> list[RetrievedChunk]:
        """Search architecture-specific collection."""
        where = {"project_id": project_id} if project_id else None
        return self._search_collection(
            query=query,
            collection_name="architecture_docs",
            where=where,
            top_k=top_k or self._top_k,
        )

    def search_code(
        self, query: str, project_id: Optional[str] = None, top_k: Optional[int] = None
    ) -> list[RetrievedChunk]:
        """Search code collection."""
        where = {"project_id": project_id} if project_id else None
        return self._search_collection(
            query=query,
            collection_name="generated_code",
            where=where,
            top_k=top_k or self._top_k,
        )

    def _search_collection(
        self,
        query: str,
        collection_name: str,
        where: Optional[dict] = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Internal: query a single collection."""
        try:
            client = get_chroma_client()
            collection = client.get_collection(collection_name)

            kwargs = {
                "query_texts": [query],
                "n_results": min(top_k, max(1, collection.count())),
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                kwargs["where"] = where

            response = collection.query(**kwargs)

            chunks = []
            for doc, meta, dist in zip(
                response["documents"][0],
                response["metadatas"][0],
                response["distances"][0],
            ):
                # ChromaDB distance → similarity (cosine: 0=identical, 2=opposite)
                similarity = max(0.0, 1.0 - dist / 2.0)
                chunk = RetrievedChunk(
                    content=doc,
                    filename=meta.get("filename", "unknown"),
                    project_id=meta.get("project_id", ""),
                    agent_role=meta.get("agent_role", ""),
                    output_type=meta.get("output_type", ""),
                    similarity_score=similarity,
                    collection_name=collection_name,
                    chunk_index=meta.get("chunk_index", 0),
                )
                chunks.append(chunk)
            return chunks

        except Exception as e:
            if "does not exist" not in str(e):
                logger.warning(f"Search failed for collection {collection_name}: {e}")
            return []
