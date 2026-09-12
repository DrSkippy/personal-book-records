import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

_tmp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
json.dump({
    "username": "user", "password": "pass", "database": "db",
    "host": "localhost", "port": 5432,
    "isbn_com": {"url_isbn": "https://example.com/{}", "key": "isbn-key"},
    "api_key": "test-key",
    "ai_agent": {
        "chat_host": "http://chat-host:1234",
        "chat_model": "test-model",
        "chat_api_key": "test-chat-key",
    },
}, _tmp_config)
_tmp_config.close()
os.environ.setdefault("BOOKDB_CONFIG", _tmp_config.name)

import psycopg2


class _UndefinedTableConn:
    """Stands in for a DB connection whose embedding_index_state table
    doesn't exist yet, so module-load-time freshness checks no-op."""
    def cursor(self):
        raise psycopg2.errors.UndefinedTable()

    def close(self):
        pass


with patch.object(psycopg2, "connect", return_value=_UndefinedTableConn()):
    import books.api as api


def _openai_response(content="", tool_calls=None):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}]}


class TestChatEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def test_requires_api_key(self):
        resp = self.client.post("/chat", json={"messages": []})
        self.assertEqual(resp.status_code, 401)

    def test_returns_503_when_chat_not_configured(self):
        with patch.object(api, "CHAT_HOST", None), patch.object(api, "CHAT_MODEL", None):
            resp = self.client.post(
                "/chat", headers={"x-api-key": "test-key"}, json={"messages": []}
            )
            self.assertEqual(resp.status_code, 503)

    @patch('booksdb.chat_util.requests.post')
    def test_simple_reply_roundtrip(self, mock_post):
        mock_post.return_value = Mock(
            json=Mock(return_value=_openai_response("Hello there!")),
            raise_for_status=Mock(),
        )
        resp = self.client.post(
            "/chat",
            headers={"x-api-key": "test-key"},
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertEqual(body["trace"], [{"type": "assistant", "content": "Hello there!"}])
        self.assertEqual(body["history"][-1], {"role": "assistant", "content": "Hello there!"})

    @patch('booksdb.chat_util.requests.post')
    def test_upstream_failure_returns_502(self, mock_post):
        import requests
        mock_post.side_effect = requests.ConnectionError("connection refused")
        resp = self.client.post(
            "/chat",
            headers={"x-api-key": "test-key"},
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
        self.assertEqual(resp.status_code, 502)
        self.assertIn("error", resp.get_json())


if __name__ == '__main__':
    unittest.main()
