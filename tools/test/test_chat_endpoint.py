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


class TestDraftReadNoteEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.body = {"BookId": 7, "ReadDate": "2026-09-01", "observations": ["a", "b", "c"]}

    def post(self, body):
        return self.client.post("/draft_read_note", headers={"x-api-key": "test-key"}, json=body)

    def test_returns_draft(self):
        draft = {"BookId": 7, "ReadDate": "2026-09-01", "Title": "Dune", "draft": "Text"}
        with patch.object(api, "draft_read_note", return_value=draft) as fn:
            resp = self.post(self.body)
        fn.assert_called_once_with(7, "2026-09-01", ["a", "b", "c"])
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), draft)

    def test_missing_fields_400(self):
        resp = self.post({"BookId": 7, "ReadDate": "2026-09-01", "observations": "a"})
        self.assertEqual(resp.status_code, 400)

    def test_value_error_400(self):
        with patch.object(api, "draft_read_note", side_effect=ValueError("no read")):
            resp = self.post(self.body)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["error"], "no read")

    def test_upstream_failure_502(self):
        import requests
        with patch.object(api, "draft_read_note", side_effect=requests.ConnectionError("down")):
            resp = self.post(self.body)
        self.assertEqual(resp.status_code, 502)

    def test_not_configured_503(self):
        with patch.object(api, "CHAT_HOST", None):
            resp = self.post(self.body)
        self.assertEqual(resp.status_code, 503)


class TestUpdateEditReadNoteEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def post(self, body):
        return self.client.post("/update_edit_read_note", headers={"x-api-key": "test-key"}, json=body)

    def test_updates_note(self):
        body = {"BookId": 7, "ReadDate": "2026-09-01", "ReadNote": "Review"}
        with patch.object(api, "update_read_note", return_value=(1, None)) as fn:
            resp = self.post(body)
        fn.assert_called_once_with(7, "2026-09-01", "Review")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json(), {"update_read": [body]})

    def test_no_matching_read_404(self):
        with patch.object(api, "update_read_note", return_value=(0, None)):
            resp = self.post({"BookId": 7, "ReadDate": "1999-01-01", "ReadNote": "x"})
        self.assertEqual(resp.status_code, 404)

    def test_missing_fields_400(self):
        resp = self.post({"BookId": 7, "ReadNote": "x"})
        self.assertEqual(resp.status_code, 400)


class TestUpdateReadNoteUtil(unittest.TestCase):
    def _conn(self, rowcount):
        cursor = Mock(rowcount=rowcount)
        conn = Mock()
        conn.cursor.return_value.__enter__ = Mock(return_value=cursor)
        conn.cursor.return_value.__exit__ = Mock(return_value=False)
        return conn, cursor

    def test_updates_and_reembeds(self):
        from booksdb import api_util
        conn, cursor = self._conn(1)
        with patch.object(api_util.psycopg2, "connect", return_value=conn), \
                patch.object(api_util, "upsert_read_note_embedding") as embed:
            self.assertEqual(api_util.update_read_note(7, "2026-09-01", " Review "), (1, None))
        cursor.execute.assert_called_once()
        self.assertEqual(cursor.execute.call_args.args[1], (" Review ", 7, "2026-09-01"))
        conn.commit.assert_called_once()
        embed.assert_called_once_with(conn, 7, "2026-09-01", "Review")

    def test_no_matching_read_skips_embedding(self):
        from booksdb import api_util
        conn, _ = self._conn(0)
        with patch.object(api_util.psycopg2, "connect", return_value=conn), \
                patch.object(api_util, "upsert_read_note_embedding") as embed:
            self.assertEqual(api_util.update_read_note(7, "1999-01-01", "Review"), (0, None))
        embed.assert_not_called()


if __name__ == '__main__':
    unittest.main()
