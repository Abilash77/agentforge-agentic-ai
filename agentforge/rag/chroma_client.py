"""
AgentForge ChromaDB Client.

Singleton ChromaDB client managing all vector collections.
Each collection stores a different category of project knowledge.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

import chromadb
from chromadb.config import Settings

from agentforge.config import get_config
from agentforge.monitoring.logger import get_logger

logger = get_logger(__name__)

# Collection names
COLLECTION_PROJECT_KNOWLEDGE = "project_knowledge"
COLLECTION_GENERATED_CODE = "generated_code"
COLLECTION_ARCHITECTURE = "architecture_docs"
COLLECTION_TESTS = "test_cases"

ALL_COLLECTIONS = [
    COLLECTION_PROJECT_KNOWLEDGE,
    COLLECTION_GENERATED_CODE,
    COLLECTION_ARCHITECTURE,
    COLLECTION_TESTS,
]


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.PersistentClient:
    """
    Return the singleton ChromaDB PersistentClient.
    Creates the persist directory if it doesn't exist.
    """
    cfg = get_config()
    persist_dir = cfg.chroma.persist_directory

    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )
    logger.info(f"ChromaDB client initialized at: {persist_dir}")
    return client


def get_or_create_collection(
    collection_name: str,
    metadata: Optional[dict] = None,
) -> chromadb.Collection:
    """
    Get an existing collection or create it if it doesn't exist.

    Args:
        collection_name: Name of the ChromaDB collection
        metadata: Optional metadata dict for the collection

    Returns:
        ChromaDB Collection object
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata=metadata or {"hnsw:space": "cosine"},
    )
    return collection


def get_project_knowledge_collection() -> chromadb.Collection:
    """Collection for BRDs, SRSs, risk matrices, and project metadata."""
    return get_or_create_collection(
        COLLECTION_PROJECT_KNOWLEDGE,
        metadata={"description": "Project knowledge, requirements, and specifications"},
    )


def get_code_collection() -> chromadb.Collection:
    """Collection for generated source code files."""
    return get_or_create_collection(
        COLLECTION_GENERATED_CODE,
        metadata={"description": "Generated source code and folder structures"},
    )


def get_architecture_collection() -> chromadb.Collection:
    """Collection for architecture docs, API specs, and database schemas."""
    return get_or_create_collection(
        COLLECTION_ARCHITECTURE,
        metadata={"description": "Architecture diagrams, API specs, database schemas"},
    )


def get_tests_collection() -> chromadb.Collection:
    """Collection for test plans and generated test code."""
    return get_or_create_collection(
        COLLECTION_TESTS,
        metadata={"description": "Test plans, unit tests, and integration tests"},
    )


def delete_project_documents(project_id: str) -> None:
    """Remove all documents for a project from all collections."""
    client = get_chroma_client()
    for collection_name in ALL_COLLECTIONS:
        try:
            collection = client.get_collection(collection_name)
            results = collection.get(where={"project_id": project_id})
            if results["ids"]:
                collection.delete(ids=results["ids"])
                logger.info(
                    f"Deleted {len(results['ids'])} docs from {collection_name} for project {project_id}"
                )
        except Exception as e:
            logger.warning(f"Could not delete from {collection_name}: {e}")


def reset_all_collections() -> None:
    """Reset all collections (use only in testing)."""
    client = get_chroma_client()
    for collection_name in ALL_COLLECTIONS:
        try:
            client.delete_collection(collection_name)
            logger.warning(f"Deleted collection: {collection_name}")
        except Exception:
            pass
