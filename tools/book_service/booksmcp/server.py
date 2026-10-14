#!/usr/bin/env python3
__version__= "3.5.0"
"""
Books MCP Server - Streamable HTTP Transport

A Model Context Protocol (MCP) server that exposes book and tag search
functionality over HTTP using FastMCP and streamable HTTP transport.

This server provides tools to search, and add to, the Hendrickson Book Collection:
1. search_books_by_title - Search books by title
2. search_books_by_author - Search books by author
3. search_books_by_isbn - Search books by ISBN-10
4. search_books_by_isbn13 - Search books by ISBN-13
5. search_books_by_publisher - Search books by publisher name
6. search_books_by_location - Search books by physical location
7. search_books_by_tags - Search books by associated tags
8. search_books_by_read_date - Search books by read date
9. semantic_search_notes - Semantic similarity search over book and reading notes (RAG)
10. lookup_book_metadata - isbndb lookup by ISBN or title (writes nothing)
11. check_book - Dry run of add_book: fill fields, validate, check for duplicates
12. add_book - Add one book; refuses books already in the collection
13. check_books - Dry run for a list of up to 25 books
14. add_books - Add up to 25 books, each added or refused on its own
15. update_book - Correct an existing book's record (before/after, dry run)
16. list_locations - Valid locations and the location rules

The search tools return book information including: title, author, tags, book notes, and reading notes.

The server runs on port 3005 and uses streamable HTTP for MCP communication.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import booksdb
sys.path.insert(0, str(Path(__file__).parent.parent))

from booksdb import api_util, book_add
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
port = int(os.getenv("PORT", "3005"))
host = os.getenv("HOST", "0.0.0.0")
mcp = FastMCP(
    "booksmcp-service",
    dependencies=["psycopg2-binary", "numpy"],
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
    - Performs exact or partial matching against the IsbnNumber field
    - ISBN-10 format (10-digit number)
    - Use search_books_by_isbn13 for ISBN-13 searches

    Args:
        isbn: ISBN-10 number (full or partial) to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by ISBN: {isbn}")
    return _execute_book_search({"IsbnNumber": isbn})


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
    - Performs exact or partial matching against the IsbnNumber13 field
    - ISBN-13 format (13-digit number)
    - Use search_books_by_isbn for ISBN-10 searches

    Args:
        isbn13: ISBN-13 number (full or partial) to search for

    Returns:
        JSON string with count and array of matching books with full details
    """
    logger.info(f"Search books by ISBN-13: {isbn13}")
    return _execute_book_search({"IsbnNumber13": isbn13})


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
# RAG / Semantic Search
# ============================================================================

@mcp.tool()
def semantic_search_notes(query: str, limit: int = 5) -> str:
    """
    Search the Hendrickson Book Collection by meaning rather than exact keywords.

    Uses vector embeddings to find books whose notes are semantically similar
    to the query. Useful for finding books related to a theme, topic, or idea
    when you don't know the exact wording used in the notes.

    Returns results ranked by similarity, each including:
    - BookId and title/author
    - Source of the match (book_note or read_note)
    - The matching note content
    - Similarity score (0-1, higher is more similar)

    Args:
        query: Natural language description of what to find
        limit: Maximum number of results to return (default 5)

    Returns:
        JSON string with array of matching notes ranked by similarity
    """
    logger.info(f"Semantic search: {query!r} limit={limit}")
    results = api_util.rag_search(query, limit=limit)
    return json.dumps({"count": len(results), "results": results})


# ============================================================================
# Adding and correcting books (isbndb lookup, duplicate check, insert, update)
# ============================================================================

# MCP argument name -> books column
_ARG_FIELDS = {"title": "Title", "author": "Author", "authors": "Author", "isbn": "IsbnNumber",
               "isbn13": "IsbnNumber13", "publisher": "PublisherName", "pages": "Pages",
               "copyright_date": "CopyrightDate", "cover_type": "CoverType", "location": "Location",
               "book_note": "BookNote"}
_ITEM_FLAGS = ("confirm_second_copy", "accept_as_is")

_FIELD_DOC = """
    Book fields (all optional; give whatever is known -- an ISBN alone, or a title and author):
        title: short or full title ("Title: Subtitle" is stored when isbndb has the subtitle)
        author: one author, or several joined with " and " / ";"
        authors: list of authors, e.g. ["Daron Acemoglu", "Simon Johnson"] (overrides author).
            Stored as "Last, First and First Last" ("Acemoglu, Daron and Simon Johnson").
        isbn / isbn13: ISBN-10 / ISBN-13, hyphens fine; either form in either field
        publisher, pages, copyright_date (YYYY, YYYY-MM or YYYY-MM-DD)
        cover_type: Hard, Soft or Digital -- pass it for a title-only add; Digital books are
            always stored at DOWNLOAD
        location: see list_locations (default "Main Collection")
        book_note: free text, e.g. where the book came from
"""


def _with_field_doc(fn):
    """Fill the shared {FIELDS} block into a tool's docstring (before @mcp.tool reads it)."""
    fn.__doc__ = fn.__doc__.replace("{FIELDS}", _FIELD_DOC.strip("\n"))
    return fn


def _fields(**args) -> dict:
    """MCP arguments -> books columns; "authors" (a list) wins over "author"."""
    fields = {_ARG_FIELDS[k]: v for k, v in args.items() if k in _ARG_FIELDS and k != "authors"}
    if args.get("authors"):
        fields["Author"] = list(args["authors"])
    return fields


def _items_to_fields(items: list[dict]) -> tuple[list[dict], list[str]]:
    """Batch items (MCP argument names, plus per-item flags) -> books-column dicts."""
    unknown = sorted({k for item in items if isinstance(item, dict) for k in item
                      if k not in _ARG_FIELDS and k not in _ITEM_FLAGS})
    out = []
    for item in items:
        fields = _fields(**item)
        fields.update({k: item[k] for k in _ITEM_FLAGS if k in item})
        out.append(fields)
    return out, unknown


def _dump(result: dict) -> str:
    return json.dumps(result, default=str)


@mcp.tool()
def lookup_book_metadata(isbn: str | None = None, title: str | None = None,
                         author: str | None = None, verbose: bool = False) -> str:
    """
    Look up book details on isbndb (the same lookup the UI's ISBN entry uses). Writes nothing.

    With an ISBN (10 or 13, hyphens fine) returns that edition. Without one, searches by
    title (narrowed by author when given) and returns up to 5 editions, best guess first:
    physical, English, complete editions rank above digital, audio, foreign and bundle editions.

    Each candidate is one line: "isbn13 | binding | publisher | year | pages | language |
    author | title". verbose=true returns full records with scores instead.

    Args:
        isbn: ISBN-10 or ISBN-13
        title: Title to search for when there's no ISBN
        author: Author to narrow a title search
        verbose: full candidate records

    Returns:
        JSON string: {"source": "isbn"|"title_search", "candidates": [...], "error"?}
    """
    logger.info(f"lookup_book_metadata isbn={isbn!r} title={title!r} author={author!r}")
    result = book_add.lookup_metadata(isbn=isbn, title=title, author=author)
    if not verbose:
        result["candidates"] = [book_add.candidate_summary(c) for c in result["candidates"]]
    return _dump(result)


@mcp.tool()
@_with_field_doc
def check_book(title: str | None = None, author: str | None = None, authors: list[str] | None = None,
               isbn: str | None = None, isbn13: str | None = None, publisher: str | None = None,
               pages: int | None = None, copyright_date: str | None = None,
               cover_type: str | None = None, location: str | None = None,
               book_note: str | None = None, verbose: bool = False) -> str:
    """
    Dry run of add_book: build the record add_book would store and check it against the
    collection. Writes nothing. For a list of books use check_books instead.

    With an ISBN, that edition fills the blanks. Without one, an isbndb title search fills them
    only when one physical edition clearly matches; otherwise the status is "needs_review" and
    the record holds only your fields, with up to 3 candidate editions to choose from.

    Status:
    - "ready": add_book will add this record
    - "needs_review": see "review" -- edition_choice (pick an isbn13 from candidates, or pass
      cover_type), author_conflict (isbndb has a different author for this title -- check it),
      no_match (isbndb has nothing). Then call again with isbn13, or add_book with
      accept_as_is=true to store only your fields
    - "duplicate": already in the collection (same ISBN, or same title + author in the same
      format); add_book refuses it
    - "confirm_second_copy": same title + author owned in a different format; ask the user
      whether this is really a second acquisition, then add_book with confirm_second_copy=true
    - "invalid": see message
    Warnings include possible duplicates filed under a different author.
{FIELDS}
        verbose: full output (all candidates as records, search details)

    Returns:
        JSON string with status, message, record, sources (field -> caller, isbndb,
        caller+isbndb or default), missing, warnings, review, duplicates, candidates
    """
    fields = _fields(title=title, author=author, authors=authors, isbn=isbn, isbn13=isbn13,
                     publisher=publisher, pages=pages, copyright_date=copyright_date,
                     cover_type=cover_type, location=location, book_note=book_note)
    logger.info(f"check_book {fields}")
    return _dump(book_add.summarize(book_add.resolve_book(fields), verbose))


@mcp.tool()
@_with_field_doc
def add_book(title: str | None = None, author: str | None = None, authors: list[str] | None = None,
             isbn: str | None = None, isbn13: str | None = None, publisher: str | None = None,
             pages: int | None = None, copyright_date: str | None = None,
             cover_type: str | None = None, location: str | None = None,
             book_note: str | None = None, confirm_second_copy: bool = False,
             accept_as_is: bool = False, verbose: bool = False) -> str:
    """
    Add one book to the Hendrickson Book Collection. Refuses books already in the collection.

    Same arguments and record building as check_book; inserts only when the status is "ready".
    Nothing is written for "duplicate", "invalid" or "needs_review". For "confirm_second_copy"
    (same title + author owned in a different format), ask the user whether this is really a
    second acquisition, then call again with confirm_second_copy=true.
{FIELDS}
        confirm_second_copy: true only after the user confirms a different-format second copy
        accept_as_is: skip isbndb and store only the given fields (plus defaults) -- for a
            "needs_review" book you have checked, or one isbndb doesn't have
        verbose: full output

    Returns:
        JSON string: status "added" with BookId and the stored record, or the check_book result
        explaining why nothing was added
    """
    fields = _fields(title=title, author=author, authors=authors, isbn=isbn, isbn13=isbn13,
                     publisher=publisher, pages=pages, copyright_date=copyright_date,
                     cover_type=cover_type, location=location, book_note=book_note)
    logger.info(f"add_book {fields} confirm_second_copy={confirm_second_copy} accept_as_is={accept_as_is}")
    try:
        result = book_add.add_book(fields, confirm_second_copy=confirm_second_copy, accept_as_is=accept_as_is)
        return _dump(book_add.summarize(result, verbose))
    except Exception as e:
        logger.error(f"add_book error: {e}", exc_info=True)
        return _dump({"status": "error", "message": str(e)})


@mcp.tool()
def check_books(items: list[dict]) -> str:
    """
    Dry run for a list of up to 25 books: one compact row per item (status, title, author,
    chosen ISBN-13, cover type, location, and warnings/duplicates/candidates where relevant),
    plus counts by status. Writes nothing. Also flags items that repeat an earlier item.

    Use it first for a list from a photo, a spreadsheet or a web page; show the user the rows,
    resolve the "needs_review" ones (add isbn13 or cover_type), then call add_books.

    Args:
        items: list of objects with check_book's arguments, e.g.
            [{"title": "Power and Progress", "authors": ["Daron Acemoglu", "Simon Johnson"],
              "cover_type": "Hard"}, {"isbn13": "9780385495325"}]

    Returns:
        JSON string: {"count", "by_status", "items": [rows]}
    """
    fields, unknown = _items_to_fields(items or [])
    if unknown:
        return _dump({"error": f"Unknown item keys: {', '.join(unknown)}"})
    logger.info(f"check_books {len(fields)} items")
    return _dump(book_add.check_books(fields))


@mcp.tool()
def add_books(items: list[dict]) -> str:
    """
    Add up to 25 books, each added or refused on its own by the same rules as add_book.
    Run check_books on the same items first and get the user's approval.

    Args:
        items: list of objects with add_book's arguments; each may also carry
            "confirm_second_copy": true or "accept_as_is": true

    Returns:
        JSON string: {"count", "by_status", "items": [rows with BookId for added books]}
    """
    fields, unknown = _items_to_fields(items or [])
    if unknown:
        return _dump({"error": f"Unknown item keys: {', '.join(unknown)}"})
    logger.info(f"add_books {len(fields)} items")
    return _dump(book_add.add_books(fields))


@mcp.tool()
@_with_field_doc
def update_book(book_id: int, title: str | None = None, author: str | None = None,
                authors: list[str] | None = None, isbn: str | None = None, isbn13: str | None = None,
                publisher: str | None = None, pages: int | None = None,
                copyright_date: str | None = None, cover_type: str | None = None,
                location: str | None = None, book_note: str | None = None,
                dry_run: bool = False) -> str:
    """
    Correct an existing book's record, e.g. a missing co-author or the wrong edition's ISBN.

    Only the fields you pass change (omit a field to leave it; pass "" to clear an optional
    one). Changed fields get add_book's normalization and validation; a new ISBN is refused if
    another book has it. Shows before/after for each change. Use dry_run=true to preview and
    confirm with the user before writing. Does not touch read dates or read notes.

    Args:
        book_id: BookId of the book to change
{FIELDS}
        dry_run: show the changes without writing

    Returns:
        JSON string: status "updated", "dry_run", "unchanged" or "invalid", with changes
        {field: {before, after}}
    """
    fields = _fields(title=title, author=author, authors=authors, isbn=isbn, isbn13=isbn13,
                     publisher=publisher, pages=pages, copyright_date=copyright_date,
                     cover_type=cover_type, location=location, book_note=book_note)
    logger.info(f"update_book {book_id} {fields} dry_run={dry_run}")
    try:
        return _dump(book_add.update_book(book_id, fields, dry_run=dry_run))
    except Exception as e:
        logger.error(f"update_book error: {e}", exc_info=True)
        return _dump({"status": "error", "message": str(e)})


@mcp.tool()
def list_locations() -> str:
    """
    List the valid physical locations for books, and the location rules (Digital books are
    always at DOWNLOAD; DOWNLOAD is only for Digital books; default "Main Collection").

    Returns:
        JSON string: {"locations": [...], "rules": "..."}
    """
    return _dump(book_add.list_locations())


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
        "description": "MCP server for searching and adding to the Hendrickson Book Collection",
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
            },
            {
                "name": "semantic_search_notes",
                "description": "Semantic (pgvector) search over book and reading notes",
                "parameters": ["query", "limit"]
            },
            {
                "name": "lookup_book_metadata",
                "description": "isbndb lookup by ISBN, or title search (writes nothing)",
                "parameters": ["isbn", "title", "author", "verbose"]
            },
            {
                "name": "check_book",
                "description": "Dry run of add_book: fill fields from isbndb, validate, check for duplicates",
                "parameters": ["title", "author", "authors", "isbn", "isbn13", "publisher", "pages",
                               "copyright_date", "cover_type", "location", "book_note", "verbose"]
            },
            {
                "name": "add_book",
                "description": "Add one book; refuses books already in the collection",
                "parameters": ["title", "author", "authors", "isbn", "isbn13", "publisher", "pages",
                               "copyright_date", "cover_type", "location", "book_note",
                               "confirm_second_copy", "accept_as_is", "verbose"]
            },
            {
                "name": "check_books",
                "description": "Dry run for a list of up to 25 books, one row each",
                "parameters": ["items"]
            },
            {
                "name": "add_books",
                "description": "Add up to 25 books, each added or refused on its own",
                "parameters": ["items"]
            },
            {
                "name": "update_book",
                "description": "Correct an existing book's record; shows before/after",
                "parameters": ["book_id", "title", "author", "authors", "isbn", "isbn13", "publisher",
                               "pages", "copyright_date", "cover_type", "location", "book_note", "dry_run"]
            },
            {
                "name": "list_locations",
                "description": "Valid locations and the location rules",
                "parameters": []
            }
        ],
        "examples": {
            "book_by_title": {"tool": "search_books_by_title", "arguments": {"title": "lewis"}},
            "book_by_author": {"tool": "search_books_by_author", "arguments": {"author": "tolkien"}},
            "book_by_isbn": {"tool": "search_books_by_isbn", "arguments": {"isbn": "0123456789"}},
            "book_by_tags": {"tool": "search_books_by_tags", "arguments": {"tags": "science"}},
            "check_book": {"tool": "check_book", "arguments": {"title": "The Overstory", "author": "Richard Powers"}}
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

    api_util.check_embedding_index_freshness()

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
    logger.info("  search_books_by_location  - Search books by location")
    logger.info("  search_books_by_tags      - Search books by tags")
    logger.info("  search_books_by_read_date - Search books by read date")
    logger.info("  semantic_search_notes     - Semantic search over notes")
    logger.info("  lookup_book_metadata      - isbndb lookup by ISBN or title")
    logger.info("  check_book                - Dry run of add_book")
    logger.info("  add_book                  - Add one book (refuses duplicates)")
    logger.info("  check_books / add_books   - Dry run / add up to 25 books")
    logger.info("  update_book               - Correct a book's record")
    logger.info("  list_locations            - Valid locations")
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
