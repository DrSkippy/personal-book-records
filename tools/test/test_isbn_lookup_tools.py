import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bookdbtool.isbn_lookup_tools import ISBNLookup


class TestISBNLookup(unittest.TestCase):

    def setUp(self):
        self.config = {
            "key": "test-api-key",
            "url_isbn": "http://api.test.com/isbn/{}"
        }
        self.isbn_lookup = ISBNLookup(self.config)

    def test_init(self):
        self.assertEqual(self.isbn_lookup.config, self.config)
        self.assertIsNone(self.isbn_lookup.result)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_single_isbn(self, mock_pprint, mock_get):
        isbn = "9780123456789"

        mock_response = Mock()
        mock_response.json.return_value = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": isbn
        }
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()):
            self.isbn_lookup.lookup(isbn)

        expected_url = self.config["url_isbn"].format(isbn)
        expected_headers = {'Authorization': self.config["key"]}
        mock_get.assert_called_once_with(expected_url, headers=expected_headers)

        self.assertEqual(self.isbn_lookup.result, mock_response.json.return_value)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_list_of_isbns(self, mock_pprint, mock_get):
        isbns = ["9780123456789", "9780987654321"]

        mock_response_1 = Mock()
        mock_response_1.json.return_value = {
            "title": "Book 1",
            "isbn": isbns[0]
        }

        mock_response_2 = Mock()
        mock_response_2.json.return_value = {
            "title": "Book 2",
            "isbn": isbns[1]
        }

        mock_get.side_effect = [mock_response_1, mock_response_2]

        with patch('builtins.input', return_value=''):
            self.isbn_lookup.lookup(isbns)

        self.assertEqual(len(mock_get.call_args_list), 2)

        self.assertIsInstance(self.isbn_lookup.result, dict)
        self.assertIn(isbns[0], self.isbn_lookup.result)
        self.assertIn(isbns[1], self.isbn_lookup.result)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_list_quit_early(self, mock_pprint, mock_get):
        isbns = ["9780123456789", "9780987654321", "9781234567890"]

        mock_response_1 = Mock()
        mock_response_1.json.return_value = {"title": "Book 1"}

        mock_response_2 = Mock()
        mock_response_2.json.return_value = {"title": "Book 2"}

        mock_get.side_effect = [mock_response_1, mock_response_2]

        with patch('builtins.input', side_effect=['', 'q']):
            self.isbn_lookup.lookup(isbns)

        self.assertEqual(len(mock_get.call_args_list), 2)

        self.assertIn(isbns[0], self.isbn_lookup.result)
        self.assertIn(isbns[1], self.isbn_lookup.result)
        self.assertNotIn(isbns[2], self.isbn_lookup.result)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_none_isbn(self, mock_pprint, mock_get):
        self.isbn_lookup.lookup(None)

        mock_get.assert_not_called()

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_empty_list(self, mock_pprint, mock_get):
        self.isbn_lookup.lookup([])

        mock_get.assert_not_called()
        self.assertEqual(self.isbn_lookup.result, {})

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_api_error(self, mock_pprint, mock_get):
        isbn = "9780123456789"

        mock_get.side_effect = Exception("API Error")

        with self.assertRaises(Exception):
            self.isbn_lookup.lookup(isbn)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_private_lookup_method(self, mock_pprint, mock_get):
        isbn = "9780123456789"

        mock_response = Mock()
        mock_response.json.return_value = {
            "title": "Test Book",
            "isbn": isbn
        }
        mock_get.return_value = mock_response

        self.isbn_lookup._lookup(isbn)

        expected_url = self.config["url_isbn"].format(isbn)
        mock_get.assert_called_once_with(
            expected_url,
            headers={'Authorization': self.config["key"]}
        )

        self.assertEqual(self.isbn_lookup.result, mock_response.json.return_value)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_with_detailed_response(self, mock_pprint, mock_get):
        isbn = "9780123456789"

        detailed_response = {
            "isbn": isbn,
            "title": "Advanced Python Programming",
            "author": "John Doe",
            "publisher": "Tech Press",
            "year": 2020,
            "pages": 450,
            "language": "English"
        }

        mock_response = Mock()
        mock_response.json.return_value = detailed_response
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()):
            self.isbn_lookup.lookup(isbn)

        self.assertEqual(self.isbn_lookup.result, detailed_response)
        self.assertEqual(self.isbn_lookup.result["title"], "Advanced Python Programming")
        self.assertEqual(self.isbn_lookup.result["author"], "John Doe")


class TestISBNLookupConfiguration(unittest.TestCase):

    def test_init_with_minimal_config(self):
        config = {
            "key": "api-key",
            "url_isbn": "http://api.com/{}",
        }
        lookup = ISBNLookup(config)

        self.assertEqual(lookup.config["key"], "api-key")
        self.assertEqual(lookup.config["url_isbn"], "http://api.com/{}")

    def test_init_with_empty_config(self):
        config = {}
        lookup = ISBNLookup(config)

        self.assertEqual(lookup.config, {})
        self.assertIsNone(lookup.result)


class TestISBNLookupIntegration(unittest.TestCase):

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_multiple_lookups_sequential(self, mock_pprint, mock_get):
        config = {
            "key": "test-key",
            "url_isbn": "http://api.test.com/{}"
        }
        lookup = ISBNLookup(config)

        isbn1 = "1111111111"
        isbn2 = "2222222222"

        response1 = Mock()
        response1.json.return_value = {"title": "First Book", "isbn": isbn1}

        response2 = Mock()
        response2.json.return_value = {"title": "Second Book", "isbn": isbn2}

        mock_get.side_effect = [response1, response2]

        with patch('sys.stdout', new=StringIO()):
            lookup.lookup(isbn1)
            first_result = lookup.result

            lookup.lookup(isbn2)
            second_result = lookup.result

        self.assertEqual(first_result["title"], "First Book")
        self.assertEqual(second_result["title"], "Second Book")

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_list_stores_all_results(self, mock_pprint, mock_get):
        config = {
            "key": "test-key",
            "url_isbn": "http://api.test.com/{}"
        }
        lookup = ISBNLookup(config)

        isbns = ["1111", "2222", "3333"]
        responses = []

        for i, isbn in enumerate(isbns):
            response = Mock()
            response.json.return_value = {"title": f"Book {i+1}", "isbn": isbn}
            responses.append(response)

        mock_get.side_effect = responses

        with patch('builtins.input', return_value=''):
            lookup.lookup(isbns)

        self.assertEqual(len(lookup.result), 3)
        for isbn in isbns:
            self.assertIn(isbn, lookup.result)


class TestISBNLookupEdgeCases(unittest.TestCase):

    def setUp(self):
        self.config = {
            "key": "test-key",
            "url_isbn": "http://api.test.com/{}"
        }

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_with_special_isbn_format(self, mock_pprint, mock_get):
        lookup = ISBNLookup(self.config)
        isbn = "978-0-123-45678-9"

        mock_response = Mock()
        mock_response.json.return_value = {"title": "Special ISBN Book"}
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()):
            lookup.lookup(isbn)

        call_url = mock_get.call_args[0][0]
        self.assertIn(isbn, call_url)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_single_item_list(self, mock_pprint, mock_get):
        lookup = ISBNLookup(self.config)
        isbns = ["1234567890"]

        mock_response = Mock()
        mock_response.json.return_value = {"title": "Only Book"}
        mock_get.return_value = mock_response

        lookup.lookup(isbns)

        self.assertIsInstance(lookup.result, dict)
        self.assertIn(isbns[0], lookup.result)

    @patch('bookdbtool.isbn_lookup_tools.req.get')
    @patch('bookdbtool.isbn_lookup_tools.pprint')
    def test_lookup_authorization_header(self, mock_pprint, mock_get):
        lookup = ISBNLookup(self.config)
        isbn = "1234567890"

        mock_response = Mock()
        mock_response.json.return_value = {"title": "Test"}
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()):
            lookup.lookup(isbn)

        call_headers = mock_get.call_args[1]['headers']
        self.assertEqual(call_headers['Authorization'], self.config["key"])


if __name__ == '__main__':
    unittest.main()
