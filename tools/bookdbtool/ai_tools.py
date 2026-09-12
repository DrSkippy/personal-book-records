__version__ = '0.3.0'

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class OllamaAgent:
    """
    AI Assistant - Natural language interface for querying your book collection.

    Talks to an OpenAI-compatible chat LLM (e.g. LM Studio) via
    /v1/chat/completions with tool calling to search books, view tags, and
    add tags through conversational queries.

    The AI can:
        - Search books by author, title, or tags
        - View tags for specific books
        - Add tags to books (requires confirmation)

    Attributes:
        reply: The last response from the AI model.
        conversation_history: List of all messages in the current conversation.

    Example:
        >>> ai = OllamaAgent(config)
        >>> ai.chat("What books do I have by Tolkien?")
        >>> ai.chat("Add the tag 'fantasy' to book 123")
        >>> ai.clear_history()  # Start fresh conversation
    """

    DIVIDER_WIDTH = 50
    MAX_HISTORY = 50  # Maximum conversation history entries to retain

    # Tool definitions for Ollama (class variable - shared across instances)
    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "search_books_by_author",
                "description": "Search for books by author name. Returns a list of books written by the specified author.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "author": {
                            "type": "string",
                            "description": "The author name to search for (e.g., 'lewis', 'tolkien')"
                        }
                    },
                    "required": ["author"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_books_by_title",
                "description": "Search for books by title. Returns a list of books matching the specified title.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The book title to search for (e.g., 'grief', 'hobbit')"
                        }
                    },
                    "required": ["title"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_books_by_tags",
                "description": "Search for books by tags. Returns a list of books that have the specified tags.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "string",
                            "description": "The tags to search for (e.g., 'lewis', 'fiction')"
                        }
                    },
                    "required": ["tags"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_book_tags",
                "description": "Get all tags associated with a specific book by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "book_id": {
                            "type": "integer",
                            "description": "The unique ID of the book"
                        }
                    },
                    "required": ["book_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "add_tag_to_book",
                "description": "Add a tag to a specific book. Use this when the user asks to add, attach, or assign a tag to a book. If a there is more than one tag to add, this tool must be called for each tag separately.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "book_id": {
                            "type": "integer",
                            "description": "The unique ID of the book to add the tag to"
                        },
                        "tag": {
                            "type": "string",
                            "description": "The tag to add to the book (e.g., 'fiction', 'classic', 'philosophy')"
                        }
                    },
                    "required": ["book_id", "tag"]
                }
            }
        }
    ]

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OllamaAgent with configuration.

        Args:
            config: Configuration dictionary containing:
                - ai_agent.chat_model: The chat model name
                - ai_agent.chat_host: The OpenAI-compatible chat server URL
                - ai_agent.chat_api_key: Bearer token for the chat LLM server
                - ai_agent.timeout: Request timeout in seconds (default: 10)
                - ai_agent.max_history: Max conversation history entries (default: 50)
                - endpoint: The book database API endpoint
                - api_key: API key for book database write operations

            Every ai_agent field above can be overridden with an environment
            variable: AI_CHAT_HOST, AI_CHAT_MODEL, AI_CHAT_API_KEY,
            AI_CHAT_TIMEOUT, AI_CHAT_MAX_HISTORY.

            chat_api_key authenticates to the chat LLM server (ai_agent.chat_host)
            and is independent of ai_agent.embed_api_key, which authenticates to
            the embedding server (ai_agent.embed_host) — the two servers are no
            longer required to be the same host.
        """
        ai_config = config.get("ai_agent", {})
        self.ollama_host = os.getenv("AI_CHAT_HOST") or ai_config.get("chat_host", "http://localhost:11434")
        self.book_db_host = config.get("endpoint", "http://localhost:8084")
        self.model_name = os.getenv("AI_CHAT_MODEL") or ai_config.get("chat_model", "gpt-oss")
        self.api_key = config.get("api_key", "")
        self.chat_api_key = os.getenv("AI_CHAT_API_KEY") or ai_config.get("chat_api_key", "")
        self.timeout = int(os.getenv("AI_CHAT_TIMEOUT") or ai_config.get("timeout", 10))
        self.max_history = int(os.getenv("AI_CHAT_MAX_HISTORY") or ai_config.get("max_history", self.MAX_HISTORY))

        # Instance variables for conversation state
        self.reply: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Dict[str, Any]] = []

        # Create HTTP session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": self.api_key})

        # Tool function mapping
        self.available_functions = {
            "search_books_by_author": self.search_books_by_author,
            "search_books_by_title": self.search_books_by_title,
            "search_books_by_tags": self.search_books_by_tags,
            "get_book_tags": self.get_book_tags,
            "add_tag_to_book": self.add_tag_to_book
        }

    @classmethod
    def from_config_file(cls, config_path: str = "config.json") -> "OllamaAgent":
        """
        Create an OllamaAgent instance from a configuration file.

        Args:
            config_path: Path to the JSON configuration file

        Returns:
            OllamaAgent instance
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

        Shows the book database endpoint, API version, Ollama endpoint,
        model name, and AI tool version.

        Alias: ver() (via ai.ver)

        Example:
            >>> ai.version()
        """
        q = self.book_db_host + "/configuration"
        try:
            r = self.session.get(q, timeout=self.timeout)
            res = r.json()
        except requests.RequestException as e:
            logging.error(e)
        else:
            print("*" * self.DIVIDER_WIDTH)
            print("        Book Records and AI Agent Information")
            print("*" * self.DIVIDER_WIDTH)
            print("Endpoint:         {}".format(self.book_db_host))
            print("Endpoint Version: {}".format(res["version"]))
            print("Chat Endpoint:    {}".format(self.ollama_host))
            print("Model:            {}".format(self.model_name))
            print("AI   Version:     {}".format(__version__))
            print("*" * self.DIVIDER_WIDTH)

    # Book Database Tool Functions
    def search_books_by_author(self, author: str) -> Dict[str, Any]:
        """Search for books by author name."""
        try:
            response = self.session.get(
                f"{self.book_db_host}/books_search",
                params={"Author": author},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def search_books_by_title(self, title: str) -> Dict[str, Any]:
        """Search for books by title."""
        try:
            response = self.session.get(
                f"{self.book_db_host}/books_search",
                params={"Title": title},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def search_books_by_tags(self, tags: str) -> Dict[str, Any]:
        """Search for books by tags."""
        try:
            response = self.session.get(
                f"{self.book_db_host}/books_search",
                params={"Tags": tags},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_book_tags(self, book_id: int) -> Dict[str, Any]:
        """Get tags for a specific book by ID."""
        try:
            response = self.session.get(
                f"{self.book_db_host}/tags/{book_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def add_tag_to_book(self, book_id: int, tag: str) -> Dict[str, Any]:
        """Add a tag to a specific book by ID."""
        try:
            response = self.session.put(
                f"{self.book_db_host}/add_tag/{book_id}/{tag}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return {"success": True, "book_id": book_id, "tag": tag, "message": "Tag added successfully"}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": f"HTTP error: {e.response.status_code}", "message": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _chat_completion(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """POST an OpenAI-compatible /v1/chat/completions request to ai_agent.chat_host."""
        url = f"{self.ollama_host.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.chat_api_key:
            headers["Authorization"] = f"Bearer {self.chat_api_key}"
        payload: Dict[str, Any] = {"model": self.model_name, "messages": messages, "stream": False}
        if tools:
            payload["tools"] = tools
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _trim_history(self) -> None:
        """Trim conversation history to max_history entries."""
        if len(self.conversation_history) > self.max_history:
            # Keep the most recent messages
            self.conversation_history = self.conversation_history[-self.max_history:]

    # Main chat interface methods

    def chat(self, prompt: str) -> None:
        """
        Send a natural language query to the AI assistant.

        The AI can search your book collection, view book details, and manage tags.
        Conversation history is maintained for follow-up questions.

        Args:
            prompt: Your question or request in natural language.

        Attributes set:
            ai.reply: Contains the full response object from the AI.

        Example:
            >>> ai.chat("What science fiction books do I have?")
            >>> ai.chat("Which of those are by Isaac Asimov?")
            >>> ai.chat("Add the tag 'classic' to book 456")
            >>> ai.chat("What tags does book 123 have?")
        """
        # Trim history if needed before adding new message
        self._trim_history()

        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        # Initial call to the model with tools
        response = self._chat_completion(self.conversation_history, tools=self.TOOLS)

        # Store the full response
        self.reply = response
        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls") or []

        if tool_calls:
            # Add the assistant's response with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": tool_calls,
            })

            # Execute each tool call
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                raw_args = tool_call["function"].get("arguments") or "{}"
                function_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args

                # Call the appropriate function
                if function_name in self.available_functions:
                    function_to_call = self.available_functions[function_name]
                    function_response = function_to_call(**function_args)

                    # Add function response to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "content": json.dumps(function_response),
                        "tool_call_id": tool_call.get("id"),
                    })

            # Get final response from model after tool execution
            final_response = self._chat_completion(self.conversation_history)
            self.reply = final_response
            content = final_response["choices"][0]["message"].get("content") or ""
            print(content)

            # Add assistant's final response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })
        else:
            # No tool calls, just display the response
            content = message.get("content") or ""
            print(content)

            # Add assistant's response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })

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
        Display the last AI response in detailed JSON format.

        Useful for debugging or seeing the full response structure
        including any tool calls that were made.

        Example:
            >>> ai.chat("Find books by Tolkien")
            >>> ai.show_reply()  # See detailed response
        """
        if self.reply:
            print(json.dumps(self.reply, indent=2))
        else:
            print("No reply available yet.")
