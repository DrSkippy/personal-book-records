# BookDBTool - Command-Line REPL for Book Database

An interactive Python REPL for querying and managing the personal book collection database.

## Overview

- **Version**: 0.6.0
- **Entry Point**: `../bin/books.py`
- **Type**: Interactive Python REPL with pre-loaded objects

## Quick Start

```bash
# From tools directory
poetry run python bin/books.py
```

## Features

- **Interactive REPL**: Full Python environment with pre-loaded database tools
- **Book Queries**: Search, filter, and browse book collection
- **AI Integration**: Natural language queries using Ollama LLM
- **Reading Estimates**: Track reading progress and predict completion dates
- **ISBN Lookup**: Query external ISBN databases
- **Visualization**: Generate reading statistics charts
- **Pagination**: Automatic pagination for large result sets

## Main Classes

When you launch the REPL, these objects are available:

### 1. **bc** - BCTool
Main interface for querying and updating book records.

```python
bc.search("Author='Tolkien'")
bc.books_read(2024)
bc.recent(10)
bc.add()
```

### 2. **ai** - OllamaAgent
Natural language AI interface powered by Ollama LLM.

```python
ai.chat("Find all fiction books I read in 2024")
ai.chat("Show me books by Isaac Asimov")
```

### 3. **est** - ESTTool
Reading progress estimation tool.

```python
est.estimate_completion(book_id)
est.add_progress(book_id, page)
```

### 4. **isbn** - ISBNLookup
ISBN database query tool.

```python
isbn.lookup("9780345339683")
isbn.add_to_collection("9780345339683")
```

### 5. **man** - Manual/Help
Display help and command reference.

```python
man  # Show help text
```

## Module Structure

```
bookdbtool/
├── __init__.py
├── book_db_tools.py          # BCTool class (main interface)
├── ai_tools.py               # OllamaAgent (AI chat)
├── estimate_tools.py         # ESTTool (reading estimates)
├── isbn_lookup_tools.py      # ISBNLookup (ISBN queries)
├── visualization_tools.py    # Visualization utilities
├── manual.py                 # Help/manual text
└── README.md                 # This file
```

## Comprehensive Documentation

For complete documentation including:
- **Detailed usage examples**
- **All available methods and commands**
- **Configuration setup**
- **Testing procedures**
- **Development workflows**

**See**: `../README.md#tool-1-bookdbtool-command-line-repl` - Main documentation

## Testing

This package has comprehensive unit test coverage (124+ tests).

```bash
# From tools directory

# Run all bookdbtool tests
make test-bookdbtool

# Run with coverage
make test-bookdbtool-coverage

# Run specific test file
poetry run pytest test/test_book_db_tools.py -v
```

**Test Documentation**: `../test/README.md` - Unit test details

## Configuration

BookDBTool uses the shared configuration file:
```bash
../book_service/config/configuration.json
```

Create from example:
```bash
cp book_service/config/configuration_example.json book_service/config/configuration.json
vim book_service/config/configuration.json
```

Required fields:
- `endpoint`: REST API URL (http://localhost:8084)
- `api_key`: API authentication key
- Database credentials (username, password, host, port, database)

## Dependencies

- Python 3.11+
- Poetry (for dependency management)
- Requests (for HTTP API calls)
- Pandas, NumPy (for data processing)
- Matplotlib (for visualizations)
- Ollama (for AI integration)

All dependencies managed via `../pyproject.toml`

## Key Features Details

### Book Queries (BCTool)
- Search by author, title, ISBN, category, publisher, location
- Filter by read status, recycled status
- Browse recently updated books
- Get reading statistics and summaries
- Add and update book records interactively

### AI Chat (OllamaAgent)
- Natural language book queries
- Tool calling for advanced searches
- Conversation history
- Multi-parameter searches
- Supports: author, title, ISBN, category, tags, dates

### Reading Estimates (ESTTool)
- Track daily reading progress
- Estimate completion dates
- Calculate reading velocity
- Visualize progress charts

### ISBN Lookup (ISBNLookup)
- Query ISBNdb.com API
- Look up book metadata by ISBN-10 or ISBN-13
- Add books directly to collection from ISBN

## Development

### Project Structure
- **bookdbtool/**: Python package with REPL tool classes
- **bin/books.py**: Entry point script
- **test/**: Unit tests (124+ tests)
- **../book_service/**: Backend API services

### Making Changes

1. Modify code in `bookdbtool/`
2. Test in REPL:
   ```bash
   poetry run python bin/books.py
   ```
3. Write unit tests in `../test/`
4. Run tests:
   ```bash
   make test-bookdbtool
   ```

## Related Documentation

- **Main README**: `../README.md` - Comprehensive documentation for all tools
- **REST API**: `../book_service/books/README.md` - Backend API documentation
- **MCP Server**: `../book_service/booksmcp/README.md` - AI integration server
- **Test Suite**: `../test/README.md` - Unit test documentation

## Version History

- **v0.6.0** (Current): AI integration, reading estimates, enhanced search
- Based on REST API v0.16.2
- Python 3.11+ required

---

For complete usage documentation, examples, and development workflows, see:
**`/var/www/html/personal-book-records/tools/README.md#tool-1-bookdbtool-command-line-repl`**
