"""Streamlit UI client decoupled from backend via REST & SSE APIs."""

from __future__ import annotations

import json
import os
import uuid
import httpx
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api/v1")

st.set_page_config(
    page_title="Enterprise AI Chatbot",
    page_icon="🤖",
    layout="wide",
)


# -------------------------------------------------------------
# API Client Helper Functions
# -------------------------------------------------------------

def check_backend_health() -> bool:
    """Verify backend connectivity."""
    try:
        resp = httpx.get(f"{BACKEND_URL.replace('/api/v1', '')}/health", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


def fetch_all_threads() -> dict[str, str]:
    """Retrieve all conversations from the backend."""
    try:
        resp = httpx.get(f"{BACKEND_URL}/threads", timeout=5.0)
        if resp.status_code == 200:
            threads_list = resp.json()
            return {t["thread_id"]: t["chat_name"] for t in threads_list}
    except Exception as exc:
        st.sidebar.error(f"Failed to fetch threads: {exc}")
    return {}


def load_conversation(thread_id: str) -> dict:
    """Load chat history and document metadata for a thread."""
    try:
        resp = httpx.get(f"{BACKEND_URL}/threads/{thread_id}", timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception as exc:
        st.error(f"Failed to load conversation: {exc}")
    return {"messages": [], "document_metadata": None}


def upload_document_to_backend(thread_id: str, file_name: str, file_bytes: bytes) -> dict | None:
    """Upload PDF to backend for indexing."""
    try:
        files = {"file": (file_name, file_bytes, "application/pdf")}
        data = {"thread_id": thread_id}
        resp = httpx.post(f"{BACKEND_URL}/documents/upload", data=data, files=files, timeout=60.0)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.sidebar.error(f"Upload failed: {resp.text}")
    except Exception as exc:
        st.sidebar.error(f"Upload error: {exc}")
    return None


def delete_thread_from_backend(thread_id: str) -> bool:
    """Delete a thread from backend."""
    try:
        resp = httpx.delete(f"{BACKEND_URL}/threads/{thread_id}", timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False


# -------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = str(uuid.uuid4())

if "message_hist" not in st.session_state:
    st.session_state["message_hist"] = []

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = fetch_all_threads()

if "doc_meta" not in st.session_state:
    st.session_state["doc_meta"] = None


def reset_chat():
    """Start a fresh conversation thread."""
    new_id = str(uuid.uuid4())
    st.session_state["thread_id"] = new_id
    st.session_state["message_hist"] = []
    st.session_state["doc_meta"] = None
    st.session_state["chat_threads"][new_id] = "New Chat"


# Ensure current thread exists in thread tracking
current_thread_id = st.session_state["thread_id"]
if current_thread_id not in st.session_state["chat_threads"]:
    st.session_state["chat_threads"][current_thread_id] = "New Chat"


# -------------------------------------------------------------
# Sidebar: Connection, Documents & Conversations
# -------------------------------------------------------------

st.sidebar.title("🤖 Enterprise Chatbot")

# Backend Health Indicator
backend_online = check_backend_health()
if backend_online:
    st.sidebar.caption("🟢 **Backend API:** Connected")
else:
    st.sidebar.error(
        "🔴 **Backend API Offline**\n\n"
        "Start the backend server with:\n"
        "`uvicorn app.main:app --reload`"
    )

if st.sidebar.button("➕ New Chat", use_container_width=True):
    reset_chat()
    st.rerun()

st.sidebar.divider()

# Document Upload Section
st.sidebar.subheader("📄 Document RAG")
if st.session_state["doc_meta"]:
    meta = st.session_state["doc_meta"]
    st.sidebar.success(
        f"**Indexed:** `{meta.get('filename')}`\n\n"
        f"• Chunks: {meta.get('chunks')}\n"
        f"• Pages: {meta.get('documents')}"
    )
else:
    st.sidebar.info("No document attached to this chat.")

uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF for this conversation",
    type=["pdf"],
    key=f"uploader_{current_thread_id}",
)

if uploaded_file and backend_online:
    existing_file = (
        st.session_state["doc_meta"].get("filename") if st.session_state["doc_meta"] else None
    )
    if uploaded_file.name != existing_file:
        with st.sidebar.status("Indexing PDF with embeddings…", expanded=True) as status_box:
            summary = upload_document_to_backend(
                thread_id=current_thread_id,
                file_name=uploaded_file.name,
                file_bytes=uploaded_file.getvalue(),
            )
            if summary:
                st.session_state["doc_meta"] = summary
                status_box.update(label="✅ Document Indexed", state="complete", expanded=False)
                st.rerun()

st.sidebar.divider()

# Conversation History List
st.sidebar.subheader("💬 Past Conversations")
threads_dict = fetch_all_threads()
if threads_dict:
    st.session_state["chat_threads"] = threads_dict

sorted_threads = list(st.session_state["chat_threads"].items())[::-1]

for tid, tname in sorted_threads:
    col1, col2 = st.sidebar.columns([0.8, 0.2])
    is_active = tid == current_thread_id
    button_label = f"👉 {tname}" if is_active else tname

    if col1.button(button_label, key=f"thread_btn_{tid}", use_container_width=True):
        st.session_state["thread_id"] = tid
        details = load_conversation(tid)
        st.session_state["message_hist"] = details.get("messages", [])
        st.session_state["doc_meta"] = details.get("document_metadata")
        st.rerun()

    if col2.button("🗑️", key=f"del_btn_{tid}", help="Delete chat"):
        delete_thread_from_backend(tid)
        st.session_state["chat_threads"].pop(tid, None)
        if tid == current_thread_id:
            reset_chat()
        st.rerun()


# -------------------------------------------------------------
# Main Chat Area
# -------------------------------------------------------------

current_title = st.session_state["chat_threads"].get(current_thread_id, "New Chat")
st.header(current_title)

# Render Chat History
for message in st.session_state["message_hist"]:
    role = message.get("role", "user")
    content = message.get("content", "")
    with st.chat_message(role):
        st.markdown(content)


# Handle User Prompt
user_prompt = st.chat_input("Type your message here...", disabled=not backend_online)

if user_prompt:
    # Append & display user message
    st.session_state["message_hist"].append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Stream assistant response via SSE
    with st.chat_message("assistant"):
        status_holder = {"box": None}
        meta_holder = {"title": None}

        def stream_response_generator():
            url = f"{BACKEND_URL}/chat/stream"
            payload = {"message": user_prompt, "thread_id": current_thread_id}

            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", url, json=payload) as response:
                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        raw_data = line[6:].strip()
                        try:
                            event = json.loads(raw_data)
                        except json.JSONDecodeError:
                            continue

                        event_type = event.get("event")

                        if event_type == "tool_start":
                            tool_name = event.get("tool", "tool")
                            if status_holder["box"] is None:
                                status_holder["box"] = st.status(
                                    f"🔧 Using `{tool_name}`…", expanded=True
                                )
                            else:
                                status_holder["box"].update(
                                    label=f"🔧 Using `{tool_name}`…",
                                    state="running",
                                    expanded=True,
                                )

                        elif event_type == "tool_complete":
                            tool_name = event.get("tool", "tool")
                            if status_holder["box"] is not None:
                                status_holder["box"].update(
                                    label=f"✅ `{tool_name}` complete",
                                    state="running",
                                    expanded=False,
                                )

                        elif event_type == "token":
                            yield event.get("text", "")

                        elif event_type == "done":
                            meta_holder["title"] = event.get("title")

                        elif event_type == "error":
                            st.error(f"Error: {event.get('detail')}")

        ai_message_text = st.write_stream(stream_response_generator())

        if status_holder["box"] is not None:
            status_holder["box"].update(label="✅ Ready", state="complete", expanded=False)

    # Save to session message history
    st.session_state["message_hist"].append({"role": "assistant", "content": ai_message_text})

    # Update thread title if auto-named
    new_title = meta_holder["title"]
    if new_title and new_title != st.session_state["chat_threads"].get(current_thread_id):
        st.session_state["chat_threads"][current_thread_id] = new_title
        st.rerun()
