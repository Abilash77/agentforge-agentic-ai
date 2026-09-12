"""agentforge/rag package"""
from agentforge.rag.chroma_client import (
    get_architecture_collection,
    get_chroma_client,
    get_code_collection,
    get_or_create_collection,
    get_project_knowledge_collection,
    get_tests_collection,
)
from agentforge.rag.context_injector import ContextInjector
from agentforge.rag.document_indexer import DocumentIndexer
from agentforge.rag.retriever import RAGRetriever, RetrievedChunk

__all__ = [
    "get_chroma_client",
    "get_or_create_collection",
    "get_project_knowledge_collection",
    "get_code_collection",
    "get_architecture_collection",
    "get_tests_collection",
    "DocumentIndexer",
    "RAGRetriever",
    "RetrievedChunk",
    "ContextInjector",
]
