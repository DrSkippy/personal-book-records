__version__ = '0.1.0'

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import ollama
import requests


class OllamaAgent:
    """
    An interactive chat agent for querying a book database using Ollama LLM with tool calling.
    """

    DIVIDER_WIDTH = 50

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OllamaAgent with configuration.

        Args:
            config: Configuration dictionary containing:
                - ai_agent.model_name: The Ollama model to use
                - ai_agent.ollama_host: The Ollama server URL
                - endpoint: The book database API endpoint
                - api_key: API key for book database write operations
        """
        self.ollama_host = config.get("ai_agent", {}).get("ollama_host", "http://localhost:11434")
        self.book_db_host = config.get("endpoint", "http://localhost:8084")
        self.model_name = config.get("ai_agent", {}).get("model_name", "gpt-oss")
        self.api_key = config.get("api_key", "")

        # Instance variables for conversation state
        self.reply: Optional[Dict[str, Any]] = None
        self.conversation_history: List[Dict[str, Any]] = []

        # Tool definitions for Ollama
        self.tools = [
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
        """ Retrieve the back end version. """
        q = self.book_db_host + "/configuration"
        try:
            r = requests.get(q, headers={"x-api-key": self.api_key})
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
            response = requests.get(
                f"{self.book_db_host}/books_search",
                params={"Author": author},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def search_books_by_title(self, title: str) -> Dict[str, Any]:
        """Search for books by title."""
        try:
            response = requests.get(
                f"{self.book_db_host}/books_search",
                params={"Title": title},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def search_books_by_tags(self, tags: str) -> Dict[str, Any]:
        """Search for books by tags."""
        try:
            response = requests.get(
                f"{self.book_db_host}/books_search",
                params={"Tags": tags},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def get_book_tags(self, book_id: int) -> Dict[str, Any]:
        """Get tags for a specific book by ID."""
        try:
            response = requests.get(
                f"{self.book_db_host}/tags/{book_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def add_tag_to_book(self, book_id: int, tag: str) -> Dict[str, Any]:
        """Add a tag to a specific book by ID."""
        try:
            response = requests.put(
                f"{self.book_db_host}/add_tag/{book_id}/{tag}",
                headers={"x-api-key": self.api_key},
                timeout=10
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

    # Main chat interface methods

    def chat(self, prompt: str) -> None:
        """
        Interactive chat function that sends a prompt to the Ollama model
        and displays the streaming response.

        Args:
            prompt: The user's message/question
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })

        # Initial call to the model with tools
        client = ollama.Client(host=self.ollama_host)
        response = client.chat(
            model=self.model_name,
            messages=self.conversation_history,
            tools=self.tools,
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
            final_response = client.chat(
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
        """Clear the conversation history."""
        self.conversation_history = []
        print("Conversation history cleared.")

    def show_history(self) -> None:
        """Display the current conversation history."""
        # Convert any Message objects to dicts before serializing
        serializable_history = [self._message_to_dict(msg) for msg in self.conversation_history]
        print(json.dumps(serializable_history, indent=2))

    def show_reply(self) -> None:
        """Display the last reply in formatted JSON."""
        if self.reply:
            # Handle nested Message objects in the reply
            serializable_reply = dict(self.reply)
            if "message" in serializable_reply:
                serializable_reply["message"] = self._message_to_dict(serializable_reply["message"])
            print(json.dumps(serializable_reply, indent=2))
        else:
            print("No reply available yet.")
