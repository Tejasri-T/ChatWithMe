"""High-level RAG orchestration service."""

from __future__ import annotations

from typing import Any

from langchain_core.embeddings import Embeddings

from app.core.rag.embeddings import get_embeddings
from app.core.rag.ingestion import DocumentIngestionService
from app.core.rag.vectorstore import VectorStoreRegistry


class RAGService:
    """Unified service for document ingestion, indexing, and context retrieval."""

    def __init__(self, embeddings: Embeddings | None = None):
        self._embeddings = embeddings
        self.ingestion = DocumentIngestionService()
        self._registry: VectorStoreRegistry | None = (
            VectorStoreRegistry(self._embeddings) if self._embeddings else None
        )

    @property
    def registry(self) -> VectorStoreRegistry:
        """Lazily initialize registry with embeddings when required."""
        if self._registry is None:
            if self._embeddings is None:
                self._embeddings = get_embeddings()
            self._registry = VectorStoreRegistry(self._embeddings)
        return self._registry

    def ingest_pdf(self, thread_id: str, file_bytes: bytes, filename: str) -> dict:
        """Parse, chunk, and index an uploaded PDF for a thread."""
        chunks, summary = self.ingestion.parse_pdf(file_bytes, filename)
        return self.registry.index_documents(thread_id, chunks, summary)

    def retrieve_context(
        self,
        thread_id: str | None,
        query: str,
        top_k: int = 4,
    ) -> dict[str, Any]:
        """
        Query context from indexed documents for a thread.
        Returns a formatted dictionary ready for tool responses.
        """
        if not thread_id:
            return {
                "error": "No thread_id provided for document retrieval.",
                "query": query,
            }

        # If registry hasn't been instantiated yet, no documents have been indexed
        if self._registry is None or not self._registry.has_document(thread_id):
            return {
                "error": "No document indexed for this chat. Please upload a PDF first.",
                "query": query,
            }

        docs = self._registry.search(thread_id=thread_id, query=query, top_k=top_k)
        context = [doc.page_content for doc in docs]
        metadata = [doc.metadata for doc in docs]
        meta = self._registry.get_metadata(thread_id)

        return {
            "query": query,
            "context": context,
            "metadata": metadata,
            "source_file": meta.get("filename"),
            "total_chunks_matched": len(docs),
        }

    def has_document(self, thread_id: str) -> bool:
        """Check if a thread has documents indexed."""
        if self._registry is None:
            return False
        return self._registry.has_document(thread_id)

    def get_document_metadata(self, thread_id: str) -> dict:
        """Fetch indexed document summary metadata for a thread."""
        if self._registry is None:
            return {}
        return self._registry.get_metadata(thread_id)

    def delete_thread_documents(self, thread_id: str) -> bool:
        """Clean up vector store memory when a thread is deleted."""
        if self._registry is None:
            return False
        return self._registry.delete_thread_index(thread_id)


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    """Singleton accessor for RAGService."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
