"""Backward-compatibility shim redirecting to the modern app package."""

from app.core.agent import get_chatbot, get_namebot
from app.core.db.repository import ThreadRepository
from app.core.rag import get_rag_service

# Legacy singletons and exports
chatbot = get_chatbot()
namebot = get_namebot()
_rag = get_rag_service()
_repo = ThreadRepository()


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: str | None = None) -> dict:
    """Legacy wrapper for PDF ingestion."""
    return _rag.ingest_pdf(thread_id=thread_id, file_bytes=file_bytes, filename=filename or "document.pdf")


def retrieve_all_threads() -> dict[str, str]:
    """Legacy wrapper for fetching all thread titles."""
    return _repo.list_threads()


def get_name(thread_id: str) -> str | None:
    """Legacy wrapper for retrieving a single thread title."""
    return _repo.get_thread_name(thread_id)


def thread_has_document(thread_id: str) -> bool:
    """Legacy wrapper for checking if a document is attached."""
    return _rag.has_document(thread_id)


def thread_document_metadata(thread_id: str) -> dict:
    """Legacy wrapper for retrieving document metadata."""
    return _rag.get_document_metadata(thread_id)


if __name__ == "__main__":
    print("All threads:", retrieve_all_threads())
