# Enterprise AI Chatbot Platform

A production-grade, multi-tenant conversational AI and RAG (Retrieval-Augmented Generation) platform powered by **LangGraph**, **FastAPI**, **Google Gemini**, and **PostgreSQL**.

---

## 🏛️ Architecture Overview

The system is designed with a decoupled client-server architecture:

- **API Layer (`app/api`):** Asynchronous FastAPI gateway providing REST and Server-Sent Events (SSE) streaming.
- **Agent Core (`app/core/agent`):** LangGraph state graph managing conversational turns, routing, memory checkpoints, and tool executions.
- **RAG & Vector Retrieval (`app/core/rag`):** Advanced document ingestion pipeline, semantic embeddings, and persistent vector database indexing.
- **State & Checkpointing:** PostgreSQL-backed checkpointing (`PostgresSaver`) for conversation memory across server restarts.
- **Observability:** Distributed tracing and cost monitoring via Langfuse.

---

## 🚀 Quickstart

### 1. Environment Setup

Clone the repository and set up a Python virtual environment:

```powershell
# Create virtual environment
python -m venv .venv

# Activate environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```powershell
cp .env.example .env
```

Required variables:
- `GOOGLE_API_KEY`: Google Gemini API key.
- `DATABASE_URL`: Connection string for PostgreSQL (or SQLite for local dev).

### 3. Run the Development Server

```powershell
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Testing & Code Quality

```powershell
# Run unit & integration tests
pytest

# Code linting
ruff check .

# Static type checking
mypy app
```

