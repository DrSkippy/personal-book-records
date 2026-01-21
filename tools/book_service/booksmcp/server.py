#!/usr/bin/env python3
__version__= "3.0.0"
"""
Books MCP Server - Streamable HTTP Transport

A Model Context Protocol (MCP) server that exposes book and tag search
functionality over HTTP using FastMCP and streamable HTTP transport.

This server provides tools to search the Hendrickson Book Collection:
1. search_books_by_title - Search books by title
2. search_books_by_author - Search books by author
3. search_books_by_isbn - Search books by ISBN-10
4. search_books_by_isbn13 - Search books by ISBN-13
5. search_books_by_publisher - Search books by publisher name
6. search_books_by_category - Search books by category
7. search_books_by_location - Search books by physical location
8. search_books_by_tags - Search books by associated tags
9. search_books_by_read_date - Search books by read date
10. search_tags - Search books by tag labels

All tools return book information including: title, author, tags, book notes, and reading notes.

The server runs on port 3002 and uses streamable HTTP for MCP communication.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import booksdb
sys.path.insert(0, str(Path(__file__).parent.parent))

from booksdb import api_util
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server with streamable HTTP support
port = int(os.getenv("PORT", "3002"))
host = os.getenv("HOST", "0.0.0.0")
mcp = FastMCP(
    "booksmcp-service",
    dependencies=["pymysql", "numpy"],
    host=host,
    port=port
)


# ============================================================================
# Helper Function: Execute Book Search
# ============================================================================

def _execute_book_search(params: dict) -> str:
    """
    Internal helper function to execute book search via booksdb API.

    Queries the Hendrickson Book Collection database and returns formatted results
    including title, author, tags, book notes, and reading notes.

    Args:
        params: Dictionary of search parameters matching booksdb field names

    Returns:
        JSON string with search results including count and book details
    """
    try:
        # Call the books_search_utility from booksdb
        data_rows, header, error_list = api_util.books_search_utility(params)

        if error_list:
            return json.dumps({
                "query": params,
                "error": error_list,
                "results": []
            })

        # Convert results to list of dictionaries
        results = []
        if data_rows:
            for row in data_rows:
                book = {}
                for i, col_name in enumerate(header):
                    if i < len(row):
                        value = row[i]
                        # Convert datetime objects to strings
                        if hasattr(value, 'strftime'):
                            value = value.strftime("%Y-%m-%d")
                        book[col_name] = value
                results.append(book)

        return json.dumps({
            "query": params,
            "count": len(results),
            "results": results
        }, indent=2)

    except Exception as e:
        logger.error(f"Book search error: {e}", exc_info=True)
        return json.dumps({
            "query": params,
            "error": [str(e)],
            "results": []
        })


# ============================================================================
# MCP Tool: Search Books by Title
# ============================================================================

@mcp.tool()
def search_books_by_title(title: str) -> str:
    """
    Search the Hendrickson Book Collection by book title.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the Title field in the books database
    - Case-insensitive search
    - Returns all books where the title contains the search string

    Args:
        title: Book title or partial title to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by title: {title}")
    return _execute_book_search({"Title": title})


# ============================================================================
# MCP Tool: Search Books by Author
# ============================================================================

@mcp.tool()
def search_books_by_author(author: str) -> str:
    """
    Search the Hendrickson Book Collection by author name.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the Author field in the books database
    - Case-insensitive search
    - Returns all books where the author name contains the search string

    Args:
        author: Author name or partial name to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by author: {author}")
    return _execute_book_search({"Author": author})


# ============================================================================
# MCP Tool: Search Books by ISBN
# ============================================================================

@mcp.tool()
def search_books_by_isbn(isbn: str) -> str:
    """
    Search the Hendrickson Book Collection by ISBN-10 number.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs exact or partial matching against the ISBNNumber field
    - ISBN-10 format (10-digit number)
    - Use search_books_by_isbn13 for ISBN-13 searches

    Args:
        isbn: ISBN-10 number (full or partial) to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by ISBN: {isbn}")
    return _execute_book_search({"ISBNNumber": isbn})


# ============================================================================
# MCP Tool: Search Books by ISBN-13
# ============================================================================

@mcp.tool()
def search_books_by_isbn13(isbn13: str) -> str:
    """
    Search the Hendrickson Book Collection by ISBN-13 number.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs exact or partial matching against the ISBNNumber13 field
    - ISBN-13 format (13-digit number)
    - Use search_books_by_isbn for ISBN-10 searches

    Args:
        isbn13: ISBN-13 number (full or partial) to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by ISBN-13: {isbn13}")
    return _execute_book_search({"ISBNNumber13": isbn13})


# ============================================================================
# MCP Tool: Search Books by Publisher
# ============================================================================

@mcp.tool()
def search_books_by_publisher(publisher: str) -> str:
    """
    Search the Hendrickson Book Collection by publisher name.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the PublisherName field
    - Case-insensitive search
    - Returns all books where the publisher name contains the search string

    Args:
        publisher: Publisher name or partial name to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by publisher: {publisher}")
    return _execute_book_search({"PublisherName": publisher})


# ============================================================================
# MCP Tool: Search Books by Category
# ============================================================================

@mcp.tool()
def search_books_by_category(category: str) -> str:
    """
    Search the Hendrickson Book Collection by category.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the Category field
    - Case-insensitive search
    - Categories represent subject classifications or genres

    Args:
        category: Category name or partial name to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by category: {category}")
    return _execute_book_search({"Category": category})


# ============================================================================
# MCP Tool: Search Books by Location
# ============================================================================

@mcp.tool()
def search_books_by_location(location: str) -> str:
    """
    Search the Hendrickson Book Collection by physical location.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the Location field
    - Case-insensitive search
    - Location indicates where the physical book is stored

    Args:
        location: Location name or partial name to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by location: {location}")
    return _execute_book_search({"Location": location})


# ============================================================================
# MCP Tool: Search Books by Tags
# ============================================================================

@mcp.tool()
def search_books_by_tags(tags: str) -> str:
    """
    Search the Hendrickson Book Collection by associated tags.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the Tags field
    - Case-insensitive search
    - Tags are keyword labels assigned to books for classification
    - Multiple tags may be associated with each book

    Args:
        tags: Tag name or partial tag to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by tags: {tags}")
    return _execute_book_search({"Tags": tags})


# ============================================================================
# MCP Tool: Search Books by Read Date
# ============================================================================

@mcp.tool()
def search_books_by_read_date(read_date: str) -> str:
    """
    Search the Hendrickson Book Collection by the date the book was read.

    Returns book information for each book matched, including:
    - Title
    - Author
    - Tags
    - Book notes
    - Read date, the date Scott last read this book

    Technical details:
    - Performs partial string matching against the ReadDate field
    - Date format: YYYY-MM-DD or partial (e.g., "2024" for all books read in 2024)
    - Returns books read on or matching the specified date pattern

    Args:
        read_date: Date or partial date in YYYY-MM-DD format

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by read date: {read_date}")
    return _execute_book_search({"ReadDate": read_date})


# ============================================================================
# Server Information Endpoint
# ============================================================================

@mcp.custom_route("/info", methods=['GET'])
async def server_info(request: Request) -> dict[str, Any]:
    """
    Provide server information.

    Returns:
        Dictionary with server metadata and available tools
    """
    return JSONResponse({
        "name": "Books MCP Server",
        "version": __version__,
        "description": "MCP server for searching the Hendrickson Book Collection",
        "transport": "Streamable HTTP (FastMCP)",
        "tools": [
            {
                "name": "search_books_by_title",
                "description": "Search books by title",
                "parameters": ["title"]
            },
            {
                "name": "search_books_by_author",
                "description": "Search books by author name",
                "parameters": ["author"]
            },
            {
                "name": "search_books_by_isbn",
                "description": "Search books by ISBN-10",
                "parameters": ["isbn"]
            },
            {
                "name": "search_books_by_isbn13",
                "description": "Search books by ISBN-13",
                "parameters": ["isbn13"]
            },
            {
                "name": "search_books_by_publisher",
                "description": "Search books by publisher name",
                "parameters": ["publisher"]
            },
            {
                "name": "search_books_by_category",
                "description": "Search books by category",
                "parameters": ["category"]
            },
            {
                "name": "search_books_by_location",
                "description": "Search books by physical location",
                "parameters": ["location"]
            },
            {
                "name": "search_books_by_tags",
                "description": "Search books by associated tags",
                "parameters": ["tags"]
            },
            {
                "name": "search_books_by_read_date",
                "description": "Search books by read date",
                "parameters": ["read_date"]
            }
        ],
        "examples": {
            "book_by_title": {"tool": "search_books_by_title", "arguments": {"title": "lewis"}},
            "book_by_author": {"tool": "search_books_by_author", "arguments": {"author": "tolkien"}},
            "book_by_isbn": {"tool": "search_books_by_isbn", "arguments": {"isbn": "0123456789"}},
            "book_by_tags": {"tool": "search_books_by_tags", "arguments": {"tags": "science"}},
            "book_by_category": {"tool": "search_books_by_category", "arguments": {"category": "fiction"}}
        }
    })


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Start the MCP server with streamable HTTP transport."""

    logger.info("=" * 70)
    logger.info(f"Starting Books MCP Server (FastMCP) [Version: {__version__}]")
    logger.info("=" * 70)
    logger.info(f"Server: http://{host}:{port}")
    logger.info(f"Transport: Streamable HTTP")
    logger.info("")
    logger.info("Endpoints:")
    logger.info(f"  GET  http://{host}:{port}/health - Health check")
    logger.info(f"  GET  http://{host}:{port}/info   - Server information")
    logger.info(f"  *    http://{host}:{port}/mcp    - MCP protocol endpoint")
    logger.info("")
    logger.info("Tools:")
    logger.info("  search_books_by_title     - Search books by title")
    logger.info("  search_books_by_author    - Search books by author")
    logger.info("  search_books_by_isbn      - Search books by ISBN-10")
    logger.info("  search_books_by_isbn13    - Search books by ISBN-13")
    logger.info("  search_books_by_publisher - Search books by publisher")
    logger.info("  search_books_by_category  - Search books by category")
    logger.info("  search_books_by_location  - Search books by location")
    logger.info("  search_books_by_tags      - Search books by tags")
    logger.info("  search_books_by_read_date - Search books by read date")
    logger.info("=" * 70)

    # Run with streamable HTTP transport
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
