import unittest
from unittest.mock import Mock, patch
import sys
import os
from io import StringIO

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bookdbtool.ai_tools import ChatAgent, OllamaAgent


def _chat_response(history, trace, status=200):
    resp = Mock(ok=200 <= status < 300, status_code=status)
    resp.json.return_value = {"history": history, "trace": trace}
    return resp


def _error_response(status, error):
    resp = Mock(ok=False, status_code=status, text=error)
    resp.json.return_value = {"error": error}
    return resp


class TestChatAgent(unittest.TestCase):

    @patch('bookdbtool.ai_tools.requests.Session')
    def setUp(self, mock_session_class):
        self.mock_session = Mock()
        mock_session_class.return_value = self.mock_session

        self.config = {
            "ai_agent": {
                "chat_model": "ignored-by-cli",
                "chat_host": "http://ignored:1234",
                "timeout": 15,
                "max_history": 100
            },
            "endpoint": "http://localhost:8084",
            "api_key": "test-api-key"
        }
        self.agent = ChatAgent(self.config)

    def test_ollama_agent_alias(self):
        self.assertIs(OllamaAgent, ChatAgent)

    @patch('bookdbtool.ai_tools.requests.Session')
    def test_init(self, mock_session_class):
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        agent = ChatAgent(self.config)
        self.assertEqual(agent.book_db_host, "http://localhost:8084")
        self.assertEqual(agent.api_key, "test-api-key")
        self.assertEqual(agent.timeout, 15)
        self.assertEqual(agent.max_history, 100)
        self.assertEqual(agent.conversation_history, [])
        self.assertIsNone(agent.reply)
        mock_session.headers.update.assert_called_once_with({"x-api-key": "test-api-key"})

    @patch('bookdbtool.ai_tools.requests.Session')
    def test_init_defaults(self, mock_session_class):
        agent = ChatAgent({})
        self.assertEqual(agent.book_db_host, "http://localhost:8084")
        self.assertEqual(agent.api_key, "")
        self.assertEqual(agent.timeout, ChatAgent.DEFAULT_TIMEOUT)
        self.assertEqual(agent.max_history, ChatAgent.MAX_HISTORY)

    @patch.dict(os.environ, {"AI_CHAT_TIMEOUT": "30", "AI_CHAT_MAX_HISTORY": "5"})
    @patch('bookdbtool.ai_tools.requests.Session')
    def test_init_env_overrides_config(self, mock_session_class):
        agent = ChatAgent(self.config)
        self.assertEqual(agent.timeout, 30)
        self.assertEqual(agent.max_history, 5)

    def test_does_not_call_llm_directly(self):
        self.assertFalse(hasattr(self.agent, "_chat_completion"))
        self.assertFalse(hasattr(self.agent, "TOOLS"))

    @patch('bookdbtool.ai_tools.Path')
    @patch('builtins.open')
    @patch('bookdbtool.ai_tools.requests.Session')
    def test_from_config_file_success(self, mock_session, mock_open, mock_path):
        mock_path.return_value.exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '{"endpoint": "http://x:1"}'
        agent = ChatAgent.from_config_file("config.json")
        self.assertEqual(agent.book_db_host, "http://x:1")

    @patch('bookdbtool.ai_tools.Path')
    def test_from_config_file_not_found(self, mock_path):
        mock_path.return_value.exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            ChatAgent.from_config_file("missing.json")

    def test_version_success(self):
        self.mock_session.get.return_value = Mock(json=Mock(return_value={"version": "0.21.2"}))
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.version()
        self.assertIn("0.21.2", out.getvalue())
        self.assertIn("http://localhost:8084/chat", out.getvalue())

    def test_version_unreachable(self):
        self.mock_session.get.side_effect = requests.ConnectionError("refused")
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.version()
        self.assertIn("Could not reach", out.getvalue())

    def test_chat_posts_history_to_endpoint(self):
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        self.mock_session.post.return_value = _chat_response(
            history, [{"type": "assistant", "content": "Hello!"}])

        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.chat("hi")

        self.mock_session.post.assert_called_once_with(
            "http://localhost:8084/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
            timeout=15,
        )
        self.assertEqual(self.agent.conversation_history, history)
        self.assertEqual(out.getvalue().strip(), "Hello!")

    def test_chat_sends_prior_history(self):
        self.agent.conversation_history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "one"},
        ]
        self.mock_session.post.return_value = _chat_response([], [])
        with patch('sys.stdout', new=StringIO()):
            self.agent.chat("second")
        sent = self.mock_session.post.call_args.kwargs["json"]["messages"]
        self.assertEqual([m["content"] for m in sent], ["first", "one", "second"])

    def test_chat_prints_tool_trace(self):
        trace = [
            {"type": "tool", "toolName": "search_books", "toolArgs": {"Author": "Tolkien"}, "toolResult": {}},
            {"type": "assistant", "content": "Found The Hobbit."},
        ]
        self.mock_session.post.return_value = _chat_response([], trace)
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.chat("Tolkien?")
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], "  [tool] search_books(Author='Tolkien')")
        self.assertEqual(lines[1], "Found The Hobbit.")

    def test_chat_server_error_keeps_history(self):
        self.agent.conversation_history = [{"role": "user", "content": "earlier"}]
        self.mock_session.post.return_value = _error_response(503, "Chat is not configured on this server.")
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.chat("hello")
        self.assertIn("503", out.getvalue())
        self.assertIn("not configured", out.getvalue())
        self.assertEqual(self.agent.conversation_history, [{"role": "user", "content": "earlier"}])

    def test_chat_connection_error_keeps_history(self):
        self.mock_session.post.side_effect = requests.ConnectionError("refused")
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.chat("hello")
        self.assertIn("Chat request failed", out.getvalue())
        self.assertEqual(self.agent.conversation_history, [])

    def test_trim_history_cuts_at_user_turn(self):
        self.agent.max_history = 4
        self.agent.conversation_history = [
            {"role": "user", "content": "q1"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]},
            {"role": "tool", "content": "{}", "tool_call_id": "c1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]
        self.agent._trim_history()
        self.assertEqual([m["content"] for m in self.agent.conversation_history], ["q2", "a2"])

    def test_trim_history_noop_when_short(self):
        self.agent.conversation_history = [{"role": "user", "content": "q"}]
        self.agent._trim_history()
        self.assertEqual(len(self.agent.conversation_history), 1)

    def test_clear_history(self):
        self.agent.conversation_history = [{"role": "user", "content": "q"}]
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.clear_history()
        self.assertEqual(self.agent.conversation_history, [])
        self.assertIn("cleared", out.getvalue())

    def test_show_history_with_messages(self):
        self.agent.conversation_history = [{"role": "user", "content": "Hello"}]
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.show_history()
        self.assertIn("Hello", out.getvalue())

    def test_show_reply_none(self):
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.show_reply()
        self.assertIn("No reply available", out.getvalue())

    def test_show_reply_with_data(self):
        self.agent.reply = {"trace": [{"type": "assistant", "content": "Test"}]}
        with patch('sys.stdout', new=StringIO()) as out:
            self.agent.show_reply()
        self.assertIn("Test", out.getvalue())


if __name__ == '__main__':
    unittest.main()
