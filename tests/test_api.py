"""Integration tests for FastAPI endpoints."""

import io
import unittest

from starlette.testclient import TestClient

from app.core.config import get_settings
from app.core.db.repository import ThreadRepository
from app.core.security import validate_pdf_content
from app.main import app


class TestAPIEndpoints(unittest.TestCase):
    """Test suite verifying core REST endpoints and security guardrails."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.repo = ThreadRepository()

    def test_health(self):
        """Verify health endpoint returns status healthy."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("version", data)

    def test_threads_lifecycle(self):
        """Test creating, reading, and deleting a thread via repository and API."""
        test_id = "test-session-999"
        self.repo.upsert_thread(test_id, "Test Discussion")

        # Fetch through API
        resp = self.client.get(f"/api/v1/threads/{test_id}")
        self.assertEqual(resp.status_code, 200)
        detail = resp.json()
        self.assertEqual(detail["thread_id"], test_id)
        self.assertEqual(detail["chat_name"], "Test Discussion")

        # Delete through API
        del_resp = self.client.delete(f"/api/v1/threads/{test_id}")
        self.assertEqual(del_resp.status_code, 200)
        self.assertTrue(del_resp.json()["deleted"])

    def test_document_metadata_not_found(self):
        """Verify 404 is returned when querying metadata for a thread with no documents."""
        resp = self.client.get("/api/v1/documents/non-existent-thread")
        self.assertEqual(resp.status_code, 404)

    def test_fake_pdf_magic_bytes_rejected(self):
        """Security Guardrail: Disguised text file must be rejected even with a .pdf extension."""
        fake_pdf = io.BytesIO(b"This is purely plain text masquerading as a PDF.")
        resp = self.client.post(
            "/api/v1/documents/upload",
            data={"thread_id": "test-sec-thread"},
            files={"file": ("malicious.pdf", fake_pdf, "application/pdf")},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Invalid file signature", resp.json()["detail"])

    def test_pdf_magic_bytes_validator(self):
        """Unit test for PDF magic byte validator."""
        self.assertTrue(validate_pdf_content(b"%PDF-1.7\nSome stream content..."))
        self.assertFalse(validate_pdf_content(b"<html><body>Not a PDF</body></html>"))
        self.assertFalse(validate_pdf_content(b""))

    def test_oversized_prompt_rejected(self):
        """Security Guardrail: Oversized prompts must be rejected to prevent denial of wallet."""
        settings = get_settings()
        huge_prompt = "A" * (settings.MAX_PROMPT_LENGTH + 100)
        resp = self.client.post(
            "/api/v1/chat",
            json={"message": huge_prompt, "thread_id": "test-sec-thread"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("exceeds maximum permitted length", resp.json()["detail"])


if __name__ == "__main__":
    unittest.main()
