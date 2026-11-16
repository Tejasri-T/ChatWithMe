"""Vector store abstraction and registry."""

from __future__ import annotations

from typing import Any, cast

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


class VectorStoreRegistry:
    """Thread-scoped vector store manager."""

    def __init__(self, embeddings: Embeddings):
        self.embeddings = embeddings
        self._stores: dict[str, Any] = {}
        self._metadata: dict[str, dict] = {}

    def index_documents(
        self,
        thread_id: str,
        documents: list[Document],
        summary_metadata: dict,
    ) -> dict:
        """Create or update a FAISS vector index for the designated thread."""
        thread_key = str(thread_id)
        vector_store = FAISS.from_documents(documents, self.embeddings)
        self._stores[thread_key] = vector_store
        self._metadata[thread_key] = summary_metadata
        return summary_metadata

    def get_retriever(self, thread_id: str | None, top_k: int = 4):
        """Retrieve a LangChain retriever for the thread if one exists."""
        if not thread_id:
            return None
        thread_key = str(thread_id)
        store = self._stores.get(thread_key)
        if store is None:
            return None
        return store.as_retriever(search_type="similarity", search_kwargs={"k": top_k})

    def search(self, thread_id: str, query: str, top_k: int = 4) -> list[Document]:
        """Perform similarity search on documents in a thread."""
        retriever = self.get_retriever(thread_id, top_k=top_k)
        if retriever is None:
            return []
        results = retriever.invoke(query)
        return cast(list[Document], results)

    def get_metadata(self, thread_id: str) -> dict:
        """Return document metadata for a thread."""
        return self._metadata.get(str(thread_id), {})

    def has_document(self, thread_id: str) -> bool:
        """Check if an index exists for a thread."""
        return str(thread_id) in self._stores

    def delete_thread_index(self, thread_id: str) -> bool:
        """Evict thread vector store and metadata from memory."""
        thread_key = str(thread_id)
        removed_store = self._stores.pop(thread_key, None)
        self._metadata.pop(thread_key, None)
        return removed_store is not None

