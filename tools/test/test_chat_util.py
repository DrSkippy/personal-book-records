import json
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'book_service'))

# booksdb.config reads configuration.json at import time; point it at a
# throwaway file before importing booksdb.chat_util (mirrors test_config.py).
_tmp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
json.dump({
    "username": "user", "password": "pass", "database": "db",
    "host": "localhost", "port": 5432,
    "isbn_com": {"url_isbn": "https://example.com/{}", "key": "isbn-key"},
    "api_key": "file-api-key",
    "ai_agent": {
        "chat_host": "http://chat-host:1234",
        "chat_model": "test-model",
        "chat_api_key": "test-chat-key",
    },
}, _tmp_config)
_tmp_config.close()
os.environ.setdefault("BOOKDB_CONFIG", _tmp_config.name)

from booksdb import chat_util


def _openai_response(content="", tool_calls=None):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}]}


class TestExecuteTool(unittest.TestCase):
    def test_unknown_tool_returns_error(self):
        result = chat_util.execute_tool("not_a_real_tool", {})
        self.assertIn("error", result)

    def test_dispatch_catches_exceptions(self):
        with patch.object(chat_util, "TOOL_DISPATCH", {"boom": Mock(side_effect=RuntimeError("db down"))}):
            result = chat_util.execute_tool("boom", {})
            self.assertEqual(result, {"error": "db down"})

    def test_search_books_dispatch(self):
        with patch.object(chat_util.api_util, "books_search_utility", return_value=([(1, "Title")], ["BookId", "Title"], None)):
            result = chat_util.execute_tool("search_books", {"Title": "Hobbit"})
            self.assertEqual(result["header"], ["BookId", "Title"])
            self.assertEqual(result["data"], [[1, "Title"]])

    def test_get_book_details_dispatch(self):
        with patch.object(chat_util.api_util, "get_complete_book_record", return_value={"book": {"BookId": 5}}) as mock_fn:
            result = chat_util.execute_tool("get_book_details", {"bookId": 5})
            mock_fn.assert_called_once_with(5)
            self.assertEqual(result, {"book": {"BookId": 5}})

    def test_add_tag_to_book_dispatch(self):
        with patch.object(chat_util.api_util, "add_tag_to_book", return_value=({"BookId": 1, "Tag": "fiction"}, None)) as mock_fn:
            result = chat_util.execute_tool("add_tag_to_book", {"bookId": 1, "tag": "fiction"})
            mock_fn.assert_called_once_with(1, "fiction")
            self.assertEqual(result["Tag"], "fiction")

    def test_semantic_search_notes_dispatch(self):
        with patch.object(chat_util.api_util, "rag_search", return_value=[{"book_id": 1}]) as mock_fn:
            result = chat_util.execute_tool("semantic_search_notes", {"query": "loss", "limit": 3})
            mock_fn.assert_called_once_with("loss", limit=3)
            self.assertEqual(result, [{"book_id": 1}])

    def test_get_tag_counts_defaults_to_20(self):
        rows = [(f"tag{i}", 100 - i) for i in range(50)]
        with patch.object(chat_util.api_util, "get_tag_counts", return_value=(rows, ["Tag", "Count"], None)):
            result = chat_util.execute_tool("get_tag_counts", {})
            self.assertEqual(len(result["data"]), 20)
            self.assertEqual(result["data"][0], ["tag0", 100])

    def test_get_tag_counts_respects_explicit_limit(self):
        rows = [(f"tag{i}", 100 - i) for i in range(50)]
        with patch.object(chat_util.api_util, "get_tag_counts", return_value=(rows, ["Tag", "Count"], None)):
            result = chat_util.execute_tool("get_tag_counts", {"limit": 3})
            self.assertEqual(len(result["data"]), 3)


class TestChatCompletion(unittest.TestCase):
    def test_raises_when_not_configured(self):
        with patch.object(chat_util, "CHAT_HOST", None), patch.object(chat_util, "CHAT_MODEL", None):
            with self.assertRaises(RuntimeError):
                chat_util.chat_completion([{"role": "user", "content": "hi"}])

    @patch('booksdb.chat_util.requests.post')
    def test_sends_auth_header_and_model(self, mock_post):
        mock_post.return_value = Mock(json=Mock(return_value=_openai_response("hi")), raise_for_status=Mock())
        chat_util.chat_completion([{"role": "user", "content": "hi"}])
        args, kwargs = mock_post.call_args
        self.assertTrue(args[0].endswith("/v1/chat/completions"))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-chat-key")
        self.assertEqual(kwargs["json"]["model"], "test-model")
        self.assertEqual(kwargs["json"]["tools"], chat_util.TOOLS)


class TestRunChatLoop(unittest.TestCase):
    @patch('booksdb.chat_util.requests.post')
    def test_no_tool_calls_returns_final_reply(self, mock_post):
        mock_post.return_value = Mock(
            json=Mock(return_value=_openai_response("Hello!")),
            raise_for_status=Mock(),
        )
        history = [{"role": "user", "content": "hi"}]
        result = chat_util.run_chat_loop(history)
        self.assertEqual(result["trace"], [{"type": "assistant", "content": "Hello!"}])
        self.assertEqual(result["history"][-1], {"role": "assistant", "content": "Hello!"})
        # system prompt never leaks into stored history
        self.assertTrue(all(m["role"] != "system" for m in result["history"]))

    @patch('booksdb.chat_util.requests.post')
    def test_tool_call_then_final_reply(self, mock_post):
        initial = _openai_response(tool_calls=[{
            "id": "call_1",
            "function": {"name": "get_tag_counts", "arguments": "{}"},
        }])
        final = _openai_response("Here are your tags.")
        mock_post.side_effect = [
            Mock(json=Mock(return_value=initial), raise_for_status=Mock()),
            Mock(json=Mock(return_value=final), raise_for_status=Mock()),
        ]
        with patch.object(chat_util.api_util, "get_tag_counts", return_value=([("fiction", 3)], ["Tag", "Count"], None)):
            result = chat_util.run_chat_loop([{"role": "user", "content": "what tags do I have?"}])

        trace_types = [t["type"] for t in result["trace"]]
        self.assertEqual(trace_types, ["tool", "assistant"])
        self.assertEqual(result["trace"][0]["toolName"], "get_tag_counts")
        self.assertEqual(result["trace"][1]["content"], "Here are your tags.")
        roles = [m["role"] for m in result["history"]]
        self.assertEqual(roles, ["user", "assistant", "tool", "assistant"])

    @patch('booksdb.chat_util.requests.post')
    def test_oversized_tool_result_truncated_in_history_not_in_trace(self, mock_post):
        # A tool result far larger than MAX_TOOL_RESULT_CHARS (e.g. get_tag_counts
        # with no prefix on a large collection) must not be sent to the model
        # verbatim -- that's exactly what blew LM Studio's context window in
        # production (57508 tokens vs. a 31232 token limit).
        huge_rows = [(f"tag{i}", i) for i in range(5000)]
        initial = _openai_response(tool_calls=[{
            "id": "call_1",
            "function": {"name": "get_tag_counts", "arguments": '{"limit": 5000}'},
        }])
        final = _openai_response("Here are your tags.")
        mock_post.side_effect = [
            Mock(json=Mock(return_value=initial), raise_for_status=Mock()),
            Mock(json=Mock(return_value=final), raise_for_status=Mock()),
        ]
        with patch.object(chat_util.api_util, "get_tag_counts", return_value=(huge_rows, ["Tag", "Count"], None)):
            result = chat_util.run_chat_loop([{"role": "user", "content": "list every tag"}])

        tool_message = next(m for m in result["history"] if m["role"] == "tool")
        self.assertLessEqual(len(tool_message["content"]), chat_util.MAX_TOOL_RESULT_CHARS + 200)
        self.assertIn("truncated", tool_message["content"])

        # the UI-facing trace keeps the full, untruncated result
        tool_trace_event = next(t for t in result["trace"] if t["type"] == "tool")
        self.assertEqual(len(tool_trace_event["toolResult"]["data"]), 5000)

    @patch('booksdb.chat_util.requests.post')
    def test_exhausting_max_iterations_returns_fallback_message(self, mock_post):
        looping_response = _openai_response(tool_calls=[{
            "id": "call_1",
            "function": {"name": "get_tag_counts", "arguments": "{}"},
        }])
        mock_post.return_value = Mock(json=Mock(return_value=looping_response), raise_for_status=Mock())
        with patch.object(chat_util.api_util, "get_tag_counts", return_value=([], ["Tag", "Count"], None)):
            result = chat_util.run_chat_loop([{"role": "user", "content": "loop forever"}])
        self.assertEqual(mock_post.call_count, chat_util.MAX_ITERATIONS)
        self.assertEqual(result["trace"][-1]["type"], "assistant")
        self.assertIn("couldn't finish", result["trace"][-1]["content"])


def _record(reads, title="Dune", tags=("sf", "classic")):
    return {
        "book": {"header": ["BookId", "Title", "Author"], "data": [[7, title, "Herbert"]]},
        "reads": {"header": ["DateRead", "ReadNote"], "data": reads},
        "tags": {"header": ["Tag"], "data": [list(tags)]},
        "img": {"header": ["ImageURL"], "data": [[]]},
    }


class TestReadNoteDrafting(unittest.TestCase):
    def test_book_details_flags_read_with_blank_note(self):
        rec = _record([["2026-01-02", "Loved it"], ["2026-09-01", None], ["2026-10-01", "  "]])
        with patch.object(chat_util.api_util, "get_complete_book_record", return_value=rec):
            result = chat_util.execute_tool("get_book_details", {"bookId": 7})
        self.assertEqual(result["reads_missing_notes"], [{"ReadDate": "2026-09-01"}, {"ReadDate": "2026-10-01"}])
        self.assertIn("draft_read_note", result["next_step"])

    def test_book_details_no_flag_when_notes_present_or_never_read(self):
        for reads in ([["2026-01-02", "Loved it"]], []):
            with patch.object(chat_util.api_util, "get_complete_book_record", return_value=_record(reads)):
                result = chat_util.execute_tool("get_book_details", {"bookId": 7})
            self.assertNotIn("reads_missing_notes", result)
            self.assertNotIn("next_step", result)

    @patch('booksdb.chat_util.requests.post')
    def test_draft_read_note_sends_observations_without_tools(self, mock_post):
        mock_post.return_value = Mock(json=Mock(return_value=_openai_response("Para one.\n\nPara two.")),
                                      raise_for_status=Mock())
        with patch.object(chat_util.api_util, "get_complete_book_record",
                          return_value=_record([["2026-09-01", None]])):
            result = chat_util.draft_read_note(7, "2026-09-01", ["Ecology matters", " ", "Slow start"])
        self.assertEqual(result, {"BookId": 7, "ReadDate": "2026-09-01", "Title": "Dune",
                                  "draft": "Para one.\n\nPara two."})
        payload = mock_post.call_args.kwargs["json"]
        self.assertNotIn("tools", payload)
        self.assertEqual(payload["messages"][0]["content"], chat_util.DRAFT_REVIEW_PROMPT)
        user_msg = payload["messages"][1]["content"]
        self.assertIn("- Ecology matters\n- Slow start", user_msg)
        self.assertIn("Tags: sf, classic", user_msg)

    def test_draft_read_note_rejects_bad_input(self):
        with patch.object(chat_util.api_util, "get_complete_book_record",
                          return_value=_record([["2026-09-01", None]])):
            with self.assertRaises(ValueError):
                chat_util.draft_read_note(7, "2026-09-01", ["  "])
            with self.assertRaises(ValueError):
                chat_util.draft_read_note(7, "1999-01-01", ["A point"])
        with patch.object(chat_util.api_util, "get_complete_book_record",
                          return_value={"book": {"header": ["BookId"], "data": []}}):
            with self.assertRaises(ValueError):
                chat_util.draft_read_note(999, "2026-09-01", ["A point"])

    def test_draft_tool_marks_unsaved_and_accepts_string_observations(self):
        with patch.object(chat_util, "draft_read_note",
                          return_value={"BookId": 7, "ReadDate": "2026-09-01", "Title": "Dune", "draft": "x"}) as fn:
            result = chat_util.execute_tool("draft_read_note", {
                "bookId": 7, "readDate": "2026-09-01", "observations": "- one\n- two"})
        fn.assert_called_once_with(7, "2026-09-01", ["one", "two"])
        self.assertIn("NOT been saved", result["status"])


class TestDraftHiddenFromModel(unittest.TestCase):
    @patch('booksdb.chat_util.requests.post')
    def test_draft_text_in_trace_but_not_history(self, mock_post):
        tool_call = {"id": "c1", "type": "function", "function": {
            "name": "draft_read_note",
            "arguments": json.dumps({"bookId": 7, "readDate": "2026-09-01", "observations": ["a"]})}}
        mock_post.side_effect = [
            Mock(json=Mock(return_value=_openai_response("", [tool_call])), raise_for_status=Mock()),
            Mock(json=Mock(return_value=_openai_response("Ready below.")), raise_for_status=Mock()),
        ]
        draft = {"BookId": 7, "ReadDate": "2026-09-01", "Title": "Dune", "draft": "SECRET DRAFT"}
        with patch.object(chat_util, "draft_read_note", return_value=dict(draft)):
            result = chat_util.run_chat_loop([{"role": "user", "content": "go"}])
        self.assertEqual(result["trace"][0]["toolResult"]["draft"], "SECRET DRAFT")
        tool_msg = [m for m in result["history"] if m["role"] == "tool"][0]
        self.assertNotIn("SECRET DRAFT", tool_msg["content"])


if __name__ == '__main__':
    unittest.main()
