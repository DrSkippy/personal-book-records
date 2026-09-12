import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

# booksdb.config reads configuration.json at import time; point it at a
# throwaway file before importing booksdb.api_util (mirrors test_config.py).
_tmp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
json.dump({
    "username": "user", "password": "pass", "database": "db",
    "host": "localhost", "port": 5432,
    "isbn_com": {"url_isbn": "https://example.com/{}", "key": "isbn-key"},
    "api_key": "file-api-key",
}, _tmp_config)
_tmp_config.close()
os.environ.setdefault("BOOKDB_CONFIG", _tmp_config.name)

from booksdb import api_util


def _mock_conn(fetchone_return=None):
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn, cursor


class TestGetEmbeddingIndexState(unittest.TestCase):
    def test_returns_none_when_no_row(self):
        conn, _ = _mock_conn(fetchone_return=None)
        self.assertIsNone(api_util.get_embedding_index_state(conn))

    def test_returns_state_dict_when_row_present(self):
        conn, _ = _mock_conn(fetchone_return=("http://host:1234", "model-a", 768, "2026-09-11"))
        state = api_util.get_embedding_index_state(conn)
        self.assertEqual(state, {
            "embed_host": "http://host:1234",
            "embed_model": "model-a",
            "embed_dimensions": 768,
            "updated_at": "2026-09-11",
        })


class TestSetEmbeddingIndexState(unittest.TestCase):
    def test_executes_upsert_and_commits(self):
        conn, cursor = _mock_conn()
        api_util.set_embedding_index_state(conn, "http://host:1234", "model-a", 768)
        cursor.execute.assert_called_once()
        args = cursor.execute.call_args[0][1]
        self.assertEqual(args, ("http://host:1234", "model-a", 768))
        conn.commit.assert_called_once()


class TestCheckEmbeddingIndexFreshness(unittest.TestCase):
    def test_noop_when_embeddings_not_configured(self):
        with patch.object(api_util, "EMBED_HOST", None), \
             patch.object(api_util, "EMBED_MODEL", None), \
             patch.object(api_util, "psycopg2") as mock_psycopg2:
            api_util.check_embedding_index_freshness()
            mock_psycopg2.connect.assert_not_called()

    def test_noop_when_no_state_row_yet(self):
        conn, _ = _mock_conn(fetchone_return=None)
        with patch.object(api_util, "EMBED_HOST", "http://host:1234"), \
             patch.object(api_util, "EMBED_MODEL", "model-a"), \
             patch.object(api_util, "EMBED_DIMENSIONS", 768), \
             patch.object(api_util.psycopg2, "connect", return_value=conn):
            api_util.check_embedding_index_freshness()  # should not raise

    def test_noop_when_state_matches_config(self):
        conn, _ = _mock_conn(fetchone_return=("http://host:1234", "model-a", 768, "2026-09-11"))
        with patch.object(api_util, "EMBED_HOST", "http://host:1234"), \
             patch.object(api_util, "EMBED_MODEL", "model-a"), \
             patch.object(api_util, "EMBED_DIMENSIONS", 768), \
             patch.object(api_util.psycopg2, "connect", return_value=conn):
            api_util.check_embedding_index_freshness()  # should not raise

    def test_exits_when_model_changed(self):
        conn, _ = _mock_conn(fetchone_return=("http://host:1234", "old-model", 768, "2026-09-11"))
        with patch.object(api_util, "EMBED_HOST", "http://host:1234"), \
             patch.object(api_util, "EMBED_MODEL", "new-model"), \
             patch.object(api_util, "EMBED_DIMENSIONS", 768), \
             patch.object(api_util.psycopg2, "connect", return_value=conn):
            with self.assertRaises(SystemExit) as ctx:
                api_util.check_embedding_index_freshness()
            self.assertIn("old-model", str(ctx.exception))
            self.assertIn("new-model", str(ctx.exception))
            self.assertIn("index_notes.py --rebuild", str(ctx.exception))

    def test_exits_when_host_changed(self):
        conn, _ = _mock_conn(fetchone_return=("http://old-host:1234", "model-a", 768, "2026-09-11"))
        with patch.object(api_util, "EMBED_HOST", "http://new-host:1234"), \
             patch.object(api_util, "EMBED_MODEL", "model-a"), \
             patch.object(api_util, "EMBED_DIMENSIONS", 768), \
             patch.object(api_util.psycopg2, "connect", return_value=conn):
            with self.assertRaises(SystemExit):
                api_util.check_embedding_index_freshness()

    def test_noop_on_undefined_table(self):
        conn, cursor = _mock_conn()
        cursor.execute.side_effect = api_util.psycopg2.errors.UndefinedTable()
        with patch.object(api_util, "EMBED_HOST", "http://host:1234"), \
             patch.object(api_util, "EMBED_MODEL", "model-a"), \
             patch.object(api_util.psycopg2, "connect", return_value=conn):
            api_util.check_embedding_index_freshness()  # should not raise


if __name__ == '__main__':
    unittest.main()
