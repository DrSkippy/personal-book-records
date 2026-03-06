__version__ = '0.2.0'

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import ollama
import requests


class OllamaAgent:
    """
    AI Assistant - Natural language interface for querying your book collection.

    Uses Ollama LLM with tool calling to search books, view tags, and add tags
    through conversational queries.

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
                - ai_agent.model_name: The Ollama model to use
                - ai_agent.ollama_host: The Ollama server URL
                - ai_agent.timeout: Request timeout in seconds (default: 10)
                - ai_agent.max_history: Max conversation history entries (default: 50)
                - endpoint: The book database API endpoint
                - api_key: API key for book database write operations
        """
        ai_config = config.get("ai_agent", {})
        self.ollama_host = ai_config.get("ollama_host", "http://localhost:11434")
        self.book_db_host = config.get("endpoint", "http://localhost:8084")
        self.model_name = ai_config.get("model_name", "gpt-oss")
        self.api_key = config.get("api_key", "")
        self.timeout = ai_config.get("timeout", 10)
        self.max_history = ai_config.get("max_history", self.MAX_HISTORY)

        # Instance variables for conversation state
        self.reply: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Dict[str, Any]] = []

        # Create Ollama client once (reused for all chat calls)
        self.client = ollama.Client(host=self.ollama_host)

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
            print("Ollama Endpoint:  {}".format(self.ollama_host))
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

    # Helper functions for serialization

    @staticmethod
    def _tool_call_to_dict(tool_call: Any) -> Dict[str, Any]:
        """Convert a ToolCall object to a dictionary."""
        if isinstance(tool_call, dict):
            return tool_call

        # Handle ToolCall objects
        result = {}
        if hasattr(tool_call, "function"):
            func = tool_call.function
            if isinstance(func, dict):
                result["function"] = func
            else:
                result["function"] = {
                    "name": getattr(func, "name", ""),
                    "arguments": getattr(func, "arguments", {})
                }

        return result

    @classmethod
    def _message_to_dict(cls, message: Any) -> Dict[str, Any]:
        """Convert an Ollama Message object to a dictionary."""
        if isinstance(message, dict):
            # Even if it's a dict, we need to check if tool_calls need conversion
            result = dict(message)
            if "tool_calls" in result and result["tool_calls"]:
                result["tool_calls"] = [cls._tool_call_to_dict(tc) for tc in result["tool_calls"]]
            return result

        # Handle Ollama Message objects
        result = {
            "role": message.get("role") if isinstance(message, dict) else getattr(message, "role", "assistant"),
            "content": message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
        }

        # Handle tool calls if present
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = [cls._tool_call_to_dict(tc) for tc in message.tool_calls]

        return result

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

        # Initial call to the model with tools (using pre-created client)
        response = self.client.chat(
            model=self.model_name,
            messages=self.conversation_history,
            tools=self.TOOLS,
            stream=False
        )

        # Store the full response
        self.reply = response

        # Process tool calls if present
        if response.get("message", {}).get("tool_calls"):
            # Add the assistant's response with tool calls to history
            self.conversation_history.append(self._message_to_dict(response["message"]))

            # Execute each tool call
            for tool_call in response["message"]["tool_calls"]:
                function_name = tool_call["function"]["name"]
                function_args = tool_call["function"]["arguments"]

                # Call the appropriate function
                if function_name in self.available_functions:
                    function_to_call = self.available_functions[function_name]
                    function_response = function_to_call(**function_args)

                    # Add function response to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "content": json.dumps(function_response)
                    })

            # Get final response from model after tool execution
            final_response = self.client.chat(
                model=self.model_name,
                messages=self.conversation_history,
                stream=True
            )

            # Stream and display the final response
            full_content = ""
            for chunk in final_response:
                if chunk.get("message", {}).get("content"):
                    content = chunk["message"]["content"]
                    print(content, end="", flush=True)
                    full_content += content

            print()  # New line after streaming

            # Update reply with the final response
            self.reply = {
                "message": {
                    "role": "assistant",
                    "content": full_content
                }
            }

            # Add assistant's final response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_content
            })
        else:
            # No tool calls, just display the response
            content = response.get("message", {}).get("content", "")
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
        # Convert any Message objects to dicts before serializing
        serializable_history = [self._message_to_dict(msg) for msg in self.conversation_history]
        print(json.dumps(serializable_history, indent=2))

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
            # Handle nested Message objects in the reply
            serializable_reply = dict(self.reply)
            if "message" in serializable_reply:
                serializable_reply["message"] = self._message_to_dict(serializable_reply["message"])
            print(json.dumps(serializable_reply, indent=2))
        else:
            print("No reply available yet.")
