import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bookdbtool.book_db_tools import BCTool
import pandas as pd


class TestBCTool(unittest.TestCase):

    def setUp(self):
        self.endpoint = "http://test-endpoint.com"
        self.api_key = "test-api-key"
        self.bc_tool = BCTool(self.endpoint, self.api_key)

    def test_init(self):
        self.assertEqual(self.bc_tool.end_point, self.endpoint)
        self.assertEqual(self.bc_tool.header, {"x-api-key": self.api_key})
        self.assertIsNone(self.bc_tool.result)

    def test_column_index_constants(self):
        self.assertEqual(BCTool.COLUMN_INDEX["BookId"], 0)
        self.assertEqual(BCTool.COLUMN_INDEX["Title"], 1)
        self.assertEqual(BCTool.COLUMN_INDEX["Author"], 2)
        self.assertIn("BookNote", BCTool.COLUMN_INDEX)

    def test_row_column_selector(self):
        row = [1, 2, 3, 4, 5]
        indexes = [0, 2, 4]
        result = self.bc_tool._row_column_selector(row, indexes)
        self.assertEqual(result, [1, 3, 5])

    def test_column_selector(self):
        data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        indexes = [0, 2]
        result = self.bc_tool._column_selector(data, indexes)
        self.assertEqual(result, [[1, 3], [4, 6], [7, 9]])

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_version_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.bc_tool.version()
            output = fake_out.getvalue()
            self.assertIn("1.0.0", output)
            self.assertIn(self.endpoint, output)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_version_request_exception(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        with patch('bookdbtool.book_db_tools.logging.error') as mock_log:
            self.bc_tool.version()
            mock_log.assert_called_once()

    def test_columns(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.bc_tool.columns()
            output = fake_out.getvalue()
            self.assertIn("BookId", output)
            self.assertIn("Title", output)
            self.assertIn("Author", output)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_tag_counts_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [["fiction", 10], ["science", 5]],
            "header": ["Tag", "Count"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.tag_counts(tag="fiction", pagination=False)
            self.assertIsInstance(self.bc_tool.result, pd.DataFrame)
            self.assertEqual(len(self.bc_tool.result), 2)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_tag_counts_with_tag(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [["fiction", 10]],
            "header": ["Tag", "Count"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.tag_counts(tag="fiction", pagination=False)
            mock_get.assert_called_once()
            call_url = mock_get.call_args[0][0]
            self.assertIn("/tag_counts/fiction", call_url)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_books_search_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "Test Book", "Test Author", 2020, "123456", "Publisher", "Hard", 300]],
            "header": ["ID", "Title", "Author", "Year", "ISBN", "Publisher", "Cover", "Pages"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.books_search(Title="Test", Author="Author")
            self.assertIsInstance(self.bc_tool.result, pd.DataFrame)
            call_url = mock_get.call_args[0][0]
            self.assertIn("Title=Test", call_url)
            self.assertIn("Author=Author", call_url)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_tags_search_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "fiction", "Book 1"], [2, "fiction", "Book 2"]],
            "header": ["BookId", "Tag", "Title"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.tags_search("fiction", pagination=False)
            self.assertEqual(self.bc_tool.result, {1, 2})

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_book_success(self, mock_get):
        # The book() method now uses /complete_record endpoint with different response structure
        mock_response = Mock()
        mock_response.json.return_value = {
            "book": {
                "data": [[1, "Test Book", "Test Author", 2020, "123456", "Publisher", "Hard", 300]],
                "header": ["ID", "Title", "Author", "Year", "ISBN", "Publisher", "Cover", "Pages"]
            },
            "tags": {
                "data": [["fiction", "classic"]],
                "header": ["Tags"]
            },
            "reads": {
                "data": [[["2024-01-01", "Finished"]]],
                "header": ["ReadDate", "Status"]
            }
        }

        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            with patch('sys.stdout', new=StringIO()):
                self.bc_tool.book(1, pagination=False)
                self.assertEqual(self.bc_tool.result, 1)

    def test_book_invalid_id(self):
        # The book() method now catches ValueError and prints a message instead of raising
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = self.bc_tool.book("not_an_int")
            output = fake_out.getvalue()
            self.assertIn("Requires in integer Book ID", output)
            self.assertIsNone(result)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_books_read_by_year_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "Book 1", "Author 1", 2020, "123", "Publisher", "Hard", 300]],
            "header": ["ID", "Title", "Author", "Year", "ISBN", "Publisher", "Cover", "Pages"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.books_read_by_year(2020, pagination=False)
            self.assertIsInstance(self.bc_tool.result, pd.DataFrame)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_summary_books_read_by_year_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[2020, 5000, 20], [2021, 6000, 25]],
            "header": ["year", "pages read", "books read"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.summary_books_read_by_year(pagination=False)
            self.assertIsInstance(self.bc_tool.result, pd.DataFrame)
            self.assertEqual(len(self.bc_tool.result), 2)

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_summary_books_read_by_year_no_show(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[2020, 5000, 20]],
            "header": ["year", "pages read", "books read"]
        }
        mock_get.return_value = mock_response

        self.bc_tool.summary_books_read_by_year(show=False, pagination=False)
        self.assertIsInstance(self.bc_tool.result, pd.DataFrame)

    def test_year_rank_with_pages(self):
        df = pd.DataFrame({
            "year": [2020, 2021, 2022],
            "pages read": [5000, 6000, 4000],
            "books read": [20, 25, 15]
        })

        with patch('sys.stdout', new=StringIO()):
            self.bc_tool.year_rank(df, pages=True)
            self.assertEqual(self.bc_tool.result.iloc[0]["pages read"], 6000)

    def test_year_rank_with_books(self):
        df = pd.DataFrame({
            "year": [2020, 2021, 2022],
            "pages read": [5000, 6000, 4000],
            "books read": [20, 25, 15]
        })

        with patch('sys.stdout', new=StringIO()):
            self.bc_tool.year_rank(df, pages=False)
            self.assertEqual(self.bc_tool.result.iloc[0]["books read"], 25)

    @patch('bookdbtool.book_db_tools.requests.post')
    def test_add_books_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "add_books": [{"BookId": 1}, {"BookId": 2}]
        }
        mock_post.return_value = mock_response

        records = [{"Title": "Book 1"}, {"Title": "Book 2"}]
        result = self.bc_tool._add_books(records)

        self.assertEqual(result, "Added.")
        self.assertEqual(self.bc_tool.result, [1, 2])

    @patch('bookdbtool.book_db_tools.requests.post')
    def test_add_books_request_exception(self, mock_post):
        import requests
        mock_post.side_effect = requests.RequestException("Connection error")

        records = [{"Title": "Book 1"}]
        result = self.bc_tool._add_books(records)

        self.assertIn("errors", result)

    @patch('bookdbtool.book_db_tools.requests.put')
    def test_add_tags_success(self, mock_put):
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_put.return_value = mock_response

        with patch('sys.stdout', new=StringIO()):
            self.bc_tool.add_tags(1, tags=["fiction", "classic"])
            self.assertEqual(self.bc_tool.result, 1)

    @patch('bookdbtool.book_db_tools.requests.put')
    def test_add_tags_with_error(self, mock_put):
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Tag already exists"}
        mock_put.return_value = mock_response

        with patch('sys.stdout', new=StringIO()):
            self.bc_tool.add_tags(1, tags=["fiction"])
            self.assertEqual(self.bc_tool.result, 1)

    def test_add_tags_invalid_id(self):
        with self.assertRaises(AssertionError):
            self.bc_tool.add_tags("not_an_int", tags=["fiction"])

    @patch('bookdbtool.book_db_tools.requests.get')
    def test_update_tag_value_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "new_tag", "Book 1"]],
            "header": ["BookId", "Tag", "Title"]
        }
        mock_get.return_value = mock_response

        with patch.object(self.bc_tool, '_show_table'):
            self.bc_tool.update_tag_value("old_tag", "new_tag", pagination=False)
            self.assertIsInstance(self.bc_tool.result, pd.DataFrame)

    def test_inputer_basic(self):
        proto = {"Title": "Test", "Author": "Author"}

        with patch('builtins.input', side_effect=["a", "a", "a"]):
            result = self.bc_tool._inputer(proto)
            self.assertEqual(result, proto)

    def test_populate_add_read_date(self):
        # _inputer needs: input for ReadDate, input for ReadNote, then 'a' to accept
        with patch('builtins.input', side_effect=["a", "a", "a"]):
            result = self.bc_tool._populate_add_read_date(1)
            self.assertEqual(result["BookId"], 1)
            self.assertIn("ReadDate", result)
            self.assertIn("ReadNote", result)


class TestBCToolAliases(unittest.TestCase):

    def setUp(self):
        self.bc_tool = BCTool("http://test.com", "test-key")

    def test_ver_alias(self):
        self.assertEqual(self.bc_tool.ver, self.bc_tool.version)

    def test_col_alias(self):
        self.assertEqual(self.bc_tool.col, self.bc_tool.columns)

    def test_tc_alias(self):
        self.assertEqual(self.bc_tool.tc, self.bc_tool.tag_counts)

    def test_bs_alias(self):
        self.assertEqual(self.bc_tool.bs, self.bc_tool.books_search)

    def test_ts_alias(self):
        self.assertEqual(self.bc_tool.ts, self.bc_tool.tags_search)

    def test_brys_alias(self):
        self.assertEqual(self.bc_tool.brys, self.bc_tool.books_read_by_year_with_summary)

    def test_bry_alias(self):
        self.assertEqual(self.bc_tool.bry, self.bc_tool.books_read_by_year)

    def test_sbry_alias(self):
        self.assertEqual(self.bc_tool.sbry, self.bc_tool.summary_books_read_by_year)

    def test_ab_alias(self):
        self.assertEqual(self.bc_tool.ab, self.bc_tool.add_books)

    def test_abi_alias(self):
        self.assertEqual(self.bc_tool.abi, self.bc_tool.add_books_by_isbn)

    def test_arb_alias(self):
        self.assertEqual(self.bc_tool.arb, self.bc_tool.add_read_books)

    def test_at_alias(self):
        self.assertEqual(self.bc_tool.at, self.bc_tool.add_tags)


if __name__ == '__main__':
    unittest.main()
