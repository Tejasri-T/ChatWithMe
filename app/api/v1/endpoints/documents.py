"""Document upload and indexing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.v1.schemas import DocumentSummaryResponse
from app.core.config import get_settings
from app.core.rag import get_rag_service
from app.core.security import rate_limit_dependency, validate_pdf_content, verify_api_key

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    dependencies=[Depends(verify_api_key), Depends(rate_limit_dependency)],
)


@router.post("/upload", response_model=DocumentSummaryResponse)
async def upload_document(
    thread_id: str = Form(..., description="Thread ID to attach the document to"),
    file: UploadFile = File(..., description="PDF document file"),
):
    """
    Upload and index a PDF document into the thread-scoped vector store.
    Enforces format checking, magic byte inspection, and size limits.
    """
    settings = get_settings()
    filename = file.filename or "uploaded.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Only PDF files (.pdf) are currently supported.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    if not validate_pdf_content(content):
        raise HTTPException(
            status_code=400,
            detail="Invalid file signature: Content is not a legitimate PDF document.",
        )

    rag = get_rag_service()
    try:
        summary = rag.ingest_pdf(
            thread_id=thread_id,
            file_bytes=content,
            filename=filename,
        )
        return DocumentSummaryResponse(
            filename=summary["filename"],
            documents=summary["documents"],
            chunks=summary["chunks"],
            thread_id=thread_id,
            chunk_size=summary["chunk_size"],
            chunk_overlap=summary["chunk_overlap"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(exc)}")


@router.get("/{thread_id}")
async def get_document_info(thread_id: str):
    """Fetch metadata for documents indexed under the specified thread."""
    rag = get_rag_service()
    meta = rag.get_document_metadata(thread_id)
    if not meta:
        raise HTTPException(status_code=404, detail="No document found for this thread.")
    return meta

