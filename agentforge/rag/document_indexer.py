"""
AgentForge Document Indexer.

Ingests generated project files into ChromaDB vector collections.
Handles chunking, metadata tagging, and embedding generation.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Optional

from agentforge.constants import OutputType
from agentforge.monitoring.logger import get_logger
from agentforge.rag.chroma_client import (
    get_architecture_collection,
    get_code_collection,
    get_project_knowledge_collection,
    get_tests_collection,
)

logger = get_logger(__name__)

# Map OutputType to ChromaDB collection getter
OUTPUT_TO_COLLECTION = {
    OutputType.BRD: get_project_knowledge_collection,
    OutputType.SRS: get_project_knowledge_collection,
    OutputType.RISK_MATRIX: get_project_knowledge_collection,
    OutputType.MILESTONES: get_project_knowledge_collection,
    OutputType.ARCHITECTURE: get_architecture_collection,
    OutputType.DATABASE_SCHEMA: get_architecture_collection,
    OutputType.API_SPEC: get_architecture_collection,
    OutputType.TECH_STACK: get_architecture_collection,
    OutputType.SOURCE_CODE: get_code_collection,
    OutputType.FOLDER_STRUCTURE: get_code_collection,
    OutputType.TEST_PLAN: get_tests_collection,
    OutputType.UNIT_TESTS: get_tests_collection,
    OutputType.INTEGRATION_TESTS: get_tests_collection,
}

MAX_CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 100


def _chunk_text(text: str, chunk_size: int = MAX_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks for indexing."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        # Try to split at a sentence boundary
        last_period = chunk.rfind(". ")
        if last_period > chunk_size // 2:
            chunk = chunk[:last_period + 1]
        chunks.append(chunk.strip())
        start += len(chunk) - overlap

    return [c for c in chunks if c.strip()]


def _generate_doc_id(project_id: str, filename: str, chunk_index: int) -> str:
    """Generate a stable document ID for a chunk."""
    raw = f"{project_id}::{filename}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def _infer_language(filename: str, content: str) -> Optional[str]:
    """Infer programming language from filename extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".sql": "sql",
        ".sh": "bash",
        ".dockerfile": "dockerfile",
        ".md": "markdown",
    }
    for ext, lang in ext_map.items():
        if filename.lower().endswith(ext):
            return lang
    if filename.lower() == "dockerfile":
        return "dockerfile"
    return None


class DocumentIndexer:
    """
    Indexes generated project documents into ChromaDB.

    Supports chunking of large documents, metadata tagging,
    and deduplication via stable content hashes.
    """

    def index_document(
        self,
        project_id: str,
        agent_role: str,
        filename: str,
        content: str,
        output_type: OutputType,
        extra_metadata: Optional[dict] = None,
    ) -> int:
        """
        Index a document into the appropriate ChromaDB collection.

        Args:
            project_id: Project ID for namespacing
            agent_role: Which agent generated this document
            filename: File name (used for display and language detection)
            content: Document content to index
            output_type: Type of output (determines collection)
            extra_metadata: Additional metadata to store

        Returns:
            Number of chunks indexed
        """
        if not content or not content.strip():
            logger.warning(f"Skipping empty document: {filename}")
            return 0

        # Get the target collection
        collection_getter = OUTPUT_TO_COLLECTION.get(output_type, get_project_knowledge_collection)
        collection = collection_getter()

        # Chunk the document
        chunks = _chunk_text(content)

        # Build metadata
        base_metadata = {
            "project_id": project_id,
            "agent_role": agent_role,
            "filename": filename,
            "output_type": output_type.value,
            "language": _infer_language(filename, content) or "text",
            "total_chunks": len(chunks),
        }
        if extra_metadata:
            base_metadata.update(extra_metadata)

        # Prepare batch
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            doc_id = _generate_doc_id(project_id, filename, i)
            chunk_metadata = {**base_metadata, "chunk_index": i}
            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append(chunk_metadata)

        # Upsert into ChromaDB (handles duplicates gracefully)
        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            logger.info(
                f"Indexed {len(chunks)} chunks for {filename} "
                f"(project={project_id}, type={output_type.value})"
            )
            return len(chunks)
        except Exception as e:
            logger.error(f"Failed to index {filename}: {e}")
            return 0

    def index_batch(
        self,
        project_id: str,
        agent_role: str,
        documents: list[dict],
    ) -> int:
        """
        Index multiple documents in one call.

        Args:
            project_id: Project ID
            agent_role: Agent role that generated these documents
            documents: List of dicts with keys: filename, content, output_type

        Returns:
            Total number of chunks indexed
        """
        total = 0
        for doc in documents:
            total += self.index_document(
                project_id=project_id,
                agent_role=agent_role,
                filename=doc["filename"],
                content=doc["content"],
                output_type=doc["output_type"],
                extra_metadata=doc.get("metadata"),
            )
        return total

    def delete_project_index(self, project_id: str) -> None:
        """Remove all indexed documents for a project."""
        from agentforge.rag.chroma_client import delete_project_documents
        delete_project_documents(project_id)
        logger.info(f"Deleted all indexed documents for project: {project_id}")
