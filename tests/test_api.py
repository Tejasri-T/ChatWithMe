"""Integration tests for FastAPI endpoints."""

import unittest
from starlette.testclient import TestClient

from app.main import app
from app.core.db.repository import ThreadRepository


class TestAPIEndpoints(unittest.TestCase):
    """Test suite verifying core REST endpoints."""

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


if __name__ == "__main__":
    unittest.main()
