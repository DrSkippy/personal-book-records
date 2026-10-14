# Books MCP Server

A Model Context Protocol (MCP) server that provides book and tag search, and book adding, using **FastMCP** and **streamable HTTP transport**.

## Overview

This MCP server exposes a books database through 16 tools:
- **search_books_by_title** - Search by title
- **search_books_by_author** - Search by author
- **search_books_by_isbn** - Search by ISBN-10
- **search_books_by_isbn13** - Search by ISBN-13
- **search_books_by_publisher** - Search by publisher
- **search_books_by_location** - Search by physical location
- **search_books_by_tags** - Search by tags
- **search_books_by_read_date** - Search by read date
- **semantic_search_notes** - pgvector RAG search over book/read notes
- **lookup_book_metadata** - isbndb lookup by ISBN, or title search (writes nothing)
- **check_book** - Dry run of `add_book`: fill fields, validate, check for duplicates
- **add_book** - Add one book; refuses books already in the collection
- **check_books** / **add_books** - Dry run / add up to 25 books at once
- **update_book** - Correct an existing book's record (before/after, dry run)
- **list_locations** - Valid locations and the location rules

The server uses the latest MCP specifications (2025-03-26) with FastMCP and streamable HTTP transport for efficient, scalable communication.

## Features

- ✨ **Streamable HTTP Transport** - Modern, efficient communication protocol
- 🚀 **FastMCP Framework** - Simplified MCP server implementation
- 🔍 **Flexible Search** - Multiple search parameters for finding books
- 🏷️ **Tag Support** - Search books by tags
- 🐳 **Docker Support** - Easy deployment with Docker and Docker Compose
- 🔧 **Health Checks** - Built-in health monitoring
- 📊 **Structured Results** - JSON-formatted search results

## Requirements

- Python 3.12+
- FastMCP 0.5.0+
- psycopg2-binary 2.9+
- NumPy 1.24.0+

Or use Docker (recommended).

## Installation

### Using Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   cd tools/book_service
   docker build -t booksmcp:latest -f booksmcp/Dockerfile .
   ```

2. **Run with Docker Compose (from repo root):**
   ```bash
   docker compose up -d
   ```

3. **Check the logs:**
   ```bash
   docker compose logs -f booksmcp
   ```

### Manual Installation

1. **Install dependencies:**
   ```bash
   cd tools/book_service/booksmcp
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export PORT=3005
   export HOST=0.0.0.0
   export BOOKDB_CONFIG=/path/to/config/configuration.json
   ```

3. **Run the server:**
   ```bash
   cd ..
   python -m booksmcp.server
   ```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3005` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `BOOKDB_CONFIG` | `/app/config/configuration.json` | Database configuration file path |

### Database Configuration

The server requires a configuration file at the path specified by `BOOKDB_CONFIG`:

```json
{
  "username": "pg_user",
  "password": "pg_password",
  "database": "book-collection",
  "host": "localhost",
  "port": 5434
}
```

### Docker Compose

The `docker-compose.yml` file includes:
- Port mapping (3005:3005)
- Health checks
- Automatic restart policy
- Network configuration
- Host gateway access for connecting to host PostgreSQL

## API Endpoints

### MCP Protocol Endpoint
- **URL:** `/mcp`
- **Methods:** GET, POST
- **Description:** Main MCP protocol communication endpoint (streamable HTTP)

### Health Check
- **URL:** `/health`
- **Method:** GET
- **Description:** Returns server health status
- **Response:**
  ```json
  {
    "status": "healthy"
  }
  ```

### Server Information
- **URL:** `/info`
- **Method:** GET
- **Description:** Returns server metadata and available tools
- **Response:**
  ```json
  {
    "name": "Books MCP Server",
    "version": "3.5.0",
    "description": "MCP server for searching the Hendrickson Book Collection",
    "transport": "Streamable HTTP (FastMCP)",
    "tools": [
      {"name": "search_books_by_title",     "parameters": ["title"]},
      {"name": "search_books_by_author",    "parameters": ["author"]},
      {"name": "search_books_by_isbn",      "parameters": ["isbn"]},
      {"name": "search_books_by_isbn13",    "parameters": ["isbn13"]},
      {"name": "search_books_by_publisher", "parameters": ["publisher"]},
      {"name": "search_books_by_location",  "parameters": ["location"]},
      {"name": "search_books_by_tags",      "parameters": ["tags"]},
      {"name": "search_books_by_read_date", "parameters": ["read_date"]},
      {"name": "semantic_search_notes",     "parameters": ["query", "limit"]},
      {"name": "lookup_book_metadata",      "parameters": ["isbn", "title", "author"]},
      {"name": "check_book",                "parameters": ["title", "author", "isbn", "isbn13", "..."]},
      {"name": "add_book",                  "parameters": ["title", "author", "isbn", "isbn13", "...", "confirm_second_copy", "accept_as_is"]},
      {"name": "check_books",               "parameters": ["items"]},
      {"name": "add_books",                 "parameters": ["items"]},
      {"name": "update_book",               "parameters": ["book_id", "title", "...", "dry_run"]},
      {"name": "list_locations",            "parameters": []}
    ]
  }
  ```

## MCP Tools

Each search-by-field tool takes a single string parameter and returns a JSON string of matching
books; `semantic_search_notes` takes a query string plus an optional result limit.

| Tool | Parameters | Searches by |
|------|-----------|-------------|
| `search_books_by_title` | `title` | Book title (partial match) |
| `search_books_by_author` | `author` | Author name (partial match) |
| `search_books_by_isbn` | `isbn` | ISBN-10 |
| `search_books_by_isbn13` | `isbn13` | ISBN-13 |
| `search_books_by_publisher` | `publisher` | Publisher name |
| `search_books_by_location` | `location` | Physical location |
| `search_books_by_tags` | `tags` | Associated tags |
| `search_books_by_read_date` | `read_date` | Date read (YYYY-MM-DD) |
| `semantic_search_notes` | `query`, `limit` (default 5) | pgvector similarity over `BookNote`/`ReadNote` embeddings |

### Adding and correcting books

For an AI client adding a book, or working through a list from a source with incomplete book
information (a photo of a stack, a spreadsheet, a web page). Logic lives in `booksdb/book_add.py`.

| Tool | Parameters | Does |
|------|-----------|------|
| `lookup_book_metadata` | `isbn`, or `title` (+ `author`); `verbose` | isbndb lookup (same as the UI's ISBN entry), or a title search returning up to 5 ranked editions as one-line summaries. Writes nothing |
| `check_book` | `title`, `author` or `authors` (list), `isbn`, `isbn13`, `publisher`, `pages`, `copyright_date`, `cover_type`, `location`, `book_note` (all optional); `verbose` | Dry run: the record `add_book` would store, `status`, where each field came from, `missing`, `warnings`, `review`, `duplicates`, and candidate editions when a choice is needed |
| `add_book` | same as `check_book`, plus `confirm_second_copy`, `accept_as_is` | Inserts the record when `check_book` would say `ready` |
| `check_books` | `items` (up to 25 objects with `check_book`'s arguments) | Batch dry run: one compact row per item, counts by status, and a warning when an item repeats an earlier one |
| `add_books` | `items` (up to 25; each may carry `confirm_second_copy` / `accept_as_is`) | Adds each item or refuses it on its own |
| `update_book` | `book_id` plus any book fields; `dry_run` | Corrects an existing record: only the given fields change (`""` clears an optional one), with the same validation, and before/after values returned |
| `list_locations` | — | Valid locations (the UI's list plus any in use) and the location rules |

**How a record is filled.** Caller values win. With an ISBN, that edition from isbndb fills the
blanks. Without one, a title search runs a fallback chain (isbndb's ranked search with the author,
then the title column, then title + surname as text, then the same with any subtitle removed) and
scores the editions: physical over digital and audio, an exact title, English and 978-0/978-1
ISBNs up; bundles ("package", "box set", "summary of" ...), missing pages or publisher, and future
dates down. It fills from the best edition only when it is clearly the one (see `needs_review`).
Then defaults: `Location` "Main Collection", `Recycled` 0.

**Normalization.** Authors are stored "Last, First and First Last"
("Acemoglu, Daron and Simon Johnson"); co-authors that isbndb lists and the caller didn't are
added. Titles keep a leading article ("The Lost Elements", not "Lost Elements, The") and get the
full "Title: Subtitle" from isbndb. isbndb values are cleaned: life dates and stray punctuation
in names, ", an imprint of ..." in publishers, and page counts under 50 are dropped.

**Digital books** are always stored at `DOWNLOAD`, but a Digital cover type is only taken from the
caller or from the caller's ISBN, never from a title-search guess.

**Statuses**
- `ready` — will be added
- `needs_review` — not added until resolved; `review` says why:
  - `edition_choice`: Hard and Soft editions both exist and no `cover_type` was given; several
    equally likely editions from different publishers; only digital/audio editions; or the best
    edition looks doubtful (e.g. a bundle). Pick an `isbn13` from `candidates`, or pass `cover_type`
  - `author_conflict`: isbndb has a different author for this title (e.g. "John Vernon Moore" vs
    "Moore, Lucy")
  - `no_match`: isbndb has nothing

  Call again with an `isbn13`, or `add_book` with `accept_as_is=true` to store only the given fields.
- `duplicate` — refused: same ISBN (either form) as an existing book, or same title + author in the
  same format (or no format given)
- `confirm_second_copy` — same title + author exists in a different format; ask the user whether it
  is really a second acquisition, then call `add_book` with `confirm_second_copy=true`. A
  `needs_review` problem is reported first, so confirming can't store a doubtful record
- `invalid` — e.g. no title/author, unknown location, `DOWNLOAD` for a non-Digital book
- `added` — inserted; the result has the new `BookId` (the `BookNote` is indexed for RAG search)

A book with the same title under a *different* author is reported as a "possible duplicate"
warning, not refused. An ISBN that came from a title-search guess counts as a title/author match,
not an ISBN match. Responses are compact by default (one-line candidates, empty fields dropped;
about 1 KB); `verbose=true` returns everything. isbndb calls retry on its per-second rate limit.

Where a book came from (a photo, a shop, a gift) goes in `book_note`; there's no separate field.

## Testing

### 1. Basic Health Check

```bash
curl http://localhost:3005/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Server Information

```bash
curl http://localhost:3005/info
```

### 3. MCP Client Configuration

Configure your MCP client (like Claude Desktop) with the server URL:

```json
{
  "mcpServers": {
    "books": {
      "url": "http://localhost:3005/mcp"
    }
  }
}
```

### 4. Test with Python MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_books_search():
    # For HTTP MCP servers, use appropriate HTTP client
    # This is a conceptual example
    server_params = StdioServerParameters(
        command="http",
        args=["http://localhost:3005/mcp"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", tools)

            # Call search_books tool
            result = await session.call_tool("search_books", {
                "Author": "tolkien"
            })
            print("Search results:", result)

asyncio.run(test_books_search())
```

### 5. Manual Tool Testing

Use curl to test the MCP protocol directly:

```bash
# Initialize connection
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'

# List available tools
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list"
  }'

# Call search_books tool
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "search_books",
      "arguments": {
        "Author": "tolkien"
      }
    }
  }'

# Call search_tags tool
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "search_tags",
      "arguments": {
        "query": "fantasy"
      }
    }
  }'
```

### 6. Docker Health Check

```bash
docker-compose ps
```

Should show healthy status:
```
NAME                COMMAND                  SERVICE    STATUS
booksmcp-service    "python -m booksmcp.…"   booksmcp   Up (healthy)
```

### 7. Log Monitoring

Monitor server logs for debugging:
```bash
# Real-time logs
docker-compose logs -f booksmcp

# Last 100 lines
docker-compose logs --tail=100 booksmcp
```

## Usage Examples

### Search by Title
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_books",
    "arguments": {
      "Title": "lord of the rings"
    }
  }
}
```

### Search by Author
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_books",
    "arguments": {
      "Author": "tolkien"
    }
  }
}
```

### Search by Tags
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_tags",
    "arguments": {
      "query": "history"
    }
  }
}
```

## Troubleshooting

### Server won't start
- Check if port 3005 is already in use: `lsof -i :3005`
- Verify environment variables are set correctly
- Check Docker logs: `docker-compose logs booksmcp`

### Database connection errors
- Verify `BOOKDB_CONFIG` points to a valid configuration file
- Check database credentials in the config file
- Ensure database server is accessible from the container
- For local PostgreSQL, use `host.docker.internal` as host in Docker

### MCP client connection issues
- Verify server is running: `curl http://localhost:3005/health`
- Check firewall settings
- Ensure client is using correct URL: `http://localhost:3005/mcp`
- Review server logs for connection errors

### Empty search results
- Verify database contains data
- Check search parameters match database fields
- Review server logs for errors
- Test with different search criteria

### Docker build fails
- Clear Docker cache: `docker system prune -a`
- Rebuild without cache: `docker-compose build --no-cache`
- Check Dockerfile paths are correct

## Development

### Running in Development Mode

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug logging
export PYTHONUNBUFFERED=1
python -m booksmcp.server
```

### Project Structure

```
booksmcp/
├── server.py           # Main server implementation (FastMCP)
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker image configuration
├── docker-compose.yml # Docker Compose configuration
└── README.md          # This file

Parent structure:
tools/book_service/
├── booksdb/           # Database access layer
├── booksmcp/          # This MCP server
└── config/            # Database configuration
```

## Architecture

The server is built using:
- **FastMCP** - Simplified MCP server framework with built-in streamable HTTP support
- **Streamable HTTP Transport** - Modern MCP transport specification (2025-03-26)
- **booksdb** - Database access layer for book and tag queries
- **Uvicorn** - ASGI server (included with FastMCP)

### Key Components

1. **FastMCP Server** - Handles MCP protocol, routing, and tool registration
2. **Tool Decorators** - Simple `@mcp.tool()` decorator for exposing functions
3. **Custom Routes** - Additional HTTP endpoints via `@mcp.custom_route()`
4. **Database Layer** - Reuses existing `booksdb.api_util` module

### Transport Flow

```
Client Request → /mcp endpoint → FastMCP Router → Tool Handler → Database → Response
```

## Performance Considerations

- **Stateless Design** - Each request is independent
- **Async Support** - FastMCP uses async/await for concurrency
- **Direct DB Queries** - No caching (add if needed for production)
- **JSON Serialization** - Results returned as JSON strings

## Security Notes

- No authentication implemented (add reverse proxy with auth for production)
- Database credentials stored in config file (use secrets management in production)
- SQL injection protection via parameterized queries in booksdb module
- No rate limiting (add if exposing publicly)

## Version History

### v3.5.0 (Current)
Changes from the first real use (57 books added from a photo of a to-be-read stack):
- Edition choice: title-search editions are scored (physical over digital/audio, exact title, English and 978-0/978-1 ISBNs, bundle and incomplete-record penalties) instead of taking the earliest published. Unclear picks return the new `needs_review` status (`edition_choice`, `author_conflict`, `no_match`) with up to 3 candidates; `add_book` refuses them until the caller passes an `isbn13` or `accept_as_is=true`
- A Digital cover type guessed by title search no longer moves a book to `DOWNLOAD`
- Title search fallback chain (isbndb `/search/books` with the author, title column, title + surname text, subtitle removed); authors joined with ";" by isbndb are now split, which had hidden books such as *Power and Progress*
- Full "Title: Subtitle" titles, co-authors from isbndb, an `authors` list parameter, leading articles, and cleaned isbndb values (life dates, stray punctuation, publisher imprints, page counts under 50)
- Title-only possible-duplicate warning (same title, different author)
- Compact responses by default (`verbose` for everything); new `check_books`, `add_books`, `update_book` and `list_locations` tools
- Locations: the UI's list plus any already in use (previously only locations some book used)
- `search_books_by_read_date` with a partial date ("2026-10") no longer fails (`ReadDate::text ILIKE`)
- isbndb calls retry on HTTP 429

### v3.4.0
- Added `lookup_book_metadata`, `check_book` and `add_book` (see [Adding books](#adding-books)); `add_book` refuses redundant books and asks for confirmation before adding a different-format second copy
- `isbn_com.py` moved to `booksdb/` so the MCP image can use the isbndb lookup; it gained a title search and maps isbndb's binding to `CoverType`

### v3.3.1
- `books_search_utility`/`tags_search_utility`/`get_tag_counts`: `LIKE` → `ILIKE` (case-insensitive search)
- `update_reading_book_data`: skip `EstimateDate` rewrite when the book already has a completed `ReadDate` after the estimate's `StartDate`, so viewing a finished book's record no longer marks it "recently touched"
- Pinned `fastmcp<4.0.0`; unpinned resolution had drifted to fastmcp 4.0.1 / mcp 2.x, which renamed `mcp.server.fastmcp.FastMCP` and crash-looped the MCP container

### v3.3.0
- Added `semantic_search_notes` tool: pgvector RAG search over book and reading notes

### v3.2.0
- Added `requests` dependency for embedding API calls

### v3.1.0
- Migrated database driver from PyMySQL to psycopg2-binary (PostgreSQL)

### v3.0.0
- 9 individual search tools (one per search axis)
- FastMCP streamable HTTP transport
- `/health` and `/info` endpoints

## Resources

- **MCP Protocol Specification:** https://modelcontextprotocol.io/
- **FastMCP Documentation:** https://github.com/jlowin/fastmcp
- **Streamable HTTP Transport:** https://modelcontextprotocol.io/specification/2025-03-26/basic/transports

## License

See main project license.

## Support

For issues or questions:
1. Check the logs: `docker-compose logs booksmcp`
2. Verify configuration is correct
3. Review this README
4. Test with curl commands
5. Check MCP protocol documentation

## Contributing

When contributing:
1. Follow existing code style
2. Test with Docker Compose
3. Update documentation
4. Add usage examples
5. Test with actual MCP clients
