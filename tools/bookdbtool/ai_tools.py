__version__ = '0.4.0'

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class ChatAgent:
    """
    AI Assistant - Natural language interface for querying your book collection.

    A thin client for book-service's POST /chat endpoint, the same one the
    React AI Chat page uses. The server owns the system prompt, the chat
    model/host/key (ai_agent.chat_* on the server), the full tool set, and the
    tool-calling loop; this class only keeps the running conversation history
    and sends it on each turn.

    Attributes:
        reply: The last /chat response ({"history": [...], "trace": [...]}).
        conversation_history: List of all messages in the current conversation.

    Example:
        >>> ai = ChatAgent(config)
        >>> ai.chat("What books do I have by Tolkien?")
        >>> ai.chat("Add the tag 'fantasy' to book 123")
        >>> ai.clear_history()  # Start fresh conversation
    """

    DIVIDER_WIDTH = 50
    MAX_HISTORY = 50  # Maximum conversation history entries to retain
    DEFAULT_TIMEOUT = 300  # The server runs up to 10 LLM round-trips per turn

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ChatAgent with configuration.

        Args:
            config: Configuration dictionary containing:
                - endpoint: The book-service API endpoint
                - api_key: The book-service x-api-key
                - ai_agent.timeout: /chat request timeout in seconds (default: 300)
                - ai_agent.max_history: Max conversation history entries (default: 50)

            timeout and max_history can be overridden with AI_CHAT_TIMEOUT and
            AI_CHAT_MAX_HISTORY. The chat model/host/key are not read here --
            they are configured on the book-service server.
        """
        ai_config = config.get("ai_agent", {})
        self.book_db_host = config.get("endpoint", "http://localhost:8084")
        self.api_key = config.get("api_key", "")
        self.timeout = int(os.getenv("AI_CHAT_TIMEOUT") or ai_config.get("timeout", self.DEFAULT_TIMEOUT))
        self.max_history = int(os.getenv("AI_CHAT_MAX_HISTORY") or ai_config.get("max_history", self.MAX_HISTORY))

        # Instance variables for conversation state
        self.reply: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Dict[str, Any]] = []

        # Create HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": self.api_key})

    @classmethod
    def from_config_file(cls, config_path: str = "config.json") -> "ChatAgent":
        """
        Create a ChatAgent instance from a configuration file.

        Args:
            config_path: Path to the JSON configuration file

        Returns:
            ChatAgent instance
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, 'r') as f:
            config = json.load(f)

        return cls(config)

    def version(self):
        """
        Display version and configuration information.

        Shows the book-service endpoint, its API version, and the AI tool version.

        Example:
            >>> ai.version()
        """
        q = self.book_db_host + "/configuration"
        try:
            r = self.session.get(q, timeout=10)
            res = r.json()
        except (requests.RequestException, ValueError) as e:
            print(f"Could not reach {q}: {e}")
        else:
            print("*" * self.DIVIDER_WIDTH)
            print("        Book Records and AI Agent Information")
            print("*" * self.DIVIDER_WIDTH)
            print("Endpoint:         {}".format(self.book_db_host))
            print("Endpoint Version: {}".format(res["version"]))
            print("Chat Endpoint:    {}/chat".format(self.book_db_host))
            print("AI   Version:     {}".format(__version__))
            print("*" * self.DIVIDER_WIDTH)

    def _trim_history(self) -> None:
        """
        Trim conversation history to at most max_history entries.

        Cuts only at a user turn, so a tool result is never kept without the
        assistant tool_calls message it answers (the LLM rejects orphans).
        """
        if len(self.conversation_history) <= self.max_history:
            return
        start = len(self.conversation_history) - self.max_history
        while start < len(self.conversation_history) and self.conversation_history[start]["role"] != "user":
            start += 1
        self.conversation_history = self.conversation_history[start:]

    @staticmethod
    def _error_message(response: requests.Response) -> str:
        try:
            return response.json().get("error") or response.text
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

    def _print_trace(self, trace: List[Dict[str, Any]]) -> None:
        """Print each tool call as a one-line summary, then the final reply."""
        for event in trace:
            if event.get("type") == "tool":
                args = ", ".join(f"{k}={v!r}" for k, v in (event.get("toolArgs") or {}).items())
                print(f"  [tool] {event.get('toolName')}({args})")
            elif event.get("type") == "assistant":
                print(event.get("content") or "")

    # Main chat interface methods

    def chat(self, prompt: str) -> None:
        """
        Send a natural language query to the AI assistant.

        The AI can search your book collection, view book details and reading
        history, run semantic searches over notes, and manage tags. Conversation
        history is maintained for follow-up questions.

        Args:
            prompt: Your question or request in natural language.

        Attributes set:
            ai.reply: Contains the full /chat response.

        Example:
            >>> ai.chat("What science fiction books do I have?")
            >>> ai.chat("Which of those are by Isaac Asimov?")
            >>> ai.chat("Add the tag 'classic' to book 456")
            >>> ai.chat("What tags does book 123 have?")
        """
        self._trim_history()
        messages = self.conversation_history + [{"role": "user", "content": prompt}]

        try:
            response = self.session.post(
                f"{self.book_db_host}/chat",
                json={"messages": messages},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            print(f"Chat request failed: {e}")
            return
        if not response.ok:
            print(f"Chat error ({response.status_code}): {self._error_message(response)}")
            return

        # Only commit the new turn once the server has answered, so a failed
        # request can simply be retried
        self.reply = response.json()
        self.conversation_history = self.reply.get("history", messages)
        self._print_trace(self.reply.get("trace", []))

    def clear_history(self) -> None:
        """
        Clear the conversation history and start fresh.

        Use this to reset context when starting a new topic or if the AI
        seems confused by previous conversation.

        Example:
            >>> ai.clear_history()
            Conversation history cleared.
        """
        self.conversation_history = []
        print("Conversation history cleared.")

    def show_history(self) -> None:
        """
        Display the full conversation history as JSON.

        Shows all messages exchanged in the current session, including
        user prompts, AI responses, and tool calls.

        Example:
            >>> ai.show_history()
        """
        print(json.dumps(self.conversation_history, indent=2))

    def show_reply(self) -> None:
        """
        Display the last /chat response in detailed JSON format.

        Useful for debugging or seeing each tool call and its result.

        Example:
            >>> ai.chat("Find books by Tolkien")
            >>> ai.show_reply()  # See detailed response
        """
        if self.reply:
            print(json.dumps(self.reply, indent=2))
        else:
            print("No reply available yet.")


# Historical name, kept so existing scripts and notebooks keep working
OllamaAgent = ChatAgent
