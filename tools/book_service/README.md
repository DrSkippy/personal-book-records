# Book Service

This directory contains two service implementations for the Book Database: a REST API and an MCP (Model Context Protocol) server.

## Overview

The `book_service` directory provides:

### 1. **REST API** (`books/`)
- Flask-based HTTP API (Port 8084)
- 50+ endpoints for managing books, reading history, and tags
- Authentication via `x-api-key` header
- Visualization and image management
- Version: 0.16.2

### 2. **MCP Server** (`booksmcp/`)
- Model Context Protocol server for AI integration (Port 3005)
- FastMCP framework with 9 search tools
- Designed for Claude Desktop and other MCP clients
- Version: 3.0.0

### 3. **Shared Database Layer** (`booksdb/`)
- Common MySQL query utilities used by all services
- Database abstraction and helper functions

### 4. **Configuration** (`config/`)
- Shared configuration file for all services
- Database credentials and API settings

## Quick Start

### REST API
```bash
# Run locally
cd /var/www/html/personal-book-records/tools
make run-local-book-service

# Or with Docker
make build-book-service
cd book_service/books
docker-compose up -d

# Test
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration
```

### MCP Server
```bash
# Run locally
cd /var/www/html/personal-book-records/tools
make run-local-mcp-service

# Or with Docker
make build-mcp-service
cd book_service/booksmcp
docker-compose up -d

# Test
curl http://localhost:3005/health
```

## Documentation

### Comprehensive Documentation

For complete documentation on all services, see:
- **Main Documentation**: `../README.md` (tools/README.md)
  - Architecture overview
  - Complete API endpoint reference (50+ endpoints)
  - Full Makefile documentation (40+ targets)
  - Testing procedures
  - Deployment workflows
  - Troubleshooting

### Service-Specific Documentation

- **REST API Details**: `books/README.md` - REST API quick reference
- **MCP Server Complete Guide**: `booksmcp/README.md` - Comprehensive MCP documentation (575 lines)

## Directory Structure

```
book_service/
├── books/                    # REST API (Flask)
│   ├── api.py                # Main Flask API (50+ endpoints)
│   ├── isbn_com.py           # ISBN integration
│   ├── Dockerfile            # Docker configuration
│   ├── docker-compose.yml    # Docker Compose
│   ├── api.ini               # uWSGI configuration
│   └── README.md             # REST API quick reference
├── booksdb/                  # Shared database layer
│   ├── __init__.py
│   └── api_util.py           # Database query utilities
├── booksmcp/                 # MCP server
│   ├── server.py             # FastMCP server
│   ├── Dockerfile            # Docker configuration
│   ├── docker-compose.yml    # Docker Compose
│   ├── requirements.txt      # MCP dependencies
│   └── README.md             # Comprehensive MCP guide
├── config/                   # Configuration
│   ├── configuration.json    # Main config (create from example)
│   └── configuration_example.json  # Template
├── example_json_payloads/    # API test examples
│   ├── test_add_books.json
│   ├── test_update_book_note_status.json
│   ├── test_update_read_dates.json
│   └── test_update_edit_read_note.json
└── test_books/               # Integration tests
    ├── test_api_util.py      # Database layer tests
    ├── test_docker_api.py    # REST API tests
    ├── test_booksmcp.py      # MCP server tests
    └── generate_curl_commands.py  # Test script generator
```

## Configuration

All services use a single configuration file: `config/configuration.json`

### Create Configuration

```bash
cp config/configuration_example.json config/configuration.json
vim config/configuration.json
```

### Required Fields

```json
{
  "username": "mysql_user",
  "password": "mysql_password",
  "database": "book_collection",
  "host": "localhost",
  "port": 3306,
  "isbn_com": {
    "url_isbn": "https://api2.isbndb.com/book/{}",
    "key": "your_isbndb_api_key"
  },
  "endpoint": "http://localhost:8084",
  "api_key": "your_api_key_here"
}
```

For detailed configuration documentation, see `../README.md#configuration`

## Testing

```bash
# From tools directory

# Test REST API
make test-book-service

# Test MCP server
make test-mcp-service

# Test both services
make test

# Test database layer (local, no Docker)
make test-local

# Test with coverage
make test-coverage
```

For detailed testing documentation, see `../README.md#testing`

## Deployment

### Production Deployment

```bash
# From tools directory

# Build and push images
make build-all
make push-all

# Deploy REST API
cd book_service/books
export API_KEY=your_key_here
docker-compose up -d

# Deploy MCP server
cd book_service/booksmcp
docker-compose up -d

# Verify
curl -H "x-api-key: $API_KEY" http://localhost:8084/configuration
curl http://localhost:3005/health
```

For detailed deployment documentation, see `../README.md#deployment`

## Shared Database Layer (booksdb)

The `booksdb` module provides common database access functionality used by both services:

### Key Components

- `api_util.py`: Database query utilities
  - `books_search_utility()` - Main search function
  - Database connection management
  - Query formatting and result processing
  - ISBN validation helpers

### Usage

```python
from booksdb import api_util

# Search books
results = api_util.books_search_utility(
    search_type="Author",
    search_str="Tolkien"
)
```

## Architecture

Both services share the same database layer and configuration:

```
┌─────────────────────────┐
│   MySQL Books Database  │
└───────────┬─────────────┘
            │
      ┌─────┴─────┐
      │ booksdb/  │  Shared database layer
      │ api_util  │
      └─────┬─────┘
            │
    ┌───────┴───────┐
    │               │
┌───▼────┐    ┌────▼────┐
│REST API│    │MCP      │
│Flask   │    │Server   │
│:8084   │    │FastMCP  │
│        │    │:3005    │
└────────┘    └─────────┘
```

## Additional Resources

- **Main README**: `../README.md` - Comprehensive documentation for all tools
- **REST API README**: `books/README.md` - REST API quick reference
- **MCP Server README**: `booksmcp/README.md` - Complete MCP guide (575 lines)
- **Test Documentation**: `../test/README.md` - Test suite documentation
- **Database Schema**: `../database/schema.sql` - MySQL database schema

## Version Information

- REST API: v0.16.2
- MCP Server: v3.0.0
- Python: 3.11+
- Flask: 3.1.2
- FastMCP: 0.5.0+

---

For complete documentation, please refer to:
- **Main documentation**: `/var/www/html/personal-book-records/tools/README.md`
- **MCP server complete guide**: `/var/www/html/personal-book-records/tools/book_service/booksmcp/README.md`
