import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

_tmp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
json.dump({
    "username": "user", "password": "pass", "database": "db",
    "host": "localhost", "port": 5432,
    "isbn_com": {"url_isbn": "https://example.com/{}", "key": "isbn-key"},
    "api_key": "test-key",
    # Must match test_chat_endpoint.py: whichever test module loads first wins
    # BOOKDB_CONFIG for the whole pytest session.
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

from books.isbn_com import Endpoint

HEADERS = {"x-api-key": "test-key"}


class TestEndpointToCollectionDb(unittest.TestCase):
    def setUp(self):
        self.ep = Endpoint({})

    def test_full_record(self):
        proto = self.ep._endpoint_to_collection_db({"book": {
            "title": "T", "authors": ["A", "B"], "isbn": "0123456789",
            "isbn13": "9780123456789", "publisher": "P", "pages": 100,
            "date_published": "1999-05-07T00:00:00",
        }})
        self.assertEqual(proto["Title"], "T")
        self.assertEqual(proto["Author"], "A")
        self.assertEqual(proto["Pages"], 100)
        self.assertEqual(proto["CopyrightDate"], "1999-05-07")

    def test_error_response_returns_none(self):
        self.assertIsNone(self.ep._endpoint_to_collection_db({"error": "404 Not Found"}))

    def test_missing_title_returns_none(self):
        self.assertIsNone(self.ep._endpoint_to_collection_db({"book": {"authors": ["A"]}}))

    def test_sparse_record_does_not_raise(self):
        proto = self.ep._endpoint_to_collection_db({"book": {"title": "T"}})
        self.assertEqual(proto["Author"], "")
        self.assertIsNone(proto["Pages"])
        self.assertIsNone(proto["CopyrightDate"])
        self.assertEqual(proto["PublisherName"], "unknown")

    def test_isbn13_in_isbn_field_yields_derived_isbn10(self):
        proto = self.ep._endpoint_to_collection_db({"book": {
            "title": "T", "isbn": "9780306406157", "isbn13": "9780306406157",
        }})
        self.assertEqual(proto["IsbnNumber"], "0306406152")
        self.assertEqual(proto["IsbnNumber13"], "9780306406157")

    def test_isbn10_field_preferred(self):
        proto = self.ep._endpoint_to_collection_db({"book": {
            "title": "T", "isbn": "9780306406157", "isbn10": "0306406152",
            "isbn13": "9780306406157",
        }})
        self.assertEqual(proto["IsbnNumber"], "0306406152")

    def test_979_prefix_has_no_isbn10(self):
        proto = self.ep._endpoint_to_collection_db({"book": {
            "title": "T", "isbn": "9791234567896", "isbn13": "9791234567896",
        }})
        self.assertEqual(proto["IsbnNumber"], "")

    def test_isbn13_to_isbn10(self):
        conv = Endpoint.isbn13_to_isbn10
        self.assertEqual(conv("9780306406157"), "0306406152")
        self.assertEqual(conv("978-0-8044-2957-3"), "080442957X")
        self.assertIsNone(conv("9791234567896"))
        self.assertIsNone(conv("0306406152"))
        self.assertIsNone(conv(None))

    def test_published_date_normalization(self):
        norm = Endpoint._normalize_published_date
        self.assertEqual(norm("1999"), "1999-01-01")
        self.assertEqual(norm(1999), "1999-01-01")
        self.assertEqual(norm("2001-05"), "2001-05-01")
        self.assertIsNone(norm("0000"))
        self.assertIsNone(norm("c1999"))
        self.assertIsNone(norm("1999-02-30"))
        self.assertIsNone(norm(None))


class TestBooksByIsbn(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    @patch("books.api.isbn.get_book_by_isbn")
    def test_failed_lookup_returns_empty_not_500(self, mock_get):
        mock_get.return_value = {"error": "404 Client Error: Not Found"}
        resp = self.client.post("/books_by_isbn", headers=HEADERS, json={"isbn_list": ["123"]})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["book_records"], [])

    @patch("books.api.isbn.get_book_by_isbn")
    def test_successful_lookup(self, mock_get):
        mock_get.return_value = {"book": {"title": "T", "authors": ["A"]}}
        resp = self.client.post("/books_by_isbn", headers=HEADERS, json={"isbn_list": ["123"]})
        self.assertEqual(resp.get_json()["book_records"][0]["Title"], "T")


class TestAddBooks(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()

    def test_bad_row_rolls_back_to_savepoint_and_reports_error(self):
        cursor = MagicMock()
        executed = []

        def execute(sql, params=None):
            executed.append(sql)
            if sql.startswith("INSERT") and params[0] == "Bad":
                raise psycopg2.DataError("date/time field value out of range")

        cursor.execute.side_effect = execute
        cursor.fetchone.return_value = (42,)
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value = cursor

        rows = [
            {"Title": "Bad", "Author": "A", "Location": "Main Collection", "CopyrightDate": "0000-01-01"},
            {"Title": "Good", "Author": "A", "Location": "Main Collection", "CopyrightDate": "1999"},
        ]
        with patch.object(api.psycopg2, "connect", return_value=conn):
            resp = self.client.post("/add_books", headers=HEADERS, json=rows)

        result = resp.get_json()["add_books"]
        self.assertIn("error", result[0])
        self.assertEqual(result[1]["BookId"], 42)
        self.assertIn("ROLLBACK TO SAVEPOINT add_book", executed)
        conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
