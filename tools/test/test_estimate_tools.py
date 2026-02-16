import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bookdbtool.estimate_tools import ESTTool


class TestESTTool(unittest.TestCase):

    def setUp(self):
        self.endpoint = "http://test-endpoint.com"
        self.api_key = "test-api-key"
        self.est_tool = ESTTool(self.endpoint, self.api_key)

    def test_init(self):
        self.assertEqual(self.est_tool.end_point, self.endpoint)
        self.assertEqual(self.est_tool.header, {"x-api-key": self.api_key})
        self.assertIsNone(self.est_tool.result)

    @patch('bookdbtool.estimate_tools.requests.get')
    def test_version_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"version": "2.0.0"}
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.version()
            output = fake_out.getvalue()
            self.assertIn("2.0.0", output)
            self.assertIn(self.endpoint, output)
            self.assertIn("Book Records and Reading Database", output)

    @patch('bookdbtool.estimate_tools.requests.get')
    def test_version_request_exception(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        with patch('bookdbtool.estimate_tools.logging.error') as mock_log:
            self.est_tool.version()
            mock_log.assert_called_once()

    def test_ver_alias(self):
        self.assertEqual(self.est_tool.ver, self.est_tool.version)

    @patch('bookdbtool.estimate_tools.requests.put')
    @patch('bookdbtool.estimate_tools.requests.get')
    def test_new_book_estimate_success(self, mock_get, mock_put):
        book_id = 1
        total_pages = 300

        put_response = Mock()
        put_response.json.return_value = {
            "add_book_estimate": {
                "BookId": book_id,
                "StartDate": "2024-01-01"
            }
        }
        mock_put.return_value = put_response

        get_response_1 = Mock()
        get_response_1.json.return_value = {
            "record_set": {
                "RecordId": [[datetime.datetime.now().strftime("%Y-%m-%d"), 123]],
                "Estimate": [["2024-02-01", "2024-01-25", "2024-02-05"]]
            }
        }

        get_response_2 = Mock()
        get_response_2.json.return_value = {
            "data": [[1, "Test Book", "Test Author", 2020, "123", "Publisher", "Hard", 300]]
        }

        mock_get.side_effect = [get_response_1, get_response_2]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.new_book_estimate(book_id, total_pages)
            output = fake_out.getvalue()
            self.assertIn("started on", output)

        expected_url = f"{self.endpoint}/add_book_estimate/{book_id}/{total_pages}"
        mock_put.assert_called_once_with(expected_url, headers=self.est_tool.header)

    @patch('bookdbtool.estimate_tools.requests.put')
    @patch('bookdbtool.estimate_tools.requests.get')
    def test_new_book_estimate_error(self, mock_get, mock_put):
        book_id = 1
        total_pages = 300

        put_response = Mock()
        put_response.json.return_value = {"error": "Book not found"}
        mock_put.return_value = put_response

        get_response_1 = Mock()
        get_response_1.json.return_value = {
            "record_set": {
                "RecordId": [],
                "Estimate": []
            }
        }

        get_response_2 = Mock()
        get_response_2.json.return_value = {
            "data": [[1, "Test Book", "Test Author", 2020, "123", "Publisher", "Hard", 300]]
        }

        mock_get.side_effect = [get_response_1, get_response_2]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.new_book_estimate(book_id, total_pages)
            output = fake_out.getvalue()
            self.assertIn("Error:", output)

    def test_nbe_alias(self):
        self.assertEqual(self.est_tool.nbe, self.est_tool.new_book_estimate)

    @patch('bookdbtool.estimate_tools.requests.get')
    def test_list_book_estimates_success(self, mock_get):
        book_id = 1

        record_response = Mock()
        record_response.json.return_value = {
            "record_set": {
                "RecordId": [["2024-01-01", 123], ["2024-01-15", 124]],
                "Estimate": [
                    ["2024-02-01", "2024-01-25", "2024-02-05"],
                    ["2024-02-15", "2024-02-10", "2024-02-20"]
                ]
            }
        }

        book_response = Mock()
        book_response.json.return_value = {
            "data": [[1, "Test Book", "Test Author", 2020, "123", "Publisher", "Hard", 300]]
        }

        mock_get.side_effect = [record_response, book_response]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.list_book_estimates(book_id)
            output = fake_out.getvalue()
            self.assertIn("Test Book", output)
            self.assertIn("Test Author", output)
            self.assertIn("Start date:", output)
            self.assertIn("Estimated Finish:", output)

        # Result is set to book_id, not RecordID
        self.assertEqual(self.est_tool.result, book_id)

    @patch('bookdbtool.estimate_tools.requests.get')
    def test_list_book_estimates_error(self, mock_get):
        book_id = 1

        record_response = Mock()
        record_response.json.return_value = {"error": "Record not found"}

        book_response = Mock()
        book_response.json.return_value = {
            "data": [[1, "Test Book", "Test Author", 2020, "123", "Publisher", "Hard", 300]]
        }

        mock_get.side_effect = [record_response, book_response]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.list_book_estimates(book_id)
            output = fake_out.getvalue()
            self.assertIn("Error:", output)

    @patch('bookdbtool.estimate_tools.requests.get')
    def test_list_book_estimates_empty(self, mock_get):
        book_id = 1

        record_response = Mock()
        record_response.json.return_value = {
            "record_set": {
                "RecordId": [],
                "Estimate": []
            }
        }

        book_response = Mock()
        book_response.json.return_value = {
            "data": [[1, "Test Book", "Test Author", 2020, "123", "Publisher", "Hard", 300]]
        }

        mock_get.side_effect = [record_response, book_response]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.list_book_estimates(book_id)
            # When there are no records, the function still completes but doesn't print record details
            # The result is still set to book_id

        self.assertEqual(self.est_tool.result, book_id)

    def test_lbe_alias(self):
        self.assertEqual(self.est_tool.lbe, self.est_tool.list_book_estimates)

    @patch('bookdbtool.estimate_tools.requests.post')
    def test_add_page_date_with_date(self, mock_post):
        record_id = 123
        page = 150
        date = "2024-01-15"

        post_response = Mock()
        post_response.json.return_value = {
            "add_date_page": {
                "RecordId": record_id,
                "Page": page,
                "RecordDate": date
            }
        }
        mock_post.return_value = post_response

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.add_page_date(record_id, page, date)
            output = fake_out.getvalue()
            self.assertIn(str(record_id), output)
            self.assertIn(str(page), output)
            self.assertIn(date, output)

        self.assertEqual(self.est_tool.result, record_id)

        expected_url = f"{self.endpoint}/add_date_page"
        expected_payload = {"RecordId": record_id, "RecordDate": date, "Page": page}
        mock_post.assert_called_once_with(
            expected_url,
            json=expected_payload,
            headers=self.est_tool.header
        )

    @patch('bookdbtool.estimate_tools.datetime.datetime')
    @patch('bookdbtool.estimate_tools.requests.post')
    def test_add_page_date_without_date(self, mock_post, mock_datetime):
        record_id = 123
        page = 150
        today = "2024-01-20"

        mock_now = Mock()
        mock_now.strftime.return_value = today
        mock_datetime.now.return_value = mock_now

        post_response = Mock()
        post_response.json.return_value = {
            "add_date_page": {
                "RecordId": record_id,
                "Page": page,
                "RecordDate": today
            }
        }
        mock_post.return_value = post_response

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.est_tool.add_page_date(record_id, page)
            output = fake_out.getvalue()
            self.assertIn(str(record_id), output)
            self.assertIn(str(page), output)

    @patch('bookdbtool.estimate_tools.requests.post')
    def test_add_page_date_error(self, mock_post):
        record_id = 123
        page = 150
        date = "2024-01-15"

        post_response = Mock()
        post_response.json.return_value = {"error": "Invalid page number"}
        mock_post.return_value = post_response

        with patch('bookdbtool.estimate_tools.logging.error') as mock_log:
            self.est_tool.add_page_date(record_id, page, date)
            mock_log.assert_called_once()

    @patch('bookdbtool.estimate_tools.requests.post')
    def test_add_page_date_request_exception(self, mock_post):
        import requests
        record_id = 123
        page = 150

        mock_post.side_effect = requests.RequestException("Network error")

        with patch('bookdbtool.estimate_tools.logging.error') as mock_log:
            self.est_tool.add_page_date(record_id, page)
            mock_log.assert_called_once()

    def test_aps_alias(self):
        self.assertEqual(self.est_tool.aps, self.est_tool.add_page_date)


class TestESTToolConstants(unittest.TestCase):

    def test_fmt_constant(self):
        from bookdbtool.estimate_tools import FMT
        self.assertEqual(FMT, "%Y-%m-%d")

    def test_divider_width_constant(self):
        from bookdbtool.estimate_tools import DIVIDER_WIDTH
        self.assertEqual(DIVIDER_WIDTH, 72)


class TestESTToolIntegration(unittest.TestCase):

    @patch('bookdbtool.estimate_tools.requests.put')
    @patch('bookdbtool.estimate_tools.requests.get')
    @patch('bookdbtool.estimate_tools.requests.post')
    def test_full_workflow(self, mock_post, mock_get, mock_put):
        endpoint = "http://test.com"
        api_key = "test-key"
        tool = ESTTool(endpoint, api_key)

        put_response = Mock()
        put_response.json.return_value = {
            "add_book_estimate": {
                "BookId": 1,
                "StartDate": "2024-01-01"
            }
        }
        mock_put.return_value = put_response

        record_response = Mock()
        record_response.json.return_value = {
            "record_set": {
                "RecordId": [["2024-01-01", 123]],
                "Estimate": [["2024-02-01", "2024-01-25", "2024-02-05"]]
            }
        }

        book_response = Mock()
        book_response.json.return_value = {
            "data": [[1, "Test Book", "Author", 2020, "123", "Pub", "Hard", 300]]
        }

        mock_get.side_effect = [record_response, book_response]

        post_response = Mock()
        post_response.json.return_value = {
            "add_date_page": {
                "RecordId": 123,
                "Page": 100,
                "RecordDate": "2024-01-10"
            }
        }
        mock_post.return_value = post_response

        with patch('sys.stdout', new=StringIO()):
            # new_book_estimate calls list_book_estimates which sets result to book_id
            tool.new_book_estimate(1, 300)
            self.assertEqual(tool.result, 1)

            # add_page_date sets result to record_id
            tool.add_page_date(123, 100, "2024-01-10")
            self.assertEqual(tool.result, 123)


if __name__ == '__main__':
    unittest.main()
