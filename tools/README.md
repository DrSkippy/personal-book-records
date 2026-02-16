# Book Database Tools

A comprehensive suite of tools for managing and querying a personal book collection database. This project provides three complementary interfaces to interact with a MySQL book collection database: a command-line REPL tool, a REST API service, and an MCP (Model Context Protocol) server for AI integration.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Tool 1: BookDBTool (Command-Line REPL)](#tool-1-bookdbtool-command-line-repl)
- [Tool 2: REST API Service](#tool-2-rest-api-service)
- [Tool 3: MCP API Service](#tool-3-mcp-api-service)
- [Configuration](#configuration)
- [Database Schema](#database-schema)
- [Build and Test Infrastructure](#build-and-test-infrastructure)
- [Docker Configuration](#docker-configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Development Workflows](#development-workflows)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

## Quick Start

### Prerequisites

- **Python 3.11+** (required)
- **Poetry** (for dependency management)
- **Docker** (for containerized deployment)
- **MySQL 8.0+** (database server)

### Configuration Setup

1. Create the configuration file:

```bash
cp book_service/config/configuration_example.json book_service/config/configuration.json
```

2. Edit `book_service/config/configuration.json` with your database credentials:

```json
{
  "username": "db_user",
  "password": "db_password",
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

### Quick Start Commands

```bash
# Install dependencies
make install-deps

# Run REST API locally (without Docker)
make run-local-book-service

# Run MCP server locally
make run-local-mcp-service

# Run bookdbtool REPL
poetry run python bin/books.py

# Build and test everything
make build-all
make run-test-all
make test
```

---

## Architecture Overview

### The Three Tools

This project provides three complementary tools for interacting with the book database:

```
┌─────────────────────────────────────────────────────┐
│           MySQL Books Database                      │
│  (books, books_read, tags, estimates)                │
└────────────────┬────────────────────────────────────┘
                 │
          ┌──────┴───────┐
          │  booksdb/    │  ← Shared database
          │  api_util.py │     access layer
          └──────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐  ┌────▼─────┐  ┌──▼────────┐
│bookdb │  │REST API   │  │MCP Server │
│ tool  │  │(Flask)    │  │(FastMCP)  │
│(REPL) │  │Port 8084  │  │Port 3005  │
└───┬───┘  └────┬─────┘  └──┬────────┘
    │           │           │
Terminal    HTTP API    Claude/AI
 Users      Clients     Integration
```

### Shared Infrastructure

All three tools share:
- **Database Layer**: `book_service/booksdb/api_util.py` - Common MySQL query utilities
- **Configuration**: Single `configuration.json` file for all services
- **Database Schema**: MySQL database with books, reading history, and tags

### Directory Structure

```
tools/
├── bin/                          # Executable entry points
│   ├── books.py                  # REPL entry point
│   ├── backup_db.sh              # Database backup script
│   ├── database_cleanup.sh       # Database cleanup
│   └── deploy.sh                 # PHP frontend deployment
├── bookdbtool/                   # Command-line REPL package
│   ├── book_db_tools.py          # BCTool class (main interface)
│   ├── ai_tools.py               # OllamaAgent (AI chat)
│   ├── estimate_tools.py         # ESTTool (reading estimates)
│   ├── isbn_lookup_tools.py      # ISBNLookup (ISBN queries)
│   ├── visualization_tools.py    # Visualization utilities
│   └── manual.py                 # Help/manual text
├── book_service/                 # REST API and MCP services
│   ├── books/                    # REST API (Flask)
│   │   ├── api.py                # Main API (50+ endpoints)
│   │   ├── isbn_com.py           # ISBN.com integration
│   │   ├── Dockerfile            # Docker config
│   │   ├── docker-compose.yml    # Docker Compose
│   │   └── api.ini               # uWSGI config
│   ├── booksdb/                  # Shared database layer
│   │   └── api_util.py           # Database utilities
│   ├── booksmcp/                 # MCP server
│   │   ├── server.py             # FastMCP server
│   │   ├── Dockerfile            # Docker config
│   │   ├── docker-compose.yml    # Docker Compose
│   │   └── requirements.txt      # MCP dependencies
│   ├── config/                   # Configuration
│   │   ├── configuration.json    # Main config (create this)
│   │   └── configuration_example.json  # Template
│   ├── example_json_payloads/    # API test payloads
│   └── test_books/               # Integration tests
├── test/                         # bookdbtool unit tests
├── notebooks/                    # Jupyter notebooks
├── Makefile                      # Build and test automation
├── pyproject.toml                # Poetry dependencies
├── database/                     # Database schema files
│   └── schema.sql               # Database schema
└── README.md                     # This file
```

---

## Tool 1: BookDBTool (Command-Line REPL)

### Overview

BookDBTool is an interactive Python REPL for querying and managing the book collection. It provides a rich command-line interface with multiple specialized classes for different operations.

**Version**: 0.6.0
**Entry Point**: `bin/books.py`
**Location**: `bookdbtool/`

### Features

- **Interactive REPL**: Full Python REPL with pre-loaded objects
- **Book Queries**: Search, filter, and browse book collection
- **AI Integration**: Natural language queries using Ollama LLM
- **Reading Estimates**: Track reading progress and estimate completion dates
- **ISBN Lookup**: Query external ISBN database for book metadata
- **Visualization**: Generate reading statistics charts
- **Pagination**: Automatic pagination for large result sets

### Installation and Setup

```bash
# Install dependencies
poetry install

# Create configuration file
cp book_service/config/configuration_example.json book_service/config/configuration.json
# Edit configuration.json with your database credentials

# Run the REPL
poetry run python bin/books.py
```

### Available Classes

When you launch the REPL, these objects are pre-loaded and ready to use:

#### 1. **bc** - BCTool (Main Database Interface)

The primary interface for querying and updating book records.

**Key Methods:**
- `bc.search(query)` - Search books by various criteria
- `bc.recent(limit)` - Show recently updated books
- `bc.books_read(year)` - List books read in a specific year
- `bc.summary(year)` - Get reading statistics summary
- `bc.add()` - Add new book records interactively
- `bc.version()` - Show API and tool versions

**Example Usage:**
```python
# Search for books by author
bc.search("Author='Tolkien'")

# Get books read in 2024
bc.books_read(2024)

# Show recently updated books
bc.recent(10)

# Get reading summary
bc.summary(2024)

# Add a new book (interactive)
bc.add()
```

#### 2. **ai** - OllamaAgent (AI Chat Interface)

Natural language interface powered by Ollama LLM for intuitive book queries.

**Version**: 0.1.0
**Features**: Tool calling, conversation history, multi-parameter searches

**Key Methods:**
- `ai.chat(message)` - Chat with AI about your book collection
- `ai.clear_history()` - Clear conversation history

**Example Usage:**
```python
# Natural language queries
ai.chat("Find all fiction books I read in 2024")
ai.chat("Show me books by Isaac Asimov")
ai.chat("What science books do I have with 'quantum' in the title?")

# Clear history to start fresh
ai.clear_history()
```

**Supported AI Search Parameters:**
- Author
- Title
- ISBN (ISBN-10 and ISBN-13)
- Tags
- Date ranges
- Publisher
- Location

#### 3. **est** - ESTTool (Reading Estimates)

Track reading progress and estimate completion dates for books in progress.

**Key Methods:**
- `est.estimate_completion(book_id)` - Estimate when you'll finish a book
- `est.add_progress(book_id, page)` - Record current page
- `est.show_progress(book_id)` - Display reading progress chart

#### 4. **isbn** - ISBNLookup (ISBN Database Queries)

Query external ISBN database for book metadata.

**Key Methods:**
- `isbn.lookup(isbn)` - Look up book by ISBN
- `isbn.add_to_collection(isbn)` - Look up and add book to collection

#### 5. **man** - Manual/Help

Display help and command reference.

**Usage:**
```python
man  # Show help text
```

### Testing BookDBTool

```bash
# Run unit tests
make test-bookdbtool

# Run with coverage
make test-bookdbtool-coverage

# Run specific test file
poetry run pytest test/test_book_db_tools.py -v
```

**Test Coverage**: 124+ unit tests covering all modules

See `test/README.md` for detailed test documentation.

---

## Tool 2: REST API Service

### Overview

A comprehensive REST API built with Flask for managing book records, reading history, tags, and generating visualizations.

**Version**: 0.16.2
**Framework**: Flask 3.1.2
**Port**: 8084
**Location**: `book_service/books/`

### Features

- **50+ Endpoints**: Complete CRUD operations for books, reading history, and tags
- **Authentication**: API key-based authentication (`x-api-key` header)
- **Search & Query**: Flexible search with multiple parameters
- **Visualization**: Generate reading progress charts as PNG images
- **ISBN Integration**: Look up and import books via ISBN
- **Image Management**: Upload and manage book cover images
- **Reading Estimates**: Track reading progress and estimate completion

### Authentication

All endpoints (except `/favicon.ico` and `/health`) require authentication via the `x-api-key` header:

```bash
curl -H "x-api-key: your_api_key_here" http://localhost:8084/configuration
```

### Installation and Setup

#### Local Development (without Docker)

```bash
# From tools directory
make run-local-book-service

# Or manually:
cd book_service
export PYTHONPATH=$PWD
export BOOKSDB_CONFIG=./config/configuration.json
poetry run uwsgi --ini books/api.ini
```

The API will be available at `http://localhost:8084`

#### Docker Deployment

```bash
# Build Docker image
make build-book-service

# Run with Docker Compose
cd book_service/books
docker-compose up -d

# Or for testing
make run-test-book-service  # Runs on port 9999
```

### Complete API Endpoint Reference

#### Configuration Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/health` | Health check (returns 'OK', 200) | None (no authentication required) |
| GET | `/configuration` | Get API version and configuration | None |
| GET | `/valid_locations` | List valid book locations | None |

**Example:**
```bash
curl http://localhost:8084/health
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration
```

---

#### Query Endpoints (Books)

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/recent` | Get recently updated books | None |
| GET | `/recent/<limit>` | Get N recent books | `limit`: Number of books (default: 10) |
| GET/POST | `/books_search` | Search books | Query params: Title, Author, IsbnNumber, IsbnNumber13, PublisherName, Location, Recycled, Tags, ReadDate |
| GET | `/complete_record/<book_id>` | Get complete book record | `book_id`: BookId |
| GET | `/complete_record/<book_id>/<adjacent>` | Navigate to next/previous book | `adjacent`: "next" or "prev" |
| GET | `/complete_records_window/<book_id>/<window>` | Get window of records around book | `window`: Number of records (default: 20) |
| POST | `/complete_record_window` | Get complete records for a list of BookIds | Body: `{"book_ids": [1,2,3]}` |

**Search Examples:**
```bash
# Search by author
curl -H "x-api-key: YOUR_KEY" \
  "http://localhost:8084/books_search?Author=Tolkien"

# Get complete book record
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/complete_record/1234

# Navigate to next book
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/complete_record/1234/next
```

---

#### Query Endpoints (Reading History)

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/books_read` | Get all books read | None |
| GET | `/books_read/<target_year>` | Get books read in year | `target_year`: Year (e.g., 2024) |
| GET | `/summary_books_read_by_year` | Get reading summary for all years | None |
| GET | `/summary_books_read_by_year/<target_year>` | Get summary for specific year | `target_year`: Year |
| GET | `/status_read/<book_id>` | Get read status for book | `book_id`: BookId |

**Examples:**
```bash
# Books read in 2024
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/books_read/2024

# Reading summary for all years
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/summary_books_read_by_year
```

---

#### Tag Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/tag_counts` | Get tag usage counts | None |
| GET | `/tag_counts/<tag>` | Get counts for tags starting with prefix | `tag`: Tag prefix |
| GET | `/tags/<book_id>` | Get all tags for a book | `book_id`: BookId |
| GET | `/tags_search/<match_str>` | Search books by tag | `match_str`: Tag to search for |
| GET | `/tag_maintenance` | Normalize tags (lowercase, trim) | None |
| PUT | `/add_tag/<book_id>/<tag>` | Add tag to book | `book_id`, `tag` |
| PUT | `/update_tag_value/<current>/<updated>` | Rename tag | `current`, `updated`: Tag names |

**Examples:**
```bash
# Add tag to book
curl -X PUT -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/add_tag/1234/fiction

# Get all tags for book
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/tags/1234

# Search books by tag
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/tags_search/science

# Rename tag
curl -X PUT -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/update_tag_value/sci-fi/science-fiction
```

---

#### Mutation Endpoints (POST)

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| POST | `/add_books` | Add new book records | Array of book objects |
| POST | `/add_read_dates` | Add read dates for books | Array of read date objects |
| POST | `/books_by_isbn` | Look up and add books by ISBN | `{"isbn_list": ["isbn1", "isbn2"]}` |
| POST | `/update_book_record` | Update any book field(s) | Book object with BookId + fields to update |
| POST | `/update_book_note_status` | Update note/recycled status | `{"BookId": N, "BookNote": "...", "Recycled": 0/1}` |
| POST | `/update_edit_read_note` | Update reading note | `{"BookId": N, "ReadDate": "YYYY-MM-DD", "ReadNote": "..."}` |
| POST | `/add_date_page` | Add daily reading progress | `{"RecordId": N, "RecordDate": "YYYY-MM-DD", "Page": N}` |
| POST | `/add_image` | Add image metadata | `{"BookId": N, "Name": "...", "Url": "...", "ImageType": "cover-face"}` |
| POST | `/upload_image` | Upload image file | Multipart form data with `file` field |
| DELETE | `/delete_book/<book_id>` | Delete a book and all related records (CASCADE) | `book_id`: BookId |

**Add Books Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '[{
    "Title": "The Hobbit",
    "Author": "Tolkien, J.R.R.",
    "CopyrightDate": "1937",
    "IsbnNumber": "0345339681",
    "IsbnNumber13": "9780345339683",
    "PublisherName": "Del Rey",
    "CoverType": "Soft",
    "Pages": 300,
    "Location": "Main Collection",
    "BookNote": "Classic fantasy novel",
    "Recycled": 0
  }]' \
  http://localhost:8084/add_books
```

**Add Read Dates Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '[{
    "BookId": 1234,
    "ReadDate": "2024-01-15",
    "ReadNote": "Great book!"
  }]' \
  http://localhost:8084/add_read_dates
```

**Update Book Record Example:**
```bash
curl -X POST -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_KEY" \
  -d '{
    "BookId": 1234,
    "BookNote": "Updated note",
    "Recycled": 1
  }' \
  http://localhost:8084/update_book_record
```

---

#### Reading Estimate Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/record_set/<book_id>` | Get all reading estimate records | `book_id`: BookId |
| GET | `/date_page_records/<record_id>` | Get daily page records | `record_id`: RecordId |
| PUT | `/add_book_estimate/<book_id>/<last_readable_page>` | Create reading estimate | `book_id`, `last_readable_page` |
| PUT | `/add_book_estimate/<book_id>/<last_readable_page>/<start_date>` | Create estimate with start date | `book_id`, `last_readable_page`, `start_date` |

**Examples:**
```bash
# Create reading estimate
curl -X PUT -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/add_book_estimate/1234/350

# Create estimate with custom start date
curl -X PUT -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/add_book_estimate/1234/350/2024-01-01
```

---

#### Image Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/images/<book_id>` | Get all images for book | `book_id`: BookId |
| POST | `/add_image` | Add image metadata | See mutation endpoints above |
| POST | `/upload_image` | Upload image file | Multipart form data |

**Examples:**
```bash
# Get images for book
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/images/1234

# Upload image
curl -X POST -H "x-api-key: YOUR_KEY" \
  -F "file=@cover.jpg" \
  -F "filename=book_1234_cover.jpg" \
  http://localhost:8084/upload_image
```

---

#### Visualization Endpoints

| Method | Endpoint | Description | Parameters |
|--------|----------|-------------|------------|
| GET | `/image/year_progress_comparison.png` | Reading progress by year chart | None |
| GET | `/image/year_progress_comparison.png/<window>` | Progress chart for N recent years | `window`: Number of years (default: 15) |
| GET | `/image/all_years.png` | All-time reading statistics | None |
| GET | `/image/all_years.png/<year>` | Statistics with specific year highlighted | `year`: Year to highlight |

**Examples:**
```bash
# Download progress comparison chart
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/image/year_progress_comparison.png \
  -o progress.png

# Get all-time statistics
curl -H "x-api-key: YOUR_KEY" \
  http://localhost:8084/image/all_years.png \
  -o stats.png
```

---

### Response Format

All endpoints return JSON responses with this general structure:

```json
{
  "data": [...],           // Result data (array or object)
  "header": [...],         // Column headers (for tabular data)
  "errors": [...],         // Error messages (if any)
  "count": N               // Number of results (for searches)
}
```

### Error Handling

- **401 Unauthorized**: Missing or invalid API key
- **400 Bad Request**: Invalid request payload or parameters
- **500 Internal Server Error**: Database or server error

Errors include descriptive messages in the `error` or `errors` field of the JSON response.

### Testing the REST API

```bash
# Run integration tests (requires Docker)
make test-book-service

# Run local unit tests (no Docker)
make test-local

# Run with coverage
make test-coverage

# Run tests manually
cd book_service
poetry run pytest test_books/test_docker_api.py -v
```

---

## Tool 3: MCP API Service

### Overview

A Model Context Protocol (MCP) server that exposes the book database to AI models like Claude for seamless integration and natural language queries.

**Version**: 3.0.0
**Framework**: FastMCP 0.5.0+
**Port**: 3005
**Location**: `book_service/booksmcp/`

### Features

- **9 MCP Tools**: Search by title, author, ISBN, publisher, location, tags, and read date
- **FastMCP Framework**: Modern, streamable HTTP transport
- **Claude Integration**: Designed for Claude Desktop and other MCP clients
- **Health Checks**: Built-in health monitoring
- **Async Support**: Efficient concurrent request handling

### Quick Start

```bash
# Run locally
make run-local-mcp-service

# Or with Docker
make build-mcp-service
cd book_service/booksmcp
docker-compose up -d
```

The MCP server will be available at `http://localhost:3005`

### MCP Tools Available

The server exposes 9 tools for searching books:

1. `search_books_by_title` - Search by title
2. `search_books_by_author` - Search by author
3. `search_books_by_isbn` - Search by ISBN-10
4. `search_books_by_isbn13` - Search by ISBN-13
5. `search_books_by_publisher` - Search by publisher
6. `search_books_by_location` - Search by physical location
7. `search_books_by_tags` - Search by tags
8. `search_books_by_read_date` - Search by read date
9. `search_tags` - Search for books by tag name

### Endpoints

- `GET/POST /mcp` - Main MCP protocol endpoint
- `GET /health` - Health check (returns `{"status": "healthy"}`)
- `GET /info` - Server metadata and available tools

### Comprehensive Documentation

For complete MCP server documentation including:
- Detailed installation instructions
- Configuration guide
- Full API reference
- Testing procedures
- Troubleshooting
- Architecture details
- Security considerations

**See: `book_service/booksmcp/README.md`** (575 lines of comprehensive documentation)

---

## Configuration

### Configuration File

All tools use a single configuration file: `book_service/config/configuration.json`

**Location**: `tools/book_service/config/configuration.json`
**Template**: `tools/book_service/config/configuration_example.json`

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
  "api_key": "your_40_char_api_key_here"
}
```

### Field Descriptions

| Field | Description | Required |
|-------|-------------|----------|
| `username` | MySQL database username | Yes |
| `password` | MySQL database password | Yes |
| `database` | MySQL database name (should be "book_collection") | Yes |
| `host` | MySQL host (localhost or IP address) | Yes |
| `port` | MySQL port (default: 3306) | Yes |
| `isbn_com.url_isbn` | ISBN lookup API URL template | Optional |
| `isbn_com.key` | ISBNdb.com API key | Optional |
| `endpoint` | REST API endpoint URL | Yes (for bookdbtool) |
| `api_key` | REST API authentication key | Yes (for bookdbtool) |

### Environment Variables

#### For REST API (Book Service)

```bash
export BOOKSDB_CONFIG=/path/to/config/configuration.json  # or BOOKDB_CONFIG
export API_KEY=your_api_key_here
```

#### For MCP Server

```bash
export BOOKDB_CONFIG=/path/to/config/configuration.json
export PORT=3005
export HOST=0.0.0.0
export PYTHONUNBUFFERED=1
```

### Docker Configuration

In Docker containers, the configuration file is typically mounted at:
- Book Service: `/app/config/configuration.json`
- MCP Server: `/app/config/configuration.json`

**Note**: When using Docker with host MySQL, use `host.docker.internal` as the host in your configuration.

---

## Database Schema

### Overview

The book database uses MySQL 8.0+ with the following tables. All tables use the InnoDB engine with utf8mb4 charset.

### Main Tables

#### 1. **books** - Core Book Records

Stores all book metadata and collection information.

**Key Fields:**
- `BookId` (PRIMARY KEY, AUTO_INCREMENT) - Unique book identifier
- `Title` (VARCHAR(200)) - Book title (FULLTEXT indexed)
- `Author` (VARCHAR(200)) - Author name (FULLTEXT indexed)
- `CopyrightDate` (DATETIME) - Copyright/publication date
- `IsbnNumber` (VARCHAR(13)) - ISBN-10 number
- `IsbnNumber13` (VARCHAR(13)) - ISBN-13 number
- `PublisherName` (VARCHAR(50)) - Publisher name
- `CoverType` (VARCHAR(30)) - Hard, Soft, or Digital
- `Pages` (SMALLINT) - Page count
- `BookNote` (MEDIUMTEXT) - Notes and comments
- `Recycled` (TINYINT(1)) - 0=No, 1=Yes (donated/removed)
- `Location` (VARCHAR(50)) - Physical location (indexed)
- `LastUpdate` (TIMESTAMP) - Auto-updated timestamp

**Valid Locations**: Main Collection, DOWNLOAD, Oversized, Pets, Woodwork, Reference, Birding

**Current Record Count**: ~2,900 books

#### 2. **books_read** - Reading History

Tracks when books were read and reading notes.

**Key Fields:**
- `BookId` (INT UNSIGNED) - Foreign key to books
- `ReadDate` (DATE) - Date book was read/started
- `ReadNote` (TEXT) - Reading notes and comments
- `LastUpdate` (TIMESTAMP) - Auto-updated timestamp

**Primary Key**: (BookId, ReadDate) - Allows tracking multiple readings

#### 3. **books_tags** & **tag_labels** - Book Categorization

**books_tags** - Book-to-tag relationships:
- `BookId` (INT) - Book identifier
- `TagId` (INT) - Tag identifier
- `LastUpdate` (TIMESTAMP)

**tag_labels** - Tag definitions:
- `TagId` (PRIMARY KEY, AUTO_INCREMENT)
- `Label` (VARCHAR(50), UNIQUE) - Tag name (lowercase)

Tags provide flexible categorization for books.

#### 4. **complete_date_estimates** - Reading Progress

Tracks reading progress and completion estimates for books in progress.

**Key Fields:**
- `RecordId` (PRIMARY KEY, AUTO_INCREMENT)
- `BookId` (BIGINT UNSIGNED) - Book being read
- `StartDate` (DATETIME) - Reading start date
- `LastReadablePage` (BIGINT) - Total pages in book
- `EstimateDate` (DATETIME) - Estimate calculation date
- `EstimatedFinishDate` (DATETIME) - Predicted completion date

#### 5. **daily_page_records** - Daily Reading Progress

Records daily page counts for reading estimates.

**Key Fields:**
- `RecordId` (BIGINT UNSIGNED) - Links to complete date estimates
- `RecordDate` (DATETIME) - Date of reading
- `Page` (BIGINT) - Page number reached
- `LastUpdate` (TIMESTAMP)

**Primary Key**: (RecordId, RecordDate)

#### 6. **images** - Book Cover Images

Stores book cover images and other book-related images.

**Key Fields:**
- `ImageId` (PRIMARY KEY, AUTO_INCREMENT)
- `BookId` (INT) - Book identifier
- `Name` (VARCHAR(255)) - Image filename
- `Url` (VARCHAR(255)) - Image URL or path
- `ImageType` (VARCHAR(64)) - Image type (default: 'cover-face')

### Schema File

The complete schema is available in `database/schema.sql` and can be used to create the database:

```bash
mysql -u root -p book_collection < database/schema.sql
```

---

## Build and Test Infrastructure

### Makefile Overview

The project uses a comprehensive Makefile with 40+ targets for building, testing, and deploying the services.

**Usage**: Run `make help` or just `make` to see all available targets and common workflows.

### Build Targets

#### Production Image Builds

| Target | Description |
|--------|-------------|
| `make build-all` | Build all Docker images (book service + MCP server + test images) |
| `make build-book-service` | Build book service Docker image (tag: `localhost:5000/book-service:latest` on lambda-dual) |
| `make build-mcp-service` | Build MCP server Docker image (tag: `localhost:5000/booksmcp-service:latest` on lambda-dual) |

**Example:**
```bash
make build-all
# Builds both production images and test images
```

#### Test Image Builds

| Target | Description |
|--------|-------------|
| `make build-test` | Build both test images |
| `make build-test-book-service` | Build book service test image (tag: `book-service-test:latest`) |
| `make build-test-mcp-service` | Build MCP server test image (tag: `bookmcp-service-test:latest`) |

**Note**: Test images use the same Dockerfiles as production but are tagged differently.

---

### Registry Push Targets

Push Docker images to local registry (only on `lambda-dual` hostname).

| Target | Description |
|--------|-------------|
| `make push-all` | Push all images to registry (book service + MCP server) |
| `make push-book-service` | Push book service to `localhost:5000` registry |
| `make push-mcp-service` | Push MCP server to `localhost:5000` registry |

**Hostname Detection**:
- On hostname `lambda-dual`: Images are automatically pushed to `localhost:5000` registry
- On other hosts: You'll see a message to push manually

**Example:**
```bash
make build-all
make push-all  # Pushes to registry if on lambda-dual
```

---

### Local Development Targets

Run services locally without Docker (useful for development and debugging).

| Target | Description | Port |
|--------|-------------|------|
| `make run-local-book-service` | Run book service with poetry and uWSGI | 8084 |
| `make run-local-mcp-service` | Run MCP server with poetry | 3005 |

**Requirements**: Poetry and dependencies must be installed (`make install-deps`)

**Example:**
```bash
# Terminal 1: Run book service
make run-local-book-service

# Terminal 2: Run MCP server
make run-local-mcp-service

# Terminal 3: Test
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration
curl http://localhost:3005/health
```

---

### Test Container Management

Build and run Docker containers specifically for testing (isolated from production).

| Target | Description | Port |
|--------|-------------|------|
| `make run-test-all` | Start both test containers | 9999 (book service), 3005 (MCP) |
| `make run-test-book-service` | Start book service test container | 9999 |
| `make run-test-mcp-service` | Start MCP server test container | 3005 |
| `make stop-test-all` | Stop all test containers | - |
| `make stop-test-book-service` | Stop book service test container | - |
| `make stop-test-mcp-service` | Stop MCP server test container | - |
| `make logs-test-book-service` | View book service test logs (follow mode) | - |
| `make logs-test-mcp-service` | View MCP server test logs (follow mode) | - |

**Example Workflow:**
```bash
# Start test containers
make run-test-all

# Check they're running
docker ps

# View logs in real-time
make logs-test-book-service

# Run tests
make test

# Clean up
make stop-test-all
```

**Note**: Book service test container runs on port **9999** (not 8084) to avoid conflicts with production.

---

### Test Execution Targets

Run test suites against Docker containers or locally.

| Target | Description | What It Tests |
|--------|-------------|---------------|
| `make test` | Run all tests (builds and starts test containers, runs tests, keeps containers running) | REST API + MCP server integration tests |
| `make test-book-service` | Test book service only (builds, runs, tests) | REST API endpoints, also generates curl test commands |
| `make test-mcp-service` | Test MCP server only (builds, runs, tests) | MCP protocol and tools |
| `make test-local` | Run local unit tests (no Docker) | Database utility functions (test_api_util.py) |
| `make test-coverage` | Run tests with coverage report (HTML + terminal) | books, booksmcp, booksdb modules |
| `make test-bookdbtool` | Run bookdbtool unit tests | All bookdbtool modules (124+ tests) |
| `make test-bookdbtool-coverage` | Run bookdbtool tests with coverage | bookdbtool module coverage |

**Examples:**

```bash
# Run all integration tests
make test
# This: builds test images, starts containers, runs tests against localhost:9999 and localhost:3005

# Test only book service
make test-book-service
# Generates curl test commands in ./api_test_commands.sh

# Test bookdbtool
make test-bookdbtool

# Get coverage report
make test-coverage
# Opens htmlcov/index.html in browser
```

**Test Locations**:
- Integration tests: `book_service/test_books/`
- BookDBTool unit tests: `test/`

**Test Coverage**:
- BookDBTool: 124+ unit tests
- REST API: Comprehensive endpoint tests
- MCP Server: Protocol and tool tests

---

### Utility Targets

Maintenance and cleanup tasks.

| Target | Description |
|--------|-------------|
| `make clean` | Remove Python cache files (__pycache__, .pyc, .pyo, .egg-info, .pytest_cache, generated test files) |
| `make clean-images` | Remove all built Docker images (book-service, booksmcp-service, test images) |
| `make stop-all` | Stop and remove all running containers (production + test) |
| `make logs-book-service` | View production book service logs (follow mode) |
| `make logs-mcp-service` | View production MCP server logs (follow mode) |
| `make info` | Display configuration and status (hostname, registry, image tags, running containers) |
| `make install-deps` | Install dependencies with Poetry (runs `poetry install --no-root` in book_service) |
| `make clean-test-records` | Remove test records from the database |

**Examples:**

```bash
# Clean up Python cache
make clean

# Remove all Docker images
make clean-images

# Stop everything
make stop-all

# View production logs
make logs-book-service
make logs-mcp-service

# Check configuration
make info
```

---

### Development Workflow Targets

Shortcuts for common development tasks.

| Target | Description |
|--------|-------------|
| `make install-deps` | Install all dependencies with Poetry |
| `make dev-setup` | Complete development environment setup (install deps + show next steps) |
| `make dev-rebuild` | Clean and rebuild all images (runs `clean` + `build-all`) |
| `make build-prod` | Alias for `build-all` |
| `make deploy-prod` | Build and push to registry, then show deployment instructions |

**Example Development Setup:**

```bash
# Initial setup
make dev-setup

# Make code changes
vim book_service/books/api.py

# Rebuild and test
make dev-rebuild
make run-test-all
make test

# Deploy
make deploy-prod
```

---

### Common Workflows

#### Development & Testing Workflow

```bash
# 1. Start test containers
make run-test-all

# 2. Run tests
make test

# 3. Check logs if needed
make logs-test-book-service
make logs-test-mcp-service

# 4. Clean up
make stop-test-all
```

#### Production Build & Deploy Workflow

```bash
# 1. Build production images
make build-all

# 2. Check configuration
make info

# 3. Push to registry (if on lambda-dual)
make push-all

# 4. Deploy with docker-compose or Dockge
cd book_service/books
docker-compose pull
docker-compose up -d

cd book_service/booksmcp
docker-compose pull
docker-compose up -d
```

#### Quick Test Individual Service

```bash
# Test just book service
make test-book-service

# Test just MCP server
make test-mcp-service
```

#### Complete Rebuild from Scratch

```bash
# Clean everything
make clean
make clean-images
make stop-all

# Rebuild and test
make build-all
make run-test-all
make test
```

---

### Makefile Variables

The Makefile automatically detects your hostname and adjusts behavior:

| Variable | Description | Value on lambda-dual | Value elsewhere |
|----------|-------------|----------------------|-----------------|
| `HOSTNAME` | Detected hostname | lambda-dual | (your hostname) |
| `USE_REGISTRY` | Whether to use registry | true | false |
| `REGISTRY` | Registry URL | localhost:5000 | localhost:5000 |
| `BOOK_SERVICE_TAG` | Book service image tag | localhost:5000/book-service:latest | book-service |
| `MCP_SERVICE_TAG` | MCP service image tag | localhost:5000/booksmcp-service:latest | booksmcp-service |

**Customization**: You can override variables:

```bash
make build-book-service VERSION=1.2.3
make push-book-service REGISTRY=myregistry.com:5000
```

---

## Docker Configuration

### Book Service Dockerfile

**Location**: `book_service/books/Dockerfile`

**Base Image**: `python:3.11-slim`

**Key Components**:
- **Working Directory**: `/app`
- **Package Manager**: Poetry (installed via pipx)
- **System Dependencies**: gcc, g++ (for building Python packages)
- **Python Dependencies**: Installed from `pyproject.toml` (no dev dependencies)
- **Configuration**: `BOOKSDB_CONFIG` environment variable points to `/app/config/configuration.json`
- **Uploads Directory**: `/app/uploads` created for file uploads
- **Port**: 8084 exposed
- **Entrypoint**: `poetry run uwsgi --ini books/api.ini`

**Build Command**:
```bash
docker build -f book_service/books/Dockerfile -t book-service .
```

---

### MCP Server Dockerfile

**Location**: `book_service/booksmcp/Dockerfile`

**Base Image**: `python:3.11-slim`

**Key Components**:
- **Working Directory**: `/app`
- **Package Manager**: pip (no Poetry)
- **System Dependencies**: gcc, g++ (for building Python packages)
- **Python Dependencies**: fastmcp, pymysql from `requirements.txt`
- **Configuration**: `BOOKDB_CONFIG` environment variable
- **Port**: 3005 exposed
- **Health Check**: Probes `/health` endpoint every 30s
- **Entrypoint**: `python -m booksmcp.server`

**Build Command**:
```bash
cd book_service
docker build -f booksmcp/Dockerfile -t booksmcp-service .
```

---

### docker-compose Files

#### Book Service docker-compose.yml

**Location**: `book_service/books/docker-compose.yml`

```yaml
version: '3'
services:
  book-service:
    image: localhost:5000/book-service:latest
    container_name: book-service
    ports:
      - "8084:8084"
    environment:
      - API_KEY=${API_KEY}
    volumes:
      - /var/www/html/resources/books:/app/uploads
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**Key Features**:
- Volume mount for persistent book uploads
- Environment variable for API key
- Host network mapping for accessing host MySQL

**Usage**:
```bash
cd book_service/books
export API_KEY=your_api_key_here
docker-compose up -d
```

#### MCP Server docker-compose.yml

**Location**: `book_service/booksmcp/docker-compose.yml`

```yaml
version: '3'
services:
  booksmcp:
    image: localhost:5000/booksmcp-service:latest
    container_name: booksmcp-service
    ports:
      - "3005:3005"
    environment:
      - PORT=3005
      - HOST=0.0.0.0
      - PYTHONUNBUFFERED=1
      - BOOKDB_CONFIG=/app/config/configuration.json
    networks:
      - books-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    extra_hosts:
      - "host.docker.internal:host-gateway"

networks:
  books-network:
    driver: bridge
```

**Key Features**:
- Custom network for isolation
- Built-in health check
- Environment configuration
- Host network mapping

**Usage**:
```bash
cd book_service/booksmcp
docker-compose up -d
```

---

### Docker Best Practices

#### Building Images

```bash
# Build with cache (fast)
make build-all

# Build without cache (clean build)
docker build --no-cache -f book_service/books/Dockerfile -t book-service .

# Build and push
make build-all
make push-all
```

#### Managing Containers

```bash
# Start containers
cd book_service/books && docker-compose up -d
cd book_service/booksmcp && docker-compose up -d

# Check status
docker ps

# View logs
docker logs -f book-service
docker logs -f booksmcp-service

# Restart containers
docker restart book-service
docker restart booksmcp-service

# Stop containers
docker stop book-service booksmcp-service
```

#### Updating Deployments

```bash
# Method 1: Rebuild and restart
make build-all
make push-all
cd book_service/books && docker-compose pull && docker-compose up -d

# Method 2: Direct restart (if image already updated in registry)
cd book_service/books && docker-compose pull && docker-compose restart
```

---

## Testing

### Test Organization

The project has three test suites:

1. **BookDBTool Unit Tests** (`test/`) - 124+ tests for REPL tool
2. **REST API Integration Tests** (`book_service/test_books/test_docker_api.py`) - Endpoint tests
3. **MCP Server Integration Tests** (`book_service/test_books/test_booksmcp.py`) - Protocol tests

### Running Tests

#### All Tests (Integration)

```bash
make test
# Builds test images, starts containers, runs REST API + MCP tests
```

This will:
1. Build and start test containers (book service on port 9999, MCP on 3005)
2. Wait 5 seconds for services to be ready
3. Run `test_docker_api.py` (REST API tests)
4. Run `test_booksmcp.py` (MCP server tests)
5. Keep containers running for inspection

#### BookDBTool Unit Tests

```bash
# Run all bookdbtool tests
make test-bookdbtool

# Run with coverage
make test-bookdbtool-coverage

# Run specific test file
poetry run pytest test/test_book_db_tools.py -v

# Run specific test class
poetry run pytest test/test_book_db_tools.py::TestBCTool -v

# Run specific test method
poetry run pytest test/test_book_db_tools.py::TestBCTool::test_init -v
```

**Test Files**:
- `test/test_book_db_tools.py` - BCTool class tests
- `test/test_ai_tools.py` - OllamaAgent tests
- `test/test_estimate_tools.py` - ESTTool tests
- `test/test_isbn_lookup_tools.py` - ISBNLookup tests
- `test/test_visualization_tools.py` - Visualization tests

#### REST API Tests

```bash
# Run book service tests only
make test-book-service
# Also generates curl test commands in ./api_test_commands.sh

# Run manually
cd book_service
poetry run pytest test_books/test_docker_api.py -v
```

#### MCP Server Tests

```bash
# Run MCP server tests only
make test-mcp-service

# Run manually
cd book_service
poetry run pytest test_books/test_booksmcp.py -v
```

#### Local Unit Tests (No Docker)

```bash
# Run database utility tests without Docker
make test-local

# Run manually
cd book_service
poetry run pytest test_books/test_api_util.py -v
```

#### Coverage Reports

```bash
# Integration test coverage
make test-coverage
# Generates HTML report in htmlcov/

# BookDBTool coverage
make test-bookdbtool-coverage

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

### Test Workflows

#### Development Testing Workflow

```bash
# 1. Make code changes
vim book_service/books/api.py

# 2. Start test containers
make run-test-all

# 3. Run tests
make test

# 4. If tests fail, check logs
make logs-test-book-service

# 5. Make fixes and re-test (containers still running)
make test

# 6. Clean up
make stop-test-all
```

#### Pre-Deployment Testing

```bash
# 1. Clean slate
make clean
make stop-all

# 2. Build production images
make build-all

# 3. Run comprehensive tests
make run-test-all
make test
make test-coverage

# 4. If all pass, deploy
make push-all
```

#### Test-Driven Development

```bash
# 1. Write test first
vim book_service/test_books/test_docker_api.py

# 2. Run test (should fail)
make test-book-service

# 3. Implement feature
vim book_service/books/api.py

# 4. Run test (should pass)
make test-book-service

# 5. Refactor and re-test
make test
```

---

### Writing New Tests

#### For BookDBTool (Unit Tests)

Create test file in `test/` directory:

```python
# test/test_my_feature.py
import unittest
from unittest.mock import Mock, patch
from bookdbtool.book_db_tools import BCTool

class TestMyFeature(unittest.TestCase):
    def setUp(self):
        self.bc = BCTool("http://test", "test_key")

    @patch('requests.get')
    def test_my_feature(self, mock_get):
        # Mock API response
        mock_get.return_value.json.return_value = {"data": [...]}

        # Test your feature
        result = self.bc.my_method()

        # Assert
        self.assertIsNotNone(result)
```

Run: `poetry run pytest test/test_my_feature.py -v`

#### For REST API (Integration Tests)

Add to `book_service/test_books/test_docker_api.py`:

```python
def test_my_endpoint(api_key):
    """Test my new endpoint"""
    response = requests.get(
        "http://localhost:9999/my_endpoint",
        headers={"x-api-key": api_key}
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
```

Run: `make test-book-service`

#### For MCP Server

Add to `book_service/test_books/test_booksmcp.py`:

```python
def test_my_mcp_tool():
    """Test new MCP tool"""
    response = requests.post(
        "http://localhost:3005/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "my_tool",
                "arguments": {"query": "test"}
            }
        }
    )

    assert response.status_code == 200
    result = response.json()
    assert "result" in result
```

Run: `make test-mcp-service`

---

### Test Fixtures and Mocking

#### Common Test Patterns

**API Key Fixture** (test_docker_api.py):
```python
@pytest.fixture(scope="module")
def api_key():
    """Get API key from configuration"""
    return booksdb.api_util.API_KEY
```

**Mock HTTP Requests** (bookdbtool tests):
```python
from unittest.mock import patch

@patch('requests.get')
def test_search(self, mock_get):
    mock_get.return_value.json.return_value = {
        "data": [[1, "Title", "Author"]],
        "header": ["ID", "Title", "Author"]
    }
    # Test code
```

**Database Mocking**:
Tests use mocking to avoid hitting actual database where possible. Integration tests use real Docker containers with test database.

---

### Continuous Testing

For ongoing development, keep test containers running:

```bash
# Terminal 1: Test containers running
make run-test-all

# Terminal 2: Watch logs
make logs-test-book-service

# Terminal 3: Run tests repeatedly
while true; do
    make test
    sleep 5
done
```

---

## Deployment

### Development Deployment (Local)

Run services locally without Docker for development and debugging.

```bash
# Terminal 1: Book Service
make run-local-book-service
# Running on http://localhost:8084

# Terminal 2: MCP Server
make run-local-mcp-service
# Running on http://localhost:3005

# Terminal 3: Test
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration
curl http://localhost:3005/health
```

**Requirements**:
- Poetry and dependencies installed: `make install-deps`
- MySQL database running and accessible
- Configuration file created and configured

---

### Test Deployment (Docker Containers)

Run test containers for integration testing.

```bash
# Build and start test containers
make run-test-all

# Verify running
docker ps

# Services available at:
# - Book Service: http://localhost:9999
# - MCP Server: http://localhost:3005

# Run tests
make test

# Stop when done
make stop-test-all
```

**Port Mapping**:
- Book Service: Port **9999** (not 8084) to avoid production conflicts
- MCP Server: Port **3005** (same as production)

---

### Production Deployment (Docker Compose)

#### Overview

Production deployment uses Docker Compose with images from a local registry (on `lambda-dual` host) or locally built images.

#### Step 1: Build Production Images

```bash
# Build all images
make build-all

# Check configuration
make info

# Push to registry (if on lambda-dual)
make push-all
```

#### Step 2: Deploy Book Service

```bash
cd book_service/books

# Set environment variables
export API_KEY=your_40_char_api_key_here

# Pull latest image (if using registry)
docker-compose pull

# Start service
docker-compose up -d

# Verify
curl -H "x-api-key: $API_KEY" http://localhost:8084/configuration
docker logs -f book-service
```

#### Step 3: Deploy MCP Server

```bash
cd book_service/booksmcp

# Pull latest image (if using registry)
docker-compose pull

# Start service
docker-compose up -d

# Verify
curl http://localhost:3005/health
docker logs -f booksmcp-service
```

#### Step 4: Verify Deployment

```bash
# Check running containers
docker ps

# Should see:
# - book-service (port 8084)
# - booksmcp-service (port 3005)

# Test endpoints
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/recent
curl http://localhost:3005/info
```

---

### Updating Production Deployment

#### Method 1: Rebuild and Redeploy

```bash
# 1. Build new images
make build-all

# 2. Push to registry (if on lambda-dual)
make push-all

# 3. Pull and restart on production server
cd book_service/books
docker-compose pull
docker-compose up -d

cd book_service/booksmcp
docker-compose pull
docker-compose up -d
```

#### Method 2: Rolling Restart (No Downtime)

```bash
# Pull new image
docker-compose pull

# Restart with no downtime
docker-compose up -d --no-deps --build <service_name>
```

#### Method 3: Complete Restart

```bash
# Stop services
cd book_service/books && docker-compose down
cd book_service/booksmcp && docker-compose down

# Rebuild and start
make build-all
cd book_service/books && docker-compose up -d
cd book_service/booksmcp && docker-compose up -d
```

---

### Registry Management

#### Setting Up Local Registry (Portainer/Dockge)

If deploying on `lambda-dual`, a local Docker registry should be running at `localhost:5000`.

**Docker Compose for Registry**:
```yaml
version: '3.8'
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - ./data/registry:/var/lib/registry
    restart: always
```

**Configure Insecure Registry** (`/etc/docker/daemon.json`):
```json
{
  "insecure-registries": ["localhost:5000"]
}
```

Restart Docker: `sudo systemctl restart docker`

#### Using Registry

```bash
# Push to registry
make push-all

# Check registry contents
curl http://localhost:5000/v2/_catalog

# Pull from registry
docker pull localhost:5000/book-service:latest
docker pull localhost:5000/booksmcp-service:latest
```

---

### Deployment Script (deploy.sh)

**Location**: `bin/deploy.sh`

This script deploys the **PHP frontend** (not the Docker services). It:
- Generates a new API key using OpenSSL
- Updates `library/base.js` with the new key
- Syncs frontend files to remote server via rsync

**Usage**:
```bash
cd bin
./deploy.sh [options]

# With custom settings
./deploy.sh --user myuser --host example.com --path /var/www/html
```

**Post-Deployment**:
After deploying PHP frontend, update the Docker book service with the new API key:

```bash
# Option 1: Update docker-compose.yml
vim book_service/books/docker-compose.yml
# Update API_KEY environment variable

# Option 2: Pass as environment variable
export API_KEY=new_key_here
docker-compose up -d

# Option 3: Update Dockerfile ENV
vim book_service/books/Dockerfile
# Add: ENV API_KEY=new_key
make build-book-service
```

---

### Health Checks and Monitoring

#### Health Check Endpoints

```bash
# Book Service - Configuration endpoint (requires API key)
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration

# MCP Server - Health check (no auth)
curl http://localhost:3005/health
# Returns: {"status": "healthy"}

# MCP Server - Info endpoint
curl http://localhost:3005/info
```

#### Monitoring Containers

```bash
# Check container status
docker ps -a

# View logs
docker logs -f book-service
docker logs -f booksmcp-service

# Check resource usage
docker stats book-service booksmcp-service

# Inspect container
docker inspect book-service
```

#### Automatic Health Checks

The MCP server has built-in Docker health checks:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 10 seconds

Check health:
```bash
docker ps  # Look for "healthy" in STATUS column
docker inspect --format='{{.State.Health.Status}}' booksmcp-service
```

---

### Backup and Restore

#### Database Backup

```bash
# Run backup script
cd bin
./backup_db.sh

# Backups saved to configured location
# Example: /mnt/raid1/shares/backups/booksdb_2025-01-04_1234.sql
```

#### Manual Backup

```bash
mysqldump -u username -p book_collection > backup_$(date +%Y%m%d).sql
```

#### Restore Database

```bash
mysql -u username -p book_collection < backup_20250104.sql
```

---

### Production Checklist

Before deploying to production:

- [ ] Configuration file created and filled out correctly
- [ ] Database accessible from Docker containers (use `host.docker.internal`)
- [ ] API key generated and secure (40 characters recommended)
- [ ] All tests passing (`make test`)
- [ ] Docker images built (`make build-all`)
- [ ] Images pushed to registry (`make push-all` if applicable)
- [ ] Persistent volumes configured (for book uploads)
- [ ] Health checks passing
- [ ] Logs reviewed for errors
- [ ] Backup strategy in place
- [ ] Monitoring set up (optional but recommended)

---

## Development Workflows

### Setting Up Development Environment

#### Initial Setup

```bash
# 1. Clone repository
git clone <repository_url>
cd tools

# 2. Install dependencies
make dev-setup
# This runs: poetry install

# 3. Create configuration
cp book_service/config/configuration_example.json book_service/config/configuration.json
vim book_service/config/configuration.json
# Fill in your database credentials and API key

# 4. Verify database connection
mysql -u your_user -p book_collection -e "SELECT COUNT(*) FROM books;"
```

#### Running Services Locally

```bash
# Terminal 1: Book Service
make run-local-book-service

# Terminal 2: MCP Server
make run-local-mcp-service

# Terminal 3: REPL
poetry run python bin/books.py
```

---

### Making Code Changes

#### Workflow for REST API Changes

```bash
# 1. Make changes
vim book_service/books/api.py

# 2. Run locally to test
make run-local-book-service

# 3. Test manually
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/your_new_endpoint

# 4. Write tests
vim book_service/test_books/test_docker_api.py

# 5. Run full test suite
make test

# 6. Build Docker image
make build-book-service

# 7. Test in Docker
make run-test-book-service
make test-book-service

# 8. Commit
git add book_service/books/api.py book_service/test_books/test_docker_api.py
git commit -m "Add new endpoint for X"
```

#### Workflow for BookDBTool Changes

```bash
# 1. Make changes
vim bookdbtool/book_db_tools.py

# 2. Test in REPL
poetry run python bin/books.py
# Try your new feature interactively

# 3. Write unit tests
vim test/test_book_db_tools.py

# 4. Run tests
make test-bookdbtool

# 5. Commit
git add bookdbtool/book_db_tools.py test/test_book_db_tools.py
git commit -m "Add feature X to BCTool"
```

#### Workflow for MCP Server Changes

```bash
# 1. Make changes
vim book_service/booksmcp/server.py

# 2. Run locally
make run-local-mcp-service

# 3. Test health endpoint
curl http://localhost:3005/health

# 4. Test MCP protocol
curl -X POST http://localhost:3005/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# 5. Write tests
vim book_service/test_books/test_booksmcp.py

# 6. Run full test suite
make test-mcp-service

# 7. Build and test Docker
make build-mcp-service
make run-test-mcp-service
make test-mcp-service

# 8. Commit
git add book_service/booksmcp/server.py book_service/test_books/test_booksmcp.py
git commit -m "Add new MCP tool for X"
```

---

### Running Tests Locally

#### Quick Test Cycle

```bash
# Run specific test
poetry run pytest test/test_book_db_tools.py::TestBCTool::test_search -v

# Run all bookdbtool tests
make test-bookdbtool

# Run with print output (for debugging)
poetry run pytest test/test_book_db_tools.py -v -s
```

#### Integration Testing

```bash
# Start test containers
make run-test-all

# In another terminal, run tests repeatedly
while sleep 2; do
    clear
    make test
done

# Stop containers when done
make stop-test-all
```

---

### Building and Testing Docker Images

#### Development Build Cycle

```bash
# Build images
make build-all

# Quick test
make run-test-all
docker ps  # Verify running

curl -H "x-api-key: YOUR_KEY" http://localhost:9999/configuration
curl http://localhost:3005/health

# Full test suite
make test

# If tests pass, clean up
make stop-test-all
```

#### Rebuild After Changes

```bash
# Clean rebuild
make clean
make dev-rebuild  # Equivalent to: make clean && make build-all

# Test again
make run-test-all
make test
```

---

### Deploying Changes

#### To Test Environment

```bash
# 1. Build and test locally
make build-all
make test

# 2. Deploy to test environment
# (Assuming test environment pulls from same registry)
ssh test-server
cd /path/to/tools
docker-compose pull
docker-compose up -d
```

#### To Production

```bash
# 1. Ensure all tests pass
make test
make test-coverage

# 2. Build production images
make build-all

# 3. Tag with version (optional)
docker tag book-service book-service:v1.2.3
docker tag booksmcp-service booksmcp-service:v1.2.3

# 4. Push to registry
make push-all

# 5. On production server
ssh production-server
cd book_service/books
docker-compose pull
docker-compose up -d

cd book_service/booksmcp
docker-compose pull
docker-compose up -d

# 6. Verify deployment
curl -H "x-api-key: YOUR_KEY" http://localhost:8084/configuration
curl http://localhost:3005/health
docker logs -f book-service
docker logs -f booksmcp-service
```

#### Rollback if Needed

```bash
# On production server
docker-compose down

# Pull previous version
docker pull localhost:5000/book-service:v1.2.2
docker tag localhost:5000/book-service:v1.2.2 localhost:5000/book-service:latest

docker-compose up -d
```

---

### Database Schema Changes

When modifying the database schema:

```bash
# 1. Update database/schema.sql
vim database/schema.sql

# 2. Test on development database
mysql -u user -p book_collection < database/schema.sql

# 3. Update API code if needed
vim book_service/books/api.py
vim book_service/booksdb/api_util.py

# 4. Update tests
vim book_service/test_books/test_api_util.py

# 5. Run full test suite
make test-local
make test

# 6. Document migration in comments
# Add migration notes to schema file

# 7. Deploy (coordinate with database admin)
```

---

### Adding New Dependencies

#### Python Dependencies (Poetry)

```bash
# Add to main dependencies
poetry add package_name

# Add to dev dependencies
poetry add --group dev package_name

# Update lock file
poetry lock

# Install updated dependencies
poetry install

# Update pyproject.toml in git
git add pyproject.toml poetry.lock
git commit -m "Add package_name dependency"

# Rebuild Docker images
make build-all
```

#### MCP Server Dependencies

```bash
# Update requirements.txt
vim book_service/booksmcp/requirements.txt

# Add new dependency
echo "new-package>=1.0.0" >> book_service/booksmcp/requirements.txt

# Test locally
cd book_service
pip install -r booksmcp/requirements.txt

# Rebuild Docker image
make build-mcp-service

# Test
make run-test-mcp-service
make test-mcp-service
```

---

### Code Quality and Linting

```bash
# Format code (if using black)
poetry run black bookdbtool/ book_service/

# Lint (if using flake8)
poetry run flake8 bookdbtool/ book_service/

# Type checking (if using mypy)
poetry run mypy bookdbtool/
```

---

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-search-endpoint

# Make changes and commit regularly
git add book_service/books/api.py
git commit -m "WIP: Adding new search endpoint"

# Run tests before pushing
make test

# Push to remote
git push origin feature/new-search-endpoint

# Create pull request on GitHub/GitLab
# After review and approval, merge to main
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Connection refused" when accessing API

**Symptoms**:
```bash
curl -H "x-api-key: KEY" http://localhost:8084/configuration
# curl: (7) Failed to connect to localhost port 8084: Connection refused
```

**Solutions**:

1. **Check if service is running**:
   ```bash
   docker ps -a
   # Should see book-service or book-service-test running
   ```

2. **Check logs**:
   ```bash
   docker logs book-service
   # or
   make logs-test-book-service
   ```

3. **Verify port mapping**:
   ```bash
   docker ps | grep book-service
   # Should show: 0.0.0.0:8084->8084/tcp (or 9999 for test)
   ```

4. **Check if port is in use**:
   ```bash
   lsof -i :8084
   # or
   netstat -tuln | grep 8084
   ```

5. **Restart service**:
   ```bash
   docker restart book-service
   # or
   make run-test-book-service
   ```

---

#### Issue: "401 Unauthorized" from API

**Symptoms**:
```bash
curl http://localhost:8084/configuration
# Returns: 401 error
```

**Solutions**:

1. **Add API key header**:
   ```bash
   curl -H "x-api-key: your_key_here" http://localhost:8084/configuration
   ```

2. **Check API key in configuration**:
   ```bash
   cat book_service/config/configuration.json | grep api_key
   ```

3. **Verify API key matches**:
   ```python
   # In Python
   import json
   with open('book_service/config/configuration.json') as f:
       config = json.load(f)
       print(config['api_key'])
   ```

4. **Check logs for API key errors**:
   ```bash
   docker logs book-service 2>&1 | grep "x-api-key"
   ```

---

#### Issue: Database connection errors

**Symptoms**:
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server...")
```

**Solutions**:

1. **Check MySQL is running**:
   ```bash
   sudo systemctl status mysql
   # or
   docker ps | grep mysql
   ```

2. **Verify database credentials**:
   ```bash
   mysql -u username -p -h host -P 3306 book_collection
   # Should connect successfully
   ```

3. **Check configuration file**:
   ```bash
   cat book_service/config/configuration.json
   # Verify username, password, host, port, database
   ```

4. **For Docker: Use host.docker.internal**:
   ```json
   {
     "host": "host.docker.internal",
     "port": 3306
   }
   ```

5. **Check Docker network**:
   ```bash
   docker exec -it book-service ping host.docker.internal
   ```

6. **Verify MySQL allows remote connections**:
   ```sql
   -- In MySQL
   SELECT user, host FROM mysql.user WHERE user='your_user';
   -- Host should be '%' or your Docker network
   ```

---

#### Issue: Tests failing

**Symptoms**:
```
FAILED test/test_book_db_tools.py::TestBCTool::test_search
```

**Solutions**:

1. **Run single test for details**:
   ```bash
   poetry run pytest test/test_book_db_tools.py::TestBCTool::test_search -v -s
   ```

2. **Check test fixtures**:
   - Ensure test data is available
   - Check mock configurations

3. **Verify test containers are running**:
   ```bash
   docker ps | grep test
   ```

4. **Check test container logs**:
   ```bash
   make logs-test-book-service
   ```

5. **Clean and rebuild**:
   ```bash
   make clean
   make stop-test-all
   make build-test
   make run-test-all
   make test
   ```

---

#### Issue: Docker build failures

**Symptoms**:
```
ERROR: failed to solve: process "/bin/sh -c poetry install" did not complete successfully
```

**Solutions**:

1. **Clear Docker cache**:
   ```bash
   docker system prune -a
   make build-all --no-cache
   ```

2. **Check Dockerfile syntax**:
   ```bash
   # Validate Dockerfile
   docker build --check -f book_service/books/Dockerfile .
   ```

3. **Build with verbose output**:
   ```bash
   docker build --progress=plain -f book_service/books/Dockerfile .
   ```

4. **Check available disk space**:
   ```bash
   df -h
   ```

5. **Rebuild dependencies**:
   ```bash
   cd book_service
   poetry lock
   poetry install
   make build-all
   ```

---

#### Issue: Port already in use

**Symptoms**:
```
Error starting userland proxy: listen tcp 0.0.0.0:8084: bind: address already in use
```

**Solutions**:

1. **Find process using port**:
   ```bash
   lsof -i :8084
   # or
   sudo netstat -tulpn | grep 8084
   ```

2. **Stop the process**:
   ```bash
   kill <PID>
   # or
   docker stop $(docker ps -q --filter "publish=8084")
   ```

3. **Use different port**:
   ```bash
   # Edit docker-compose.yml
   ports:
     - "8085:8084"  # Map to different host port
   ```

---

#### Issue: Configuration file not found

**Symptoms**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'book_service/config/configuration.json'
```

**Solutions**:

1. **Create configuration file**:
   ```bash
   cp book_service/config/configuration_example.json book_service/config/configuration.json
   vim book_service/config/configuration.json
   ```

2. **Check environment variable**:
   ```bash
   echo $BOOKSDB_CONFIG
   # Should point to configuration.json
   ```

3. **Verify file exists**:
   ```bash
   ls -la book_service/config/
   ```

4. **Check Docker volume mounts**:
   ```bash
   docker inspect book-service | grep -A 10 Mounts
   ```

---

#### Issue: MCP server not responding

**Symptoms**:
```bash
curl http://localhost:3005/health
# curl: (7) Failed to connect...
```

**Solutions**:

1. **Check if MCP container is running**:
   ```bash
   docker ps | grep booksmcp
   ```

2. **Check MCP logs**:
   ```bash
   docker logs booksmcp-service
   # or
   make logs-mcp-service
   ```

3. **Verify health check**:
   ```bash
   docker inspect booksmcp-service | grep -A 5 Health
   ```

4. **Test from inside container**:
   ```bash
   docker exec -it booksmcp-service curl http://localhost:3005/health
   ```

5. **Restart service**:
   ```bash
   cd book_service/booksmcp
   docker-compose restart
   ```

---

#### Issue: Permission denied errors

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: '/app/uploads/image.jpg'
```

**Solutions**:

1. **Check directory permissions**:
   ```bash
   ls -la /var/www/html/resources/books
   ```

2. **Fix permissions**:
   ```bash
   sudo chown -R $USER:$USER /var/www/html/resources/books
   chmod -R 755 /var/www/html/resources/books
   ```

3. **Check Docker user**:
   ```bash
   docker exec book-service whoami
   # Should match owner of mounted volume
   ```

---

#### Issue: REPL import errors

**Symptoms**:
```
ImportError: No module named 'bookdbtool'
```

**Solutions**:

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Run with poetry**:
   ```bash
   poetry run python bin/books.py
   ```

3. **Check Python path**:
   ```python
   import sys
   print(sys.path)
   ```

---

### Debugging Techniques

#### Enable Debug Logging

**For REST API**:
```python
# In api.py, logging is already set to DEBUG
# Check logs:
docker logs -f book-service
```

**For BookDBTool**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Interactive Debugging

**With pdb**:
```python
# Add to code
import pdb; pdb.set_trace()

# Run and interact
poetry run python bin/books.py
```

**With iPython**:
```bash
poetry add --group dev ipython
poetry run ipython
```

#### Container Debugging

```bash
# Enter running container
docker exec -it book-service bash

# Check processes
ps aux

# Check network
curl http://host.docker.internal:3306

# Check files
ls -la /app/
cat /app/config/configuration.json
```

---

### Log Locations

| Service | Log Command | Location (if mounted) |
|---------|-------------|----------------------|
| Book Service | `docker logs book-service` | N/A (stdout) |
| MCP Server | `docker logs booksmcp-service` | N/A (stdout) |
| Test Book Service | `make logs-test-book-service` | N/A (stdout) |
| Test MCP | `make logs-test-mcp-service` | N/A (stdout) |

**View logs**:
```bash
# Follow logs
docker logs -f book-service

# Last 100 lines
docker logs --tail 100 book-service

# Logs since 10 minutes ago
docker logs --since 10m book-service

# Save logs to file
docker logs book-service > book-service.log 2>&1
```

---

### Getting Help

**Documentation**:
- BookDBTool: `test/README.md`
- MCP Server: `book_service/booksmcp/README.md` (comprehensive)
- Makefile: Run `make help`

**Useful Commands**:
```bash
# Show Makefile help
make help

# Show configuration
make info

# Check Docker status
docker ps -a
docker stats

# Check disk space
df -h
docker system df
```

---

## Additional Resources

### Internal Documentation

- **MCP Server Comprehensive Guide**: `book_service/booksmcp/README.md` - 575 lines of detailed MCP server documentation
- **BookDBTool Tests**: `test/README.md` - Test coverage and running instructions
- **Example Payloads**: `book_service/example_json_payloads/` - Sample JSON for API testing
- **Database Schema**: `database/schema.sql` - Complete MySQL schema

### External Resources

#### Python and Dependencies

- **Python 3.11 Documentation**: https://docs.python.org/3.11/
- **Poetry Documentation**: https://python-poetry.org/docs/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Pandas Documentation**: https://pandas.pydata.org/docs/
- **PyMySQL Documentation**: https://pymysql.readthedocs.io/

#### Docker

- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose Documentation**: https://docs.docker.com/compose/
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/

#### Model Context Protocol (MCP)

- **MCP Specification**: https://modelcontextprotocol.io/
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp
- **Streamable HTTP Transport**: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- **Claude Desktop MCP Setup**: https://docs.anthropic.com/claude/docs/model-context-protocol

#### Testing

- **pytest Documentation**: https://docs.pytest.org/
- **unittest Documentation**: https://docs.python.org/3/library/unittest.html
- **pytest-cov (Coverage)**: https://pytest-cov.readthedocs.io/

#### ISBN Integration

- **ISBNdb API**: https://isbndb.com/apidocs
- **ISBN Wikipedia**: https://en.wikipedia.org/wiki/International_Standard_Book_Number

#### AI Integration

- **Ollama Documentation**: https://ollama.ai/
- **LangChain**: https://python.langchain.com/ (if extending AI features)

### Tools and Utilities

- **MySQL Documentation**: https://dev.mysql.com/doc/
- **uWSGI Documentation**: https://uwsgi-docs.readthedocs.io/
- **Makefile Tutorial**: https://makefiletutorial.com/

### Related Projects

- **Claude Code**: https://claude.com/claude-code (for CLI integration)
- **Anthropic API**: https://docs.anthropic.com/ (for Claude API usage)

---

## Quick Reference

### Essential Commands

```bash
# Setup
make dev-setup                    # Install dependencies
make info                         # Show configuration

# Local Development
make run-local-book-service       # Run API locally (port 8084)
make run-local-mcp-service        # Run MCP locally (port 3005)
poetry run python bin/books.py   # Run REPL

# Testing
make test                         # Run all tests
make test-bookdbtool             # Test REPL tool
make test-book-service           # Test REST API
make test-mcp-service            # Test MCP server

# Building
make build-all                    # Build all images
make push-all                     # Push to registry

# Cleanup
make clean                        # Remove cache files
make stop-all                     # Stop all containers
```

### Port Reference

| Service | Development | Test | Production |
|---------|------------|------|------------|
| Book Service | 8084 | 9999 | 8084 |
| MCP Server | 3005 | 3005 | 3005 |

### Configuration Files

| File | Purpose |
|------|---------|
| `book_service/config/configuration.json` | Main config (create from example) |
| `pyproject.toml` | Python dependencies |
| `book_service/booksmcp/requirements.txt` | MCP dependencies |
| `database/schema.sql` | Database schema |

---

## Version Information

- **BookDBTool**: v0.6.0
- **REST API**: v0.16.2
- **MCP Server**: v3.0.0
- **Python**: 3.11+
- **Flask**: 3.1.2
- **FastMCP**: 0.5.0+
- **MySQL**: 8.0+

---

## Project Structure Summary

```
tools/
├── bookdbtool/           # REPL tool (Python package)
├── book_service/         # Services directory
│   ├── books/            # REST API (Flask)
│   ├── booksmcp/         # MCP server (FastMCP)
│   ├── booksdb/          # Shared DB layer
│   └── config/           # Configuration
├── test/                 # BookDBTool unit tests
├── bin/                  # Executable scripts
├── Makefile              # Build automation
├── pyproject.toml        # Dependencies
└── README.md             # This file
```

---

## Contributing

When contributing to this project:

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Write tests**: Add tests for new functionality
3. **Run all tests**: `make test` must pass
4. **Update documentation**: Update relevant README files
5. **Follow code style**: Use existing patterns
6. **Commit messages**: Clear, descriptive commit messages
7. **Pull request**: Create PR with description of changes

---

## License

See main project license.

---

## Support and Issues

For issues or questions:
1. Check this documentation and related READMEs
2. Review logs: `docker logs <service>`
3. Check [Troubleshooting](#troubleshooting) section
4. Review test output: `make test`

---

**Last Updated**: 2026-02-16

This documentation covers all three tools in the Book Database Tools suite. For tool-specific details, see individual README files:
- MCP Server: `book_service/booksmcp/README.md`
- BookDBTool Tests: `test/README.md`
