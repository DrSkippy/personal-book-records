# Books MCP Server

A Model Context Protocol (MCP) server that provides book and tag search functionality using **FastMCP** and **streamable HTTP transport**.

## Overview

This MCP server exposes a books database through two main tools:
- **search_books** - Search books by title, author, ISBN, tags, and more
- **search_tags** - Search books by tag labels

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

- Python 3.11+
- FastMCP 0.5.0+
- PyMySQL 1.1.0+
- NumPy 1.24.0+

Or use Docker (recommended).

## Installation

### Using Docker (Recommended)

1. **Build the Docker image:**
   ```bash
   cd tools/book_service
   docker build -t booksmcp:latest -f booksmcp/Dockerfile .
   ```

2. **Run with Docker Compose:**
   ```bash
   cd booksmcp
   docker-compose up -d
   ```

3. **Check the logs:**
   ```bash
   docker-compose logs -f booksmcp
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
  "username": "db_user",
  "password": "db_password",
  "database": "book_collection",
  "host": "localhost",
  "port": 3306
}
```

### Docker Compose

The `docker-compose.yml` file includes:
- Port mapping (3005:3005)
- Health checks
- Automatic restart policy
- Network configuration
- Host gateway access for connecting to host MySQL

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
    "version": "2.0.0",
    "description": "MCP server for book and tag search functionality",
    "transport": "Streamable HTTP (FastMCP)",
    "tools": [
      {
        "name": "search_books",
        "description": "Search books by title, author, ISBN, tags, etc.",
        "parameters": ["Title", "Author", "IsbnNumber", "IsbnNumber13", "PublisherName", "Location", "Tags", "ReadDate"]
      },
      {
        "name": "search_tags",
        "description": "Search books by tag labels",
        "parameters": ["query"]
      }
    ]
  }
  ```

## MCP Tools

### 1. search_books

Search books by various criteria.

**Parameters:**
- `Title` (string, optional) - Book title to search for
- `Author` (string, optional) - Author name to search for
- `IsbnNumber` (string, optional) - ISBN-10 number
- `IsbnNumber13` (string, optional) - ISBN-13 number
- `PublisherName` (string, optional) - Publisher name
- `Location` (string, optional) - Book location
- `Tags` (string, optional) - Tags associated with the book
- `ReadDate` (string, optional) - Date when the book was read

**Returns:** JSON string with search results

**Example Response:**
```json
{
  "query": {
    "Author": "tolkien"
  },
  "count": 5,
  "results": [
    {
      "BookId": "123",
      "Title": "The Lord of the Rings",
      "Author": "J.R.R. Tolkien",
      "IsbnNumber": "0618574948",
      "IsbnNumber13": "9780618574940",
      "PublisherName": "Houghton Mifflin",
      "Location": "Shelf A1",
      "ReadDate": "2024-01-15"
    }
  ]
}
```

### 2. search_tags

Search for books by tag labels.

**Parameters:**
- `query` (string, required) - Tag name to search for

**Returns:** JSON string with search results

**Example Response:**
```json
{
  "query": "history",
  "count": 12,
  "results": [
    {
      "BookId": "456",
      "Title": "A Brief History of Time",
      "Tag": "history",
      "TagId": "78"
    }
  ]
}
```

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
- For local MySQL, use `host.docker.internal` as host in Docker

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

### v2.0.0 (Current)
- **Breaking Changes:** Reimplemented using FastMCP
- Streamable HTTP transport (2025-03-26 spec)
- Simplified architecture
- Enhanced logging
- Custom `/info` endpoint
- Removed SSE-specific endpoints (now handled by FastMCP)

### v1.0.0 (Legacy)
- Manual SSE implementation
- Starlette-based routing
- Deprecated HTTP+SSE specification

## Migration from v1.0.0

If upgrading from v1.0.0:

1. **Endpoints changed:**
   - Old: `/sse` (GET) + `/messages/` (POST)
   - New: `/mcp` (GET/POST) - single endpoint

2. **MCP clients need updating:**
   - Update URL to `http://localhost:3005/mcp`
   - Streamable HTTP transport now used

3. **Dependencies changed:**
   - Old: `mcp`, `starlette`, `uvicorn`
   - New: `fastmcp` (includes everything)

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
