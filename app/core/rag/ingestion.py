"""Document ingestion and chunking pipeline."""

from __future__ import annotations

import os
import tempfile
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentIngestionService:
    """Handles parsing, validation, and chunking of uploaded documents."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    def parse_pdf(self, file_bytes: bytes, filename: str) -> Tuple[List[Document], dict]:
        """
        Parse raw PDF bytes into chunked documents with enriched metadata.

        Returns:
            Tuple of (chunked_documents, summary_metadata)
        """
        if not file_bytes:
            raise ValueError("Cannot ingest empty file bytes.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            loader = PyPDFLoader(tmp_path)
            raw_docs = loader.load()

            if not raw_docs:
                raise ValueError("PDF document contains no readable text pages.")

            # Enrich metadata before splitting
            for doc in raw_docs:
                doc.metadata["filename"] = filename

            chunks = self.splitter.split_documents(raw_docs)

            # Assign chunk indices for traceability
            for idx, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = idx

            summary = {
                "filename": filename,
                "documents": len(raw_docs),
                "chunks": len(chunks),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }

            return chunks, summary

        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

