import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import json
from io import StringIO

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bookdbtool.ai_tools import OllamaAgent


class TestOllamaAgent(unittest.TestCase):

    def setUp(self):
        self.config = {
            "ai_agent": {
                "model_name": "test-model",
                "ollama_host": "http://localhost:11434"
            },
            "endpoint": "http://localhost:8084",
            "api_key": "test-api-key"
        }
        self.agent = OllamaAgent(self.config)

    def test_init(self):
        self.assertEqual(self.agent.ollama_host, "http://localhost:11434")
        self.assertEqual(self.agent.book_db_host, "http://localhost:8084")
        self.assertEqual(self.agent.model_name, "test-model")
        self.assertEqual(self.agent.api_key, "test-api-key")
        self.assertIsNone(self.agent.reply)
        self.assertEqual(self.agent.conversation_history, [])

    def test_init_defaults(self):
        minimal_config = {}
        agent = OllamaAgent(minimal_config)
        self.assertEqual(agent.ollama_host, "http://localhost:11434")
        self.assertEqual(agent.book_db_host, "http://localhost:8084")
        self.assertEqual(agent.model_name, "gpt-oss")
        self.assertEqual(agent.api_key, "")

    def test_tools_structure(self):
        self.assertEqual(len(self.agent.tools), 5)
        tool_names = [tool["function"]["name"] for tool in self.agent.tools]
        self.assertIn("search_books_by_author", tool_names)
        self.assertIn("search_books_by_title", tool_names)
        self.assertIn("search_books_by_tags", tool_names)
        self.assertIn("get_book_tags", tool_names)
        self.assertIn("add_tag_to_book", tool_names)

    def test_available_functions_mapping(self):
        self.assertEqual(len(self.agent.available_functions), 5)
        self.assertIn("search_books_by_author", self.agent.available_functions)
        self.assertEqual(
            self.agent.available_functions["search_books_by_author"],
            self.agent.search_books_by_author
        )

    @patch('bookdbtool.ai_tools.Path')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"endpoint": "http://test.com"}')
    def test_from_config_file_success(self, mock_open, mock_path):
        mock_path.return_value.exists.return_value = True

        agent = OllamaAgent.from_config_file("config.json")
        self.assertIsInstance(agent, OllamaAgent)

    @patch('bookdbtool.ai_tools.Path')
    def test_from_config_file_not_found(self, mock_path):
        mock_path.return_value.exists.return_value = False

        with self.assertRaises(FileNotFoundError):
            OllamaAgent.from_config_file("missing.json")

    @patch('bookdbtool.ai_tools.requests.get')
    def test_version_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"version": "1.5.0"}
        mock_get.return_value = mock_response

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.version()
            output = fake_out.getvalue()
            self.assertIn("1.5.0", output)
            self.assertIn("http://localhost:8084", output)
            self.assertIn("http://localhost:11434", output)
            self.assertIn("test-model", output)

    @patch('bookdbtool.ai_tools.requests.get')
    def test_search_books_by_author_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "Book 1", "Test Author", 2020]],
            "header": ["ID", "Title", "Author", "Year"]
        }
        mock_get.return_value = mock_response

        result = self.agent.search_books_by_author("Test Author")
        self.assertIn("data", result)
        self.assertEqual(len(result["data"]), 1)
        mock_get.assert_called_once()

    @patch('bookdbtool.ai_tools.requests.get')
    def test_search_books_by_author_error(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = self.agent.search_books_by_author("Test Author")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Network error")

    @patch('bookdbtool.ai_tools.requests.get')
    def test_search_books_by_title_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "Test Book", "Author", 2020]],
            "header": ["ID", "Title", "Author", "Year"]
        }
        mock_get.return_value = mock_response

        result = self.agent.search_books_by_title("Test Book")
        self.assertIn("data", result)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn("Title", call_args[1]["params"])

    @patch('bookdbtool.ai_tools.requests.get')
    def test_search_books_by_tags_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [[1, "Book 1", "Author", 2020]],
            "header": ["ID", "Title", "Author", "Year"]
        }
        mock_get.return_value = mock_response

        result = self.agent.search_books_by_tags("fiction")
        self.assertIn("data", result)
        call_args = mock_get.call_args
        self.assertIn("Tags", call_args[1]["params"])

    @patch('bookdbtool.ai_tools.requests.get')
    def test_get_book_tags_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {"tag_list": ["fiction", "classic"]}
        mock_get.return_value = mock_response

        result = self.agent.get_book_tags(1)
        self.assertIn("tag_list", result)
        self.assertEqual(len(result["tag_list"]), 2)

    @patch('bookdbtool.ai_tools.requests.get')
    def test_get_book_tags_error(self, mock_get):
        mock_get.side_effect = Exception("Connection error")

        result = self.agent.get_book_tags(1)
        self.assertIn("error", result)

    @patch('bookdbtool.ai_tools.requests.put')
    def test_add_tag_to_book_success(self, mock_put):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_put.return_value = mock_response

        result = self.agent.add_tag_to_book(1, "fiction")
        self.assertTrue(result["success"])
        self.assertEqual(result["book_id"], 1)
        self.assertEqual(result["tag"], "fiction")

    @patch('bookdbtool.ai_tools.requests.put')
    def test_add_tag_to_book_http_error(self, mock_put):
        from requests.exceptions import HTTPError
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)
        mock_put.return_value = mock_response

        result = self.agent.add_tag_to_book(1, "fiction")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch('bookdbtool.ai_tools.requests.put')
    def test_add_tag_to_book_general_error(self, mock_put):
        mock_put.side_effect = Exception("Network error")

        result = self.agent.add_tag_to_book(1, "fiction")
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_tool_call_to_dict_with_dict(self):
        tool_call = {"function": {"name": "test", "arguments": {}}}
        result = OllamaAgent._tool_call_to_dict(tool_call)
        self.assertEqual(result, tool_call)

    def test_tool_call_to_dict_with_object(self):
        tool_call = Mock()
        tool_call.function = Mock()
        tool_call.function.name = "search_books_by_author"
        tool_call.function.arguments = {"author": "Test"}

        result = OllamaAgent._tool_call_to_dict(tool_call)
        self.assertIn("function", result)
        self.assertEqual(result["function"]["name"], "search_books_by_author")

    def test_message_to_dict_with_dict(self):
        message = {
            "role": "assistant",
            "content": "Hello",
            "tool_calls": [{"function": {"name": "test"}}]
        }
        result = OllamaAgent._message_to_dict(message)
        self.assertEqual(result["role"], "assistant")
        self.assertEqual(result["content"], "Hello")

    def test_message_to_dict_with_object(self):
        message = Mock()
        message.role = "assistant"
        message.content = "Hello"
        message.tool_calls = None

        result = OllamaAgent._message_to_dict(message)
        self.assertEqual(result["role"], "assistant")
        self.assertEqual(result["content"], "Hello")

    @patch('bookdbtool.ai_tools.ollama.Client')
    def test_chat_without_tool_calls(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_response = {
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you?"
            }
        }
        mock_client.chat.return_value = mock_response

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.chat("Hello")
            output = fake_out.getvalue()
            self.assertIn("Hello! How can I help you?", output)

        self.assertEqual(len(self.agent.conversation_history), 2)
        self.assertEqual(self.agent.conversation_history[0]["role"], "user")
        self.assertEqual(self.agent.conversation_history[1]["role"], "assistant")

    @patch('bookdbtool.ai_tools.ollama.Client')
    def test_chat_with_tool_calls(self, mock_client_class):
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create a mock for the search function and patch it in available_functions
        mock_search = Mock()
        mock_search.return_value = {"data": [[1, "Book", "Author"]], "header": ["ID", "Title", "Author"]}
        self.agent.available_functions["search_books_by_author"] = mock_search

        initial_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "search_books_by_author",
                            "arguments": {"author": "Tolkien"}
                        }
                    }
                ]
            }
        }

        final_chunks = [
            {"message": {"content": "I found "}},
            {"message": {"content": "books by Tolkien."}}
        ]

        mock_client.chat.side_effect = [initial_response, iter(final_chunks)]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.chat("Find books by Tolkien")
            output = fake_out.getvalue()
            self.assertIn("I found", output)

        mock_search.assert_called_once_with(author="Tolkien")
        self.assertGreater(len(self.agent.conversation_history), 2)

    def test_clear_history(self):
        self.agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        with patch('sys.stdout', new=StringIO()):
            self.agent.clear_history()

        self.assertEqual(self.agent.conversation_history, [])

    def test_show_history_empty(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.show_history()
            output = fake_out.getvalue()
            self.assertEqual(output.strip(), "[]")

    def test_show_history_with_messages(self):
        self.agent.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.show_history()
            output = fake_out.getvalue()
            self.assertIn("user", output)
            self.assertIn("assistant", output)

    def test_show_reply_none(self):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.show_reply()
            output = fake_out.getvalue()
            self.assertIn("No reply available", output)

    def test_show_reply_with_data(self):
        self.agent.reply = {
            "message": {
                "role": "assistant",
                "content": "Test reply"
            }
        }

        with patch('sys.stdout', new=StringIO()) as fake_out:
            self.agent.show_reply()
            output = fake_out.getvalue()
            self.assertIn("Test reply", output)


class TestOllamaAgentIntegration(unittest.TestCase):

    @patch('bookdbtool.ai_tools.ollama.Client')
    @patch('bookdbtool.ai_tools.requests.get')
    def test_full_chat_flow(self, mock_get, mock_client_class):
        config = {
            "ai_agent": {"model_name": "test", "ollama_host": "http://localhost:11434"},
            "endpoint": "http://localhost:8084",
            "api_key": "test-key"
        }
        agent = OllamaAgent(config)

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_get_response = Mock()
        mock_get_response.json.return_value = {
            "data": [[1, "The Hobbit", "Tolkien"]],
            "header": ["ID", "Title", "Author"]
        }
        mock_get.return_value = mock_get_response

        initial_response = {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "function": {
                        "name": "search_books_by_author",
                        "arguments": {"author": "Tolkien"}
                    }
                }]
            }
        }

        final_response = iter([
            {"message": {"content": "I found The Hobbit by Tolkien."}}
        ])

        mock_client.chat.side_effect = [initial_response, final_response]

        with patch('sys.stdout', new=StringIO()):
            agent.chat("Find books by Tolkien")

        self.assertEqual(len(agent.conversation_history), 4)
        self.assertEqual(agent.conversation_history[0]["role"], "user")
        self.assertEqual(agent.conversation_history[2]["role"], "tool")


if __name__ == '__main__':
    unittest.main()
